from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QScrollArea, QComboBox, QTextEdit,
    QGroupBox, QFrame, QFileDialog
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Application Cartographique")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumWidth(600)

        # Définir l'icône de l'application
        self.setWindowIcon(QIcon("img/dataPickerLogo.png"))

        # Initialiser le suivi des vérifications et le compteur de couples
        self.verification_status = {}
        self.couple_count = 0

        # Configuration de la mise en page principale
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Ajouter une zone défilante
        self.setup_scroll_area()

        # Ajouter les boutons de contrôle et la zone de journal
        self.setup_controls()
        self.setup_log_area()

        # Charger la feuille de style externe
        self.load_stylesheet("src/dataPickerUI.css")

        # Ajouter le premier couple par défaut
        self.add_couple()

    def setup_scroll_area(self):
        """Configure une zone défilante pour ajouter des couples."""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

    def setup_controls(self):
        """Configure les boutons de contrôle pour ajouter des couples et générer une sortie."""
        button_layout = QHBoxLayout()
        self.add_couple_button = QPushButton("Ajouter un couple")
        self.add_couple_button.clicked.connect(self.add_couple)
        button_layout.addWidget(self.add_couple_button)

        self.generate_button = QPushButton("Générer et ouvrir")
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self.generate_and_open)
        button_layout.addWidget(self.generate_button)

        self.main_layout.addLayout(button_layout)

    def setup_log_area(self):
        """Configure la zone de journal pour afficher les actions."""
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.main_layout.addWidget(self.log_area)

    def load_stylesheet(self, filename):
        """Charge les styles CSS à partir d'un fichier externe."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            self.log_area.append(f"Erreur : Fichier de style '{filename}' introuvable.")
        except UnicodeDecodeError as e:
            self.log_area.append(f"Erreur : Impossible de décoder le fichier '{filename}'. {e}")

    def add_couple(self):
        """Ajoute un nouveau couple à l'interface."""
        self.couple_count += 1
        couple_id = self.couple_count
        self.verification_status[couple_id] = {"zone_verified": False, "points_verified": False}

        # Crée une boîte de groupe pour le couple
        group_box = QGroupBox()
        layout = QVBoxLayout(group_box)

        # Ajouter un en-tête et un bouton de suppression optionnel
        self.add_couple_header(layout, couple_id, group_box)

        # Ajouter le contenu (sections Zone et Points)
        self.add_couple_content(layout, couple_id)

        # Ajouter la boîte de groupe à la zone défilante
        self.scroll_layout.addWidget(group_box)
        self.log_area.append(f"Couple {couple_id} ajouté.")
        self.update_generate_button_state()

    def add_couple_header(self, layout, couple_id, group_box):
        """Ajoute un titre et un bouton de suppression à l'en-tête d'un couple."""
        title_layout = QHBoxLayout()
        title_label = QLabel(f"Couple {couple_id}")
        title_label.setObjectName("groupTitle")
        title_layout.addWidget(title_label, alignment=Qt.AlignLeft)

        if couple_id > 1:
            remove_button = QPushButton("❌")
            remove_button.setObjectName("smallButton")
            remove_button.clicked.connect(lambda: self.remove_couple(group_box, couple_id))
            remove_button.setToolTip("Supprimer ce couple")
            title_layout.addWidget(remove_button, alignment=Qt.AlignRight)

        layout.addLayout(title_layout)

    def add_couple_content(self, layout, couple_id):
        """Ajoute les sections Zone et Points à un couple."""
        content_layout = QHBoxLayout()

        # Ajouter le widget Zone
        zone_widget = self.create_zone_widget(couple_id, "zone_verified")
        content_layout.addWidget(zone_widget)

        # Ajouter un séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(separator)

        # Ajouter le widget Points
        points_widget = self.create_zone_widget(couple_id, "points_verified")
        content_layout.addWidget(points_widget)

        layout.addLayout(content_layout)

    def remove_couple(self, group_box, couple_id):
        """Supprime un couple et met à jour l'interface utilisateur."""
        self.scroll_layout.removeWidget(group_box)
        group_box.deleteLater()
        del self.verification_status[couple_id]
        self.log_area.append(f"Couple {couple_id} supprimé.")
        self.renumber_couples()
        self.update_generate_button_state()

    def renumber_couples(self):
        """Renumérote tous les couples restants pour maintenir un ordre séquentiel."""
        for index in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(index).widget()
            if isinstance(widget, QGroupBox):
                layout = widget.layout()
                title_layout = layout.itemAt(0).layout()
                title_label = title_layout.itemAt(0).widget()
                title_label.setText(f"Couple {index + 1}")
        self.couple_count = self.scroll_layout.count()

    def create_zone_widget(self, couple_id, section):
        """Crée la section Zone ou Points pour un couple."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Ajouter des champs d'entrée et un bouton de vérification
        self.add_input_fields(layout, couple_id, section)

        return widget

    def add_input_fields(self, layout, couple_id, section):
        """Ajoute des champs d'entrée et un bouton de vérification à une section."""
        # Champ Nom et bouton Vérifier
        name_layout = QHBoxLayout()
        name_input = QLineEdit()
        verify_button = QPushButton("Vérifier")
        verify_button.setEnabled(False)
        name_layout.addWidget(name_input)
        name_layout.addWidget(verify_button)
        layout.addRow(QLabel(f"{section.split('_')[0].capitalize()} Nom :"), name_layout)

        # Menu déroulant Source et champ dynamique
        source_dropdown = QComboBox()
        source_dropdown.addItems(["Local", "API", "URL"])
        self.disable_scroll_wheel(source_dropdown)
        layout.addRow(QLabel("Source :"), source_dropdown)
        dynamic_field, dynamic_button = self.create_dynamic_field(layout, source_dropdown)

        # Connecter les signaux
        name_input.textChanged.connect(
            lambda: self.update_verify_button_state(name_input, dynamic_field, verify_button, couple_id, section)
        )
        dynamic_field.textChanged.connect(
            lambda: self.update_verify_button_state(name_input, dynamic_field, verify_button, couple_id, section)
        )
        verify_button.clicked.connect(
            lambda: self.verify_button_action(couple_id, section, verify_button)
        )

    def create_dynamic_field(self, layout, dropdown):
        """Crée un champ dynamique avec un bouton de sélection de fichier."""
        dynamic_layout = QHBoxLayout()
        field = QLineEdit(placeholderText="Chemin ou URL...")
        button = QPushButton("...")
        button.setObjectName("smallButton")
        button.setVisible(dropdown.currentText() == "Local")
        dropdown.currentTextChanged.connect(lambda: self.update_dynamic_field(dropdown.currentText(), field, button))
        dropdown.currentTextChanged.connect(lambda: field.clear())
        button.clicked.connect(lambda: self.open_file_dialog(field))
        dynamic_layout.addWidget(field)
        dynamic_layout.addWidget(button)
        layout.addRow(QLabel("Chemin/URL :"), dynamic_layout)
        return field, button

    def update_dynamic_field(self, choice, field, button):
        """Met à jour l'espace réservé et la visibilité du champ dynamique en fonction de la sélection du menu déroulant."""
        button.setVisible(choice == "Local")
        placeholders = {
            "Local": "Chemin vers un fichier local...",
            "URL": "Entrez une URL...",
            "API": "Entrez les paramètres de l'API..."
        }
        field.setPlaceholderText(placeholders.get(choice, ""))

    def open_file_dialog(self, field):
        """Ouvre une boîte de dialogue de fichier et définit le chemin sélectionné dans le champ."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez un fichier")
        if file_path:
            field.setText(file_path)

    def update_verify_button_state(self, name_input, dynamic_field, verify_button, couple_id, section):
        """Met à jour l'état du bouton de vérification."""
        fields_filled = bool(name_input.text()) and bool(dynamic_field.text())
        if verify_button.text() == "✔️" and not verify_button.isEnabled():
            verify_button.setText("Vérifier")
            verify_button.setEnabled(True)
            self.update_verification_status(couple_id, section, False)
        verify_button.setEnabled(fields_filled)

    def verify_button_action(self, couple_id, section, verify_button):
        """Gère les clics sur le bouton de vérification."""
        verify_button.setText("✔️")
        verify_button.setEnabled(False)
        self.update_verification_status(couple_id, section, True)

    def update_verification_status(self, couple_id, section, verified):
        """Met à jour le statut de vérification et l'état du bouton de génération."""
        self.verification_status[couple_id][section] = verified
        self.update_generate_button_state()

    def update_generate_button_state(self):
        """Active ou désactive le bouton 'Générer et ouvrir'."""
        all_verified = all(
            status["zone_verified"] and status["points_verified"]
            for status in self.verification_status.values()
        )
        self.generate_button.setEnabled(all_verified)

    def disable_scroll_wheel(self, widget):
        """Désactive la molette de défilement pour un QComboBox."""
        def wheelEvent(event):
            event.ignore()
        widget.wheelEvent = wheelEvent

    def generate_and_open(self):
        """Gère le processus de génération et d'ouverture."""
        self.log_area.append("Génération et ouverture...")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
