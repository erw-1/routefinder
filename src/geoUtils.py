import os
import geopandas as gpd
import requests
from pathlib import Path
import tempfile
import zipfile
import logging

# Configuration du logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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
        # Vérifier si le fichier existe
        if not os.path.exists(source):
            message = f"Le fichier '{source}' n'existe pas."
            logging.error(message)
            return {"success": False, "message": message}

        # Lire le fichier avec GeoPandas
        gdf = gpd.read_file(source)
        logging.info(f"Données chargées avec succès depuis {source}")

        # Validation du type de géométrie
        if not validate_geometry_type(gdf, expected_type):
            found_types = gdf.geometry.geom_type.unique().tolist()
            message = f"Le type de géométrie des données ({found_types}) ne correspond pas au type attendu '{expected_type}'."
            logging.error(message)
            return {"success": False, "message": message}

        logging.info(f"Le type de géométrie correspond au type attendu '{expected_type}'.")
        return {"success": True, "data": gdf}

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
    try:
        logging.info(f"Tentative de téléchargement des données depuis l'URL : {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        logging.info("Téléchargement réussi.")

        content_type = response.headers.get("Content-Type", "")
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "downloaded_data"

        # Déterminer l'extension du fichier en fonction du type de contenu
        if "json" in content_type or "geojson" in content_type:
            temp_file = temp_file.with_suffix(".geojson")
        elif "zip" in content_type:
            temp_file = temp_file.with_suffix(".zip")
        elif "kml" in content_type or "xml" in content_type:
            temp_file = temp_file.with_suffix(".kml")
        elif "octet-stream" in content_type:
            # Tentative de détection basée sur l'URL
            if url.endswith(".shp.zip") or url.endswith(".shp"):
                temp_file = temp_file.with_suffix(".zip")
            elif url.endswith(".geojson") or url.endswith(".json"):
                temp_file = temp_file.with_suffix(".geojson")
            elif url.endswith(".kml"):
                temp_file = temp_file.with_suffix(".kml")
            else:
                message = f"Type de contenu non supporté et extension inconnue pour l'URL : {url}"
                logging.error(message)
                return {"success": False, "message": message}
        else:
            message = f"Type de contenu non supporté : {content_type}"
            logging.error(message)
            return {"success": False, "message": message}

        # Écrire le contenu téléchargé dans un fichier temporaire
        with open(temp_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
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

        # Charger et valider les données
        result = load_geodata(str(source_file), expected_type)

        # Nettoyer les fichiers temporaires
        temp_file.unlink(missing_ok=True)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info(f"Répertoire temporaire supprimé : {temp_dir}")

        return result

    except requests.RequestException as e:
        message = f"Erreur lors du téléchargement des données depuis l'URL : {e}"
        logging.exception(message)
        return {"success": False, "message": message}
    except Exception as e:
        message = f"Erreur lors du traitement des données téléchargées : {e}"
        logging.exception(message)
        return {"success": False, "message": message}


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


def save_geodata(gdf, couple_display_number, section_key):
    """
    Enregistre le GeoDataFrame dans un fichier GeoJSON.

    Args:
        gdf (GeoDataFrame): Le GeoDataFrame à enregistrer.
        couple_display_number (int): Numéro d'affichage du couple.
        section_key (str): Clé de la section.

    Returns:
        dict: Résultat avec "success", "message" et "file_path".
    """
    try:
        # Construire le chemin de sortie en utilisant le numéro d'affichage
        output_dir = os.path.join("temp", "data")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"couple{couple_display_number}_{section_key.split('_')[0].lower()}.geojson"
        file_path = os.path.join(output_dir, filename)

        # Enregistrer le GeoDataFrame
        gdf.to_file(file_path, driver='GeoJSON')
        logging.info(f"Données enregistrées dans le fichier : {file_path}")

        return {
            "success": True,
            "message": f"Données enregistrées dans {file_path}.",
            "file_path": file_path
        }
    except Exception as e:
        message = f"Erreur lors de l'enregistrement des données : {e}"
        logging.exception(message)
        return {"success": False, "message": message}
