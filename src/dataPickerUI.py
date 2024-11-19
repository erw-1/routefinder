from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QScrollArea, QComboBox, QTextEdit, QMessageBox,
    QGroupBox, QFrame, QFileDialog, QInputDialog, QStackedWidget, QPlainTextEdit
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QCursor
from PySide6.QtCore import Qt, QPoint

import os
import shutil
import sys
import subprocess
import json

# Importation des fonctions nécessaires
from dataVerification import verify_and_update_json, update_json_file
from uiUtils import (
    disable_scroll_wheel, remove_couple_data, remove_layer_data
)
from genWebmap import generate_web_page  # Importer la fonction Jinja


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RouteFinder Builder")
        self.setGeometry(100, 100, 1150, 600)
        self.setMinimumWidth(800)

        # Supprimer la barre de titre par défaut
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Définir l'icône de l'application
        self.setWindowIcon(QIcon("img/dataPickerLogo.png"))

        # Initialisation des structures de données
        self.couples = {}
        self.next_couple_id = 1  # Compteur séquentiel d'ID

        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(2, 2, 2, 2)  # Add margins for the custom border

        # Initialiser les variables pour le redimensionnement
        self.resizing = False
        self.resize_direction = None
        self.old_resize_pos = None

        # Définir une marge pour détecter les zones de redimensionnement
        self.resize_margin = 10

        # Ajouter une barre de titre personnalisée
        self.title_bar = self.create_title_bar()
        self.main_layout.addWidget(self.title_bar)

        # Ajouter la zone de défilement, les contrôles et la zone de log
        self.setup_scroll_area()
        self.setup_controls()
        self.setup_log_area()

        # Charger le fichier CSS
        try:
            self.load_stylesheet("src/dataPickerUI.css")
        except FileNotFoundError:
            self.load_stylesheet("dataPickerUI.css")


        # Ajouter un couple par défaut
        self.add_couple()

        # Connecter la méthode de nettoyage au signal de fermeture
        QApplication.instance().aboutToQuit.connect(self.cleanup)

        # Variables pour déplacer la fenêtre
        self.old_pos = None

    def create_title_bar(self):
        """Créer une barre de titre personnalisée."""
        title_bar = QWidget(self)
        title_bar.setObjectName("title_bar")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 10, 10)
        title_layout.setSpacing(2)

        # Icône de l'application
        app_icon = QLabel(self)
        app_icon.setPixmap(QIcon("img/dataPickerLogo.png").pixmap(24, 24))

        # Titre de l'application
        title_label = QLabel("Application Cartographique", self)
        title_label.setStyleSheet("color: white; font-size: 14px;")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Bouton de fermeture
        close_button = QPushButton("✕", self)
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)

        # Ajouter les widgets à la barre
        title_layout.addWidget(app_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)

        return title_bar

    def paintEvent(self, event):
        """Draw rounded corners and a border around the outer edge of the window."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # Draw the border
        border_color = QColor(68, 68, 68)  # #444
        border_width = 2
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(border_color, border_width))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)

        # Draw the background
        painter.setBrush(QBrush(QColor(32, 32, 32)))  # Background color
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect.adjusted(border_width, border_width, -border_width, -border_width), 10, 10)

    def mousePressEvent(self, event):
        """Gérer les clics de souris pour le déplacement ou le redimensionnement."""
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            self.old_resize_pos = event.globalPosition().toPoint()

            # Déterminer si le clic est dans une zone de redimensionnement
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                event.accept()
            else:
                self.resizing = False

    def mouseMoveEvent(self, event):
        """Gérer les mouvements de la souris pour déplacer ou redimensionner la fenêtre."""
        if self.resizing:
            # Calculer la nouvelle taille en fonction de la direction
            delta = event.globalPosition().toPoint() - self.old_resize_pos
            rect = self.geometry()

            new_width = rect.width()
            new_height = rect.height()

            if 'left' in self.resize_direction:
                new_width = max(rect.width() - delta.x(), self.minimumWidth())
                rect.setLeft(rect.right() - new_width)
            if 'right' in self.resize_direction:
                new_width = max(rect.width() + delta.x(), self.minimumWidth())
                rect.setRight(rect.left() + new_width)
            if 'top' in self.resize_direction:
                new_height = max(rect.height() - delta.y(), self.minimumHeight())
                rect.setTop(rect.bottom() - new_height)
            if 'bottom' in self.resize_direction:
                new_height = max(rect.height() + delta.y(), self.minimumHeight())
                rect.setBottom(rect.top() + new_height)

            self.setGeometry(rect)
            self.old_resize_pos = event.globalPosition().toPoint()
            event.accept()
        elif self.old_pos:
            # Déplacer la fenêtre
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            # Mettre à jour le curseur en fonction de la position
            resize_direction = self.get_resize_direction(event.pos())
            if resize_direction:
                self.setCursor(self.get_resize_cursor(resize_direction))
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        """Réinitialiser les variables après le déplacement ou le redimensionnement."""
        if self.resizing:
            self.resizing = False
            rect = self.geometry()

            # Enforce minimum dimensions after resizing
            if rect.width() < self.minimumWidth():
                rect.setWidth(self.minimumWidth())
            if rect.height() < self.minimumHeight():
                rect.setHeight(self.minimumHeight())
            self.setGeometry(rect)

        self.old_pos = None
        self.old_resize_pos = None
        event.accept()

    def get_resize_direction(self, pos):
        """Déterminer la direction de redimensionnement en fonction de la position."""
        rect = self.rect()
        direction = ''

        if pos.x() <= self.resize_margin:
            direction += 'left'
        elif pos.x() >= rect.width() - self.resize_margin:
            direction += 'right'

        if pos.y() <= self.resize_margin:
            direction += 'top'
        elif pos.y() >= rect.height() - self.resize_margin:
            direction += 'bottom'

        return direction if direction else None

    def get_resize_direction(self, pos):
        """Déterminer la direction de redimensionnement en fonction de la position."""
        rect = self.rect()
        direction = ''

        if pos.x() <= self.resize_margin:
            direction += 'left'
        elif pos.x() >= rect.width() - self.resize_margin:
            direction += 'right'

        if pos.y() <= self.resize_margin:
            direction += 'top'
        elif pos.y() >= rect.height() - self.resize_margin:
            direction += 'bottom'

        return direction if direction else None

    def get_resize_cursor(self, direction):
        """Retourne le curseur approprié en fonction de la direction de redimensionnement."""
        if direction in ('left', 'right'):
            return Qt.SizeHorCursor
        elif direction in ('top', 'bottom'):
            return Qt.SizeVerCursor
        elif 'left' in direction and 'top' in direction:
            return Qt.SizeFDiagCursor
        elif 'right' in direction and 'bottom' in direction:
            return Qt.SizeFDiagCursor
        elif 'left' in direction and 'bottom' in direction:
            return Qt.SizeBDiagCursor
        elif 'right' in direction and 'top' in direction:
            return Qt.SizeBDiagCursor
        return Qt.ArrowCursor

    def setup_scroll_area(self):
        """Configurer une zone de défilement pour ajouter des couples."""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

    def setup_controls(self):
        """Configurer les boutons de contrôle pour ajouter des couples."""
        button_layout = QHBoxLayout()

        # Bouton "Ajouter un couple" avec alignement en haut
        self.add_couple_button = QPushButton("Ajouter un couple")
        self.add_couple_button.setObjectName("addCoupleButton")  # Nom pour le ciblage CSS
        self.add_couple_button.clicked.connect(self.add_couple)
        button_layout.addWidget(self.add_couple_button, alignment=Qt.AlignTop)

        # Bouton "Générer et exporter" avec alignement en haut
        self.generate_button = QPushButton("Générer et exporter")
        self.generate_button.setObjectName("generateButton")  # Nom pour le ciblage CSS
        self.generate_button.setEnabled(False)  # Désactivé jusqu'à ce que tous les couples soient vérifiés
        self.generate_button.clicked.connect(self.generate_and_export)
        button_layout.addWidget(self.generate_button, alignment=Qt.AlignTop)
        
        self.main_layout.addLayout(button_layout)

    def setup_log_area(self):
        """Configurer la zone de log pour afficher les actions."""
        self.log_area = QTextEdit()
        self.log_area.setObjectName("log_area")  # Définir l'objectName pour le ciblage CSS
        self.log_area.setReadOnly(True)
        self.main_layout.addWidget(self.log_area)

    def load_stylesheet(self, filename):
        """Charger les styles CSS à partir d'un fichier externe."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            self.log_area.append(f"Erreur : Fichier de style '{filename}' introuvable.")
        except UnicodeDecodeError as e:
            self.log_area.append(f"Erreur : Impossible de décoder le fichier '{filename}'. {e}")

    def add_couple(self):
        """Ajouter un nouveau couple à l'interface."""
        couple_id = self.next_couple_id
        self.next_couple_id += 1

        group_box = QGroupBox()
        layout = QVBoxLayout(group_box)

        # Ajouter couple_id à self.couples
        self.couples[couple_id] = {
            'group_box': group_box,
            'zone_verified': False,
            'points_verified': False
        }

        self.add_couple_header(layout, couple_id)
        self.add_couple_content(layout, couple_id)
        self.scroll_layout.addWidget(group_box)

        self.log_area.append(f"Couple {self.get_couple_display_number(couple_id)} ajouté.\n")
        self.update_generate_button_state()
        self.renumber_couples()  # Mettre à jour les étiquettes de l'interface

    def get_couple_display_number(self, couple_id):
        """Retourne le numéro d'affichage pour un couple donné."""
        return list(self.couples.keys()).index(couple_id) + 1

    def add_couple_header(self, layout, couple_id):
        """Ajouter un titre et un bouton de suppression à l'en-tête d'un couple."""
        title_layout = QHBoxLayout()
        display_number = self.get_couple_display_number(couple_id)
        title_label = QLabel(f"Couple {display_number}")
        title_label.setObjectName("groupTitle")
        title_label.setProperty("couple_id", couple_id)
        title_layout.addWidget(title_label, alignment=Qt.AlignLeft)

        remove_button = QPushButton("✕")
        remove_button.setObjectName("smallButton")
        remove_button.clicked.connect(lambda: self.remove_couple(couple_id))
        remove_button.setToolTip("Supprimer ce couple")
        title_layout.addWidget(remove_button, alignment=Qt.AlignRight)

        layout.addLayout(title_layout)

    def add_couple_content(self, layout, couple_id):
        """Ajouter les sections Zone et Points à un couple."""
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        # Ajouter le widget Zone
        zone_widget = self.create_section_widget(couple_id, "zone")
        content_layout.addWidget(zone_widget)

        # Ajouter un séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(separator)

        # Ajouter le widget Points
        points_widget = self.create_section_widget(couple_id, "points")
        content_layout.addWidget(points_widget)

        layout.addLayout(content_layout)

    def remove_couple(self, couple_id):
        """Supprimer un couple et mettre à jour l'interface."""
        couple_display_number = self.get_couple_display_number(couple_id)
        group_box = self.couples[couple_id]['group_box']

        self.scroll_layout.removeWidget(group_box)
        group_box.deleteLater()
        del self.couples[couple_id]
        self.log_area.append(f"Couple {couple_display_number} supprimé.\n")
        self.update_generate_button_state()
        self.renumber_couples()
        remove_couple_data(couple_display_number)

    def renumber_couples(self):
        """Renuméroter les couples pour maintenir l'ordre séquentiel dans l'interface."""
        for display_number, couple_id in enumerate(self.couples.keys(), start=1):
            group_box = self.couples[couple_id]['group_box']
            layout = group_box.layout()
            title_layout = layout.itemAt(0).layout()
            title_label = title_layout.itemAt(0).widget()
            title_label.setText(f"Couple {display_number}")

    def create_section_widget(self, couple_id, section):
        """Créer la section Zone ou Points pour un couple."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Ajouter les champs de saisie et le bouton de vérification
        self.add_input_fields(layout, couple_id, section)

        return widget

    def add_input_fields(self, layout, couple_id, section):
        """Ajouter les champs de saisie et un bouton de vérification à une section."""
        # Noms des champs et bouton de vérification
        name_layout = QHBoxLayout()
        name_input = QLineEdit()
        name_input.setObjectName(f"{section}_name_{couple_id}")
        verify_button = QPushButton("Vérifier")
        verify_button.setObjectName(f"{section}_verify_button_{couple_id}")
        verify_button.setEnabled(False)
        
        # Ajout avec alignement en haut
        name_layout.addWidget(name_input, alignment=Qt.AlignTop)
        name_layout.addWidget(verify_button, alignment=Qt.AlignTop)
        
        layout.addRow(QLabel(f"{section.capitalize()} Nom :"), name_layout)
        
        # Source dropdown et champs dynamiques
        source_dropdown = QComboBox()
        source_dropdown.setObjectName(f"{section}_source_{couple_id}")
        source_dropdown.addItems(["Local", "API", "URL"])
        disable_scroll_wheel(source_dropdown)
        
        # Alignement pour le dropdown
        layout.addRow(QLabel("Source :"), source_dropdown)
        
        # Champs dynamiques basés sur le type de source
        dynamic_widget = self.create_dynamic_fields(couple_id, section, source_dropdown)
        layout.addRow(QLabel("Détails de la source :"), dynamic_widget)
        
        # Connecter les signaux
        name_input.textChanged.connect(
            lambda: self.update_verify_button_state(
                name_input, dynamic_widget, verify_button, couple_id, section
            )
        )
        
        # Connexion des signaux pour tous les champs dynamiques
        # Local field
        local_field = dynamic_widget.widget(0).findChild(QLineEdit, f"{section}_local_field_{couple_id}")
        local_field.textChanged.connect(
            lambda: self.update_verify_button_state(
                name_input, dynamic_widget, verify_button, couple_id, section
            )
        )
        
        # API fields
        api_url_field = dynamic_widget.widget(1).findChild(QLineEdit, f"{section}_api_url_field_{couple_id}")
        api_params_field = dynamic_widget.widget(1).findChild(QPlainTextEdit, f"{section}_api_params_field_{couple_id}")
        api_url_field.textChanged.connect(
            lambda: self.update_verify_button_state(
                name_input, dynamic_widget, verify_button, couple_id, section
            )
        )
        api_params_field.textChanged.connect(
            lambda: self.update_verify_button_state(
                name_input, dynamic_widget, verify_button, couple_id, section
            )
        )
        
        # URL field
        url_field = dynamic_widget.widget(2).findChild(QLineEdit, f"{section}_url_field_{couple_id}")
        url_field.textChanged.connect(
            lambda: self.update_verify_button_state(
                name_input, dynamic_widget, verify_button, couple_id, section
            )
        )
        
        # Mettre à jour l'état du bouton lors du changement de source
        source_dropdown.currentTextChanged.connect(
            lambda: self.update_verify_button_state(
                name_input, dynamic_widget, verify_button, couple_id, section
            )
        )
        
        verify_button.clicked.connect(
            lambda: self.verify_button_action(couple_id, section, verify_button)
        )

    def create_dynamic_fields(self, couple_id, section, source_dropdown):
        """Crée des champs dynamiques pour les différents types de source."""
        # Création du QStackedWidget
        stacked_widget = QStackedWidget()
        stacked_widget.setObjectName(f"{section}_stacked_widget_{couple_id}")

        # Widget pour la source "Local"
        local_widget = QWidget()
        local_layout = QHBoxLayout(local_widget)
        local_field = QLineEdit(placeholderText="Chemin vers un fichier local...")
        local_field.setObjectName(f"{section}_local_field_{couple_id}")
        local_button = QPushButton("...")
        local_button.clicked.connect(lambda: self.open_file_dialog(local_field))
        
        # Ajout avec alignement en haut
        local_layout.addWidget(local_field, alignment=Qt.AlignTop)
        local_layout.addWidget(local_button, alignment=Qt.AlignTop)
        stacked_widget.addWidget(local_widget)  # Index 0

        # Widget pour la source "API"
        api_widget = QWidget()
        api_layout = QFormLayout(api_widget, alignment=Qt.AlignTop)
        
        api_url_field = QLineEdit(placeholderText="Entrez l'URL de l'API...")
        api_url_field.setObjectName(f"{section}_api_url_field_{couple_id}")
        api_params_field = QPlainTextEdit()
        api_params_field.setPlaceholderText("Entrez les paramètres de l'API au format JSON...")
        api_params_field.setObjectName(f"{section}_api_params_field_{couple_id}")
        
        # Alignement en haut pour les champs API
        api_layout.addRow(QLabel("URL de l'API :"), api_url_field)
        api_layout.addRow(QLabel("Paramètres de l'API :"), api_params_field)
        stacked_widget.addWidget(api_widget)  # Index 1

        # Widget pour la source "URL"
        url_widget = QWidget()
        url_layout = QHBoxLayout(url_widget)
        url_field = QLineEdit(placeholderText="Entrez une URL...")
        url_field.setObjectName(f"{section}_url_field_{couple_id}")
        
        # Ajout avec alignement en haut
        url_layout.addWidget(url_field, alignment=Qt.AlignTop)
        stacked_widget.addWidget(url_widget)  # Index 2

        # Fonction pour mettre à jour le widget en fonction de la source sélectionnée
        def on_source_changed(text):
            if text == "Local":
                stacked_widget.setCurrentIndex(0)
            elif text == "API":
                stacked_widget.setCurrentIndex(1)
            elif text == "URL":
                stacked_widget.setCurrentIndex(2)

        source_dropdown.currentTextChanged.connect(on_source_changed)
        on_source_changed(source_dropdown.currentText())

        return stacked_widget

    def update_dynamic_field(self, choice, field, button):
        """Mettre à jour le placeholder et la visibilité du bouton en fonction de la sélection."""
        button.setVisible(choice == "Local")
        placeholders = {
            "Local": "Chemin vers un fichier local...",
            "URL": "Entrez une URL...",
            "API": "Entrez les paramètres de l'API..."
        }
        field.setPlaceholderText(placeholders.get(choice, ""))

    def open_file_dialog(self, field):
        """Ouvrir une boîte de dialogue pour sélectionner un fichier et définir le chemin dans le champ."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez un fichier")
        if file_path:
            field.setText(file_path)

    def update_verify_button_state(self, name_input, dynamic_widget, verify_button, couple_id, section):
        """Mettre à jour l'état du bouton de vérification et gérer la dé-vérification."""
        # Obtenir le type de source actuel
        source_dropdown = self.findChild(QComboBox, f"{section}_source_{couple_id}")
        source_type = source_dropdown.currentText()

        # Déterminer les champs à vérifier en fonction du type de source
        fields_filled = False
        if source_type == "Local":
            local_field = dynamic_widget.widget(0).findChild(QLineEdit, f"{section}_local_field_{couple_id}")
            fields_filled = bool(name_input.text()) and bool(local_field.text())
        elif source_type == "API":
            api_url_field = dynamic_widget.widget(1).findChild(QLineEdit, f"{section}_api_url_field_{couple_id}")
            # Les paramètres de l'API peuvent être optionnels
            fields_filled = bool(name_input.text()) and bool(api_url_field.text())
        elif source_type == "URL":
            url_field = dynamic_widget.widget(2).findChild(QLineEdit, f"{section}_url_field_{couple_id}")
            fields_filled = bool(name_input.text()) and bool(url_field.text())

        if verify_button.text() == "✔️" and not verify_button.isEnabled():
            verify_button.setText("Vérifier")
            verify_button.setEnabled(True)
            self.couples[couple_id][f"{section}_verified"] = False
            self.update_generate_button_state()

            # Supprimer les données de la couche
            couple_display_number = self.get_couple_display_number(couple_id)
            remove_layer_data(couple_display_number, section)
            self.log_area.append(
                f"Le {section} pour le Couple {couple_display_number} a été supprimé du JSON et le fichier associé a été supprimé en raison de modifications des champs.\n"
            )

        verify_button.setEnabled(fields_filled)

    def update_generate_button_state(self):
        """Activer ou désactiver le bouton 'Générer et exporter'."""
        all_verified = all(
            couple['zone_verified'] and couple['points_verified']
            for couple in self.couples.values()
        )
        self.generate_button.setEnabled(all_verified)

    def collect_couple_data(self):
        """Collecter les données de tous les couples et les retourner sous forme de dictionnaire."""
        data = {}
        for couple_id in self.couples:
            couple_display_number = self.get_couple_display_number(couple_id)
            group_widget = self.couples[couple_id]['group_box']

            zone_data = self.extract_section_data(group_widget, "zone", couple_id)
            points_data = self.extract_section_data(group_widget, "points", couple_id)

            couple_data = {}
            if self.couples[couple_id]['zone_verified']:
                couple_data["Zone"] = {
                    "name": zone_data["name"],
                    "source": f"data/couple{couple_display_number}_zone.fgb"
                }
            if self.couples[couple_id]['points_verified']:
                couple_data["Points"] = {
                    "name": points_data["name"],
                    "source": f"data/couple{couple_display_number}_points.fgb"
                }

            if couple_data:
                data[f"Couple {couple_display_number}"] = couple_data
        return data

    def export_data(self, export_name):
        """Exporter le répertoire 'temp' vers 'www/export_name'."""
        export_path = os.path.join('www', export_name)
        try:
            if not os.path.exists(export_path):
                shutil.copytree('temp', export_path)
                self.log_area.append(f"Contenu temporaire exporté vers '{export_path}'.\n")
                return export_path
            else:
                QMessageBox.warning(self, "Erreur d'exportation", f"Le dossier '{export_name}' existe déjà.")
                return None
        except Exception as e:
            self.log_area.append(f"Erreur lors de l'exportation du contenu : {e}\n")
            QMessageBox.warning(self, "Erreur d'exportation", f"Erreur lors de l'exportation du contenu : {e}")
            return None

    def open_exported_folder(self, export_path):
        """Ouvrir le dossier exporté dans l'explorateur de fichiers par défaut."""
        if os.path.exists(export_path):
            try:
                export_path_abs = os.path.abspath(export_path)
                if sys.platform.startswith('win'):
                    os.startfile(export_path_abs)  # Pour Windows
                elif sys.platform.startswith('darwin'):
                    subprocess.call(['open', export_path_abs])  # Pour macOS
                else:
                    subprocess.call(['xdg-open', export_path_abs])  # Pour Linux
                QMessageBox.information(
                    self, "Action",
                    f"Contenu exporté enregistré dans '{export_path}' et dossier ouvert."
                )
            except Exception as e:
                self.log_area.append(f"Erreur lors de l'ouverture du dossier : {e}\n")
                QMessageBox.information(
                    self, "Action",
                    f"Contenu exporté enregistré dans '{export_path}', mais échec de l'ouverture du dossier."
                )
        else:
            QMessageBox.information(
                self, "Action",
                f"Contenu exporté enregistré dans '{export_path}', mais le dossier est introuvable."
            )

    def generate_and_export(self):
        """Génère le fichier JSON et exporte le contenu temporaire."""
        # Demander à l'utilisateur un nom
        export_name, ok = QInputDialog.getText(self, "Nom de l'exportation", "Entrez un nom pour l'exportation :")
        if not ok or not export_name:
            self.log_area.append("Exportation annulée par l'utilisateur.\n")
            return

        # Collecter les données
        data = self.collect_couple_data()

        # Mettre à jour le fichier JSON
        update_json_file(data, self.log_area)
        self.log_area.append("Fichier JSON généré.\n")

        # Exporter les données
        export_path = self.export_data(export_name)
        if export_path is None:
            return

        # Appeler le script Jinja pour générer une page web
        try:
            self.log_area.append("Génération de la page web...\n")
            html_output_path = generate_web_page(os.path.join("www", export_name, "data","report.json"))  # Appeler avec le chemin du JSON
            self.log_area.append(f"Page web générée : {html_output_path}\n")
        except Exception as e:
            self.log_area.append(f"Erreur lors de la génération de la page web : {str(e)}\n")

        # Proposer de lancer le serveur HTTP
        self.propose_launch_server(html_output_path.replace("\\index.html", ""))
        
        # Ouvrir le dossier exporté
        self.open_exported_folder(html_output_path.replace("\\index.html", ""))

    def propose_launch_server(self, export_path):
        """Propose à l'utilisateur de lancer un serveur HTTP pour le dossier exporté."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Lancer le serveur HTTP")
        msg_box.setText("Voulez-vous lancer un serveur HTTP pour visualiser les fichiers exportés?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)

        # Connecter les boutons aux actions
        ret = msg_box.exec_()

        if ret == QMessageBox.Yes:
            self.launch_http_server(export_path)

    def launch_http_server(self, export_path):
        """Lance un serveur HTTP dans le répertoire export_path."""
        try:
            # Définir le répertoire de travail
            os.chdir(export_path)

            # Lancer le serveur HTTP en arrière-plan
            # Utilisation de subprocess.Popen pour ne pas bloquer l'interface
            subprocess.Popen(["py", "-m", "http.server"], cwd=export_path)

            self.log_area.append(f"Serveur HTTP lancé dans {export_path}\n")
            QMessageBox.information(self, "Serveur HTTP", f"Serveur HTTP lancé dans {export_path} sur le port 8000.")
        except Exception as e:
            self.log_area.append(f"Erreur lors du lancement du serveur HTTP : {str(e)}\n")
            QMessageBox.critical(self, "Erreur", f"Impossible de lancer le serveur HTTP : {str(e)}")

    def cleanup(self):
        """Nettoyer les ressources et arrêter le serveur HTTP à la fermeture."""
        
        # Arrêter le serveur HTTP
        if hasattr(self, 'http_server') and self.http_server:
            try:
                self.http_server.shutdown()  # Méthode pour arrêter le serveur
                self.log_area.append("Serveur HTTP arrêté à la fermeture.\n")
            except Exception as e:
                self.log_area.append(f"Erreur lors de l'arrêt du serveur HTTP : {e}\n")

        # Supprimer le dossier 'temp' dans le répertoire courant
        current_temp_path = os.path.join(os.getcwd(), 'temp')
        if os.path.exists(current_temp_path):
            try:
                shutil.rmtree(current_temp_path)
                self.log_area.append("Dossier temporaire 'temp' supprimé dans le répertoire courant à la fermeture.\n")
            except Exception as e:
                self.log_area.append(f"Erreur lors de la suppression du dossier 'temp' dans le répertoire courant : {e}\n")

        # Supprimer le dossier 'temp' dans le répertoire parent
        parent_temp_path = os.path.join(os.path.dirname(os.getcwd()), 'temp')
        if os.path.exists(parent_temp_path):
            try:
                shutil.rmtree(parent_temp_path)
                self.log_area.append("Dossier temporaire 'temp' supprimé dans le répertoire parent à la fermeture.\n")
            except Exception as e:
                self.log_area.append(f"Erreur lors de la suppression du dossier 'temp' dans le répertoire parent : {e}\n")

    def verify_button_action(self, couple_id, section, verify_button):
        """Gérer l'événement de clic sur le bouton de vérification."""
        group_widget = self.couples[couple_id]['group_box']

        # Extraire les données
        section_data = self.extract_section_data(group_widget, section, couple_id)

        # Déterminer le type de source
        source_type = section_data["source"].lower()  # "local", "url", "api"

        # Déterminer le type attendu (zone ou points)
        expected_type = section

        # Obtenir le numéro d'affichage du couple
        couple_display_number = self.get_couple_display_number(couple_id)

        # Préparer les paramètres
        api_params = None
        if source_type == "api":
            api_url = section_data.get("api_url", "")
            api_params_text = section_data.get("api_params", "")
            try:
                api_params = json.loads(api_params_text) if api_params_text else {}
            except json.JSONDecodeError as e:
                self.log_area.append(f"Erreur lors de l'analyse des paramètres API JSON : {e}")
                self.log_area.append("")  # Ajouter une ligne vide pour la lisibilité
                return

            source = api_url
        else:
            source = section_data.get("value", "")

        # Appeler la fonction de vérification
        result = verify_and_update_json(
            couple_display_number=couple_display_number,
            section=section,
            name=section_data["name"],
            source=source,
            expected_type=expected_type,
            source_type=source_type,
            api_params=api_params
        )

        # Mettre à jour l'interface utilisateur en fonction du résultat
        if result["success"]:
            verify_button.setText("✔️")
            verify_button.setEnabled(False)
            self.couples[couple_id][f"{section}_verified"] = True
            self.log_area.append(result["message"])
            self.log_area.append("")  # Ajouter une ligne vide pour la lisibilité
            self.update_generate_button_state()
        else:
            self.log_area.append(result["message"])
            self.log_area.append("")  # Ajouter une ligne vide pour la lisibilité

    def extract_section_data(self, group_widget, section, couple_id):
        """Extraire les données pour une section spécifique dans un couple."""
        section_data = {}
        try:
            couple_display_number = self.get_couple_display_number(couple_id)
            self.log_area.append(
                f"Traitement du Couple {couple_display_number} pour la section {section}."
            )

            # Récupérer les widgets
            name_widget = group_widget.findChild(QLineEdit, f"{section}_name_{couple_id}")
            source_widget = group_widget.findChild(QComboBox, f"{section}_source_{couple_id}")
            stacked_widget = group_widget.findChild(QStackedWidget, f"{section}_stacked_widget_{couple_id}")

            if name_widget and source_widget and stacked_widget:
                section_data["name"] = name_widget.text()
                section_data["source"] = source_widget.currentText()

                # Récupérer les données en fonction de la source
                if section_data["source"] == "Local":
                    local_field = stacked_widget.widget(0).findChild(QLineEdit, f"{section}_local_field_{couple_id}")
                    section_data["value"] = local_field.text()
                elif section_data["source"] == "API":
                    api_url_field = stacked_widget.widget(1).findChild(QLineEdit, f"{section}_api_url_field_{couple_id}")
                    api_params_field = stacked_widget.widget(1).findChild(QPlainTextEdit, f"{section}_api_params_field_{couple_id}")
                    section_data["api_url"] = api_url_field.text()
                    section_data["api_params"] = api_params_field.toPlainText()
                elif section_data["source"] == "URL":
                    url_field = stacked_widget.widget(2).findChild(QLineEdit, f"{section}_url_field_{couple_id}")
                    section_data["value"] = url_field.text()
                else:
                    section_data["value"] = ""

                # Enregistrement des données extraites
                self.log_area.append(
                    f"Données extraites pour {section} dans le Couple {couple_display_number} : {section_data}"
                )
                self.log_area.append("")  # Ajouter une ligne vide pour la lisibilité
            else:
                self.log_area.append(
                    f"Erreur : Widgets manquants pour {section} dans le Couple {couple_display_number}."
                )
                self.log_area.append("")  # Ajouter une ligne vide pour la lisibilité
        except Exception as e:
            self.log_area.append(f"Erreur dans extract_section_data : {e}")
            self.log_area.append("")  # Ajouter une ligne vide pour la lisibilité

        return section_data


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
