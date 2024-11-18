import os
import geopandas as gpd
from shapely.geometry import Point
import logging
import requests
from pathlib import Path
import tempfile
import zipfile
import json
import shutil
from io import BytesIO
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtGui import QIcon

# Configuration du logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class FieldSelectionDialog(QDialog):
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sélectionner un champ")
        self.setMinimumWidth(300)
        self.setWindowIcon(QIcon("img/dataPickerLogo.png"))
        self.load_stylesheet("src/dataPickerUI.css")

        # Charger les styles globaux
        with open("src/dataPickerUI.css", "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

        # Layout principal
        layout = QVBoxLayout(self)

        # Label
        label = QLabel("Choisissez le champ à conserver :")
        layout.addWidget(label)

        # Dropdown
        self.field_dropdown = QComboBox()
        self.field_dropdown.addItems(fields)
        layout.addWidget(self.field_dropdown)

        # Bouton OK
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
    
    def get_selected_field(self):
        """Renvoie le champ sélectionné."""
        return self.field_dropdown.currentText()

    def load_stylesheet(self, filename):
        """Charger les styles CSS à partir d'un fichier externe."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            self.log_area.append(f"Erreur : Fichier de style '{filename}' introuvable.")
        except UnicodeDecodeError as e:
            self.log_area.append(f"Erreur : Impossible de décoder le fichier '{filename}'. {e}")


def clip_points_to_zone(points_gdf, zone_gdf):
    """
    Découpe les points en fonction de la géométrie de la zone.

    Args:
        points_gdf (GeoDataFrame): Le GeoDataFrame contenant les points.
        zone_gdf (GeoDataFrame): Le GeoDataFrame contenant la géométrie de la zone.

    Returns:
        dict: Résultat avec "success" et "data" ou "message".
    """
    try:
        # Vérifier si la zone est remplie
        if zone_gdf.empty:
            message = "La couche zone est vide. Impossible de découper les points. Commencez par la zone."
            logging.error(message)
            return {"success": False, "message": message}

        # Vérifier si les CRS sont définies
        if points_gdf.crs is None or zone_gdf.crs is None:
            message = "L'une des couches (points ou zone) n'a pas de CRS défini."
            logging.error(message)
            return {"success": False, "message": message}

        # Reprojection des données si nécessaire
        if points_gdf.crs != zone_gdf.crs:
            logging.info("Reprojection des données en CRS commun.")
            points_gdf = points_gdf.to_crs(zone_gdf.crs)

        # Découpe des points
        clipped_points = gpd.sjoin(points_gdf, zone_gdf, predicate="within")
        logging.info(f"{len(clipped_points)} points conservés après découpage.")
        
        return {"success": True, "data": clipped_points}

    except Exception as e:
        message = f"Erreur lors du découpage des points : {e}"
        logging.exception(message)
        return {"success": False, "message": message}

def process_points_with_zone(points_source, zone_source, points_section, zone_section):
    """
    Découpe les points par la géométrie de la zone.

    Args:
        points_source (str): Source des données des points (chemin ou URL).
        zone_source (str): Chemin vers la couche zone.
        points_section (str): Nom de la section des points.
        zone_section (str): Nom de la section de la zone.

    Returns:
        dict: Résultat avec "success", "message" et éventuellement les données découpées.
    """
    try:
        # Charger la couche zone
        zone_gdf = gpd.read_file(zone_source)
        if zone_gdf.crs.to_epsg() != 4326:
            zone_gdf = zone_gdf.to_crs(epsg=4326)
        logging.info("Couche zone chargée et reprojetée en WGS84.")

        # Charger la couche points
        if points_source.startswith("http://") or points_source.startswith("https://"):
            response = requests.get(points_source)
            response.raise_for_status()
            points_gdf = gpd.read_file(BytesIO(response.content))
        else:
            points_gdf = gpd.read_file(points_source)

        if points_gdf.crs.to_epsg() != 4326:
            points_gdf = points_gdf.to_crs(epsg=4326)
        logging.info("Couche points chargée et reprojetée en WGS84.")

        # Découpe les points par la géométrie de la zone
        clipped_gdf = gpd.overlay(points_gdf, zone_gdf, how='intersection')
        logging.info("Découpage des points par la zone effectué avec succès.")

        return {"success": True, "data": clipped_gdf}

    except requests.exceptions.RequestException as e:
        message = f"Erreur lors du téléchargement des données depuis l'URL : {e}"
        logging.exception(message)
        return {"success": False, "message": message}
    except Exception as e:
        message = f"Erreur lors du traitement des points et de la zone : {e}"
        logging.exception(message)
        return {"success": False, "message": message}

def load_geodata(source, expected_type):
    """
    Charge les données géospatiales à partir d'un fichier local et valide le type de géométrie.

    Args:
        source (str): Chemin vers le fichier local.
        expected_type (str): Type attendu des données ("zone" ou "points").

    Returns:
        dict: Résultat avec "success" et "data" ou "message".
    """
    try:
        logging.info(f"Tentative de chargement des données à partir du fichier local : {source}")
        if not os.path.exists(source):
            message = f"Le fichier '{source}' n'existe pas."
            logging.error(message)
            return {"success": False, "message": message}

        # Taille du fichier source en Mo
        original_size = os.path.getsize(source) / (1024 * 1024)  # Taille en Mo

        # Lire le fichier avec GeoPandas
        gdf = gpd.read_file(source)
        logging.info(f"Données chargées avec succès depuis {source}. Taille originelle : {original_size:.2f} Mo.")

        # Validation du type de géométrie
        if not validate_geometry_type(gdf, expected_type):
            found_types = gdf.geometry.geom_type.unique().tolist()
            message = f"Le type de géométrie des données ({found_types}) ne correspond pas au type attendu '{expected_type}'."
            logging.error(message)
            return {"success": False, "message": message}

        logging.info(f"Le type de géométrie correspond au type attendu '{expected_type}'.")
        return {"success": True, "data": gdf, "original_size": original_size}

    except Exception as e:
        message = f"Erreur lors du chargement des données géographiques : {e}"
        logging.exception(message)
        return {"success": False, "message": message}

def load_geodata_from_url(url, expected_type):
    """
    Télécharge et charge des données géospatiales depuis une URL.

    Args:
        url (str): URL du fichier de données géographiques.
        expected_type (str): Type attendu des données ("zone" ou "points").

    Returns:
        dict: Résultat avec "success" et "data" ou "message".
    """
    temp_dir = None
    try:
        logging.info(f"Tentative de téléchargement des données depuis l'URL : {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        logging.info("Téléchargement réussi.")

        content_type = response.headers.get("Content-Type", "")
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "downloaded_data"

        # Déterminer l'extension du fichier en fonction du type de contenu ou de l'URL
        if "geojson" in content_type or "json" in content_type or "text/plain" in content_type:
            temp_file = temp_file.with_suffix(".geojson")
        elif "zip" in content_type:
            temp_file = temp_file.with_suffix(".zip")
        elif url.endswith(".geojson") or url.endswith(".json"):
            temp_file = temp_file.with_suffix(".geojson")
        elif url.endswith(".zip"):
            temp_file = temp_file.with_suffix(".zip")
        else:
            message = f"Type de contenu ou extension non supportée : {content_type}"
            logging.error(message)
            return {"success": False, "message": message}

        # Écrire le contenu téléchargé dans un fichier temporaire
        with open(temp_file, "wb") as f:
            f.write(response.content)
        logging.info(f"Données enregistrées temporairement dans {temp_file}")

        # Si le fichier est un zip contenant des fichiers shapefile
        if temp_file.suffix == ".zip":
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                logging.info(f"Archive zip extraite dans {temp_dir}")

            # Rechercher un fichier .shp extrait
            shp_files = list(Path(temp_dir).glob("*.shp"))
            if shp_files:
                source_file = shp_files[0]
                logging.info(f"Fichier shapefile trouvé : {source_file}")
            else:
                message = "Aucun fichier shapefile trouvé dans l'archive zip."
                logging.error(message)
                return {"success": False, "message": message}
        else:
            source_file = temp_file

        # Si le fichier est un GeoJSON, effectuer une validation basique
        if source_file.suffix == ".geojson":
            try:
                with open(source_file, 'r', encoding='utf-8') as geojson_file:
                    geojson_data = geojson_file.read()
                    data = json.loads(geojson_data)
                    if 'features' not in data:
                        message = "Le GeoJSON ne contient pas de 'features'."
                        logging.error(message)
                        return {"success": False, "message": message}
                    logging.info("Le GeoJSON a été validé avec succès.")
            except json.JSONDecodeError as e:
                message = f"Erreur lors de la lecture du fichier GeoJSON : {e}"
                logging.error(message)
                return {"success": False, "message": message}

        # Charger et valider les données
        result = load_geodata(str(source_file), expected_type)

        return result

    except Exception as e:
        message = f"Erreur lors du chargement des données depuis l'URL : {e}"
        logging.exception(message)
        return {"success": False, "message": str(e)}
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info(f"Répertoire temporaire supprimé : {temp_dir}")

def load_geodata_from_api(api_url, params=None, expected_type="zone", method='GET'):
    """
    Envoie une requête à une API géographique et charge les données de réponse.

    Args:
        api_url (str): URL de l'API.
        params (dict): Paramètres de la requête pour l'API.
        expected_type (str): Type attendu des données ("zone" ou "points").
        method (str): Méthode HTTP ('GET' ou 'POST').

    Returns:
        dict: Résultat avec "success" et "data" ou "message".
    """
    try:
        logging.info(f"Envoi d'une requête {method} à l'API : {api_url} avec les paramètres : {params}")
        if method.upper() == 'GET':
            response = requests.get(api_url, params=params)
        elif method.upper() == 'POST':
            response = requests.post(api_url, data=params)
        else:
            message = f"Méthode HTTP non supportée : {method}"
            logging.error(message)
            return {"success": False, "message": message}

        response.raise_for_status()
        logging.info("Réponse de l'API reçue avec succès.")

        content_type = response.headers.get("Content-Type", "")
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "api_response"

        # Déterminer l'extension du fichier en fonction du type de contenu
        if "json" in content_type or "geojson" in content_type:
            temp_file = temp_file.with_suffix(".geojson")
        elif "xml" in content_type:
            temp_file = temp_file.with_suffix(".osm")  # Pour Overpass API
        else:
            message = f"Type de contenu non supporté pour les données de l'API : {content_type}"
            logging.error(message)
            return {"success": False, "message": message}

        # Écrire la réponse de l'API dans un fichier temporaire
        with open(temp_file, "wb") as f:
            f.write(response.content)
        logging.info(f"Données de l'API enregistrées temporairement dans {temp_file}")

        # Charger et valider les données
        result = load_geodata(str(temp_file), expected_type)

        # Nettoyer les fichiers temporaires
        temp_file.unlink(missing_ok=True)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info(f"Répertoire temporaire supprimé : {temp_dir}")

        return result

    except requests.RequestException as e:
        message = f"Erreur lors de l'accès à l'API : {e}"
        logging.exception(message)
        return {"success": False, "message": message}
    except Exception as e:
        message = f"Erreur lors du traitement des données de l'API : {e}"
        logging.exception(message)
        return {"success": False, "message": message}

def validate_geometry_type(gdf, expected_type):
    """
    Valide le type de géométrie des données géographiques.

    Args:
        gdf (GeoDataFrame): GeoDataFrame à valider.
        expected_type (str): Type attendu ("zone" ou "points").

    Returns:
        bool: True si toutes les géométries correspondent, sinon False.
    """
    if expected_type == "zone":
        valid_types = ["Polygon", "MultiPolygon"]
    elif expected_type == "points":
        valid_types = ["Point", "MultiPoint"]
    else:
        logging.error(f"Type attendu inconnu : {expected_type}")
        return False

    is_valid = gdf.geometry.geom_type.isin(valid_types).all()
    logging.debug(f"Validation du type de géométrie : {is_valid}")
    return is_valid

def save_geodata(gdf, couple_display_number, section_key, simplify_tolerance=0.001, parent=None):
    """
    Enregistre le GeoDataFrame dans un fichier FlatGeobuf en WGS84 avec simplification des géométries.

    Args:
        gdf (GeoDataFrame): Le GeoDataFrame à enregistrer.
        couple_display_number (int): Numéro d'affichage du couple.
        section_key (str): Clé de la section.
        simplify_tolerance (float): Tolérance de simplification géométrique.
        parent (QWidget): Parent pour les fenêtres de dialogue.

    Returns:
        dict: Résultat avec "success", "message", et "file_path".
    """
    try:
        # Vérifier si le GeoDataFrame a une CRS définie
        if gdf.crs is None:
            message = "Le GeoDataFrame n'a pas de système de coordonnées défini."
            logging.error(message)
            return {"success": False, "message": message}

        # Reprojection en WGS84 (EPSG:4326) si nécessaire
        if gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
            logging.info("Reprojection du GeoDataFrame en WGS84 (EPSG:4326).")

        # Simplification des géométries
        gdf["geometry"] = gdf["geometry"].simplify(simplify_tolerance)
        logging.info(f"Géométries simplifiées avec une tolérance de {simplify_tolerance}.")

        # Si la section est "zone", ne garder que la géométrie
        if section_key == "zone":
            gdf = gdf[["geometry"]]
            logging.info("Seule la géométrie est conservée pour la couche de zone.")

        # Si la section est "points", demander à l'utilisateur de choisir un champ
        if section_key == "points":
            fields = [col for col in gdf.columns if col != "geometry"]

            # Afficher une boîte de dialogue pour choisir le champ
            dialog = FieldSelectionDialog(fields, parent)
            if dialog.exec() == QDialog.Accepted:
                selected_field = dialog.get_selected_field()
                logging.info(f"Champ sélectionné pour les points : {selected_field}")

                # Garder uniquement le champ sélectionné et la géométrie
                gdf = gdf[[selected_field, "geometry"]]

                # Renommer le champ sélectionné en 'name'
                gdf = gdf.rename(columns={selected_field: "name"})
                logging.info(f"Le champ '{selected_field}' a été renommé en 'name'.")
            else:
                message = "Aucun champ n'a été sélectionné pour les points. Opération annulée."
                logging.error(message)
                return {"success": False, "message": message}

        # Construire le chemin de sortie
        output_dir = os.path.join("temp", "data")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"couple{couple_display_number}_{section_key.split('_')[0].lower()}.fgb"
        file_path = os.path.join(output_dir, filename)

        # Enregistrer au format FlatGeobuf
        gdf.to_file(file_path, driver="FlatGeobuf")
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Taille en Mo
        logging.info(f"Données enregistrées dans {file_path} ({file_size:.2f} Mo).")

        return {"success": True, "message": f"Données enregistrées dans {file_path}.", "file_path": file_path}
    except Exception as e:
        message = f"Erreur lors de l'enregistrement des données : {e}"
        logging.exception(message)
        return {"success": False, "message": message}
