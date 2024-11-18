import os
import json
from geoUtils import load_geodata, load_geodata_from_api, save_geodata

def verify_and_update_json(
    couple_display_number, section, name, source, expected_type,
    source_type="local", api_params=None
):
    """
    Vérifie les données géospatiales et les enregistre sous forme de fichier GeoJSON.

    Args:
        couple_display_number (int): Numéro d'affichage du couple.
        section (str): 'zone' ou 'points'.
        name (str): Nom de la section.
        source (str): Chemin, URL ou paramètres de l'API.
        expected_type (str): Type attendu ('zone' ou 'points').
        source_type (str): Type de source ('local', 'url' ou 'api').
        api_params (dict): Paramètres pour les requêtes API.

    Returns:
        dict: Résultat avec "success" et "message".
    """
    try:
        # Charger les données en fonction du type de source
        if source_type == "local":
            result = load_geodata(source, expected_type)
        elif source_type == "url":
            result = load_geodata_from_url(source, expected_type)
        elif source_type == "api":
            # Extraire la méthode HTTP si fournie
            method = api_params.pop('method', 'GET') if api_params else 'GET'
            result = load_geodata_from_api(source, params=api_params, expected_type=expected_type, method=method)
        else:
            return {"success": False, "message": f"Type de source non pris en charge : {source_type}"}

        if not result["success"]:
            return result

        gdf = result["data"]

        # Enregistrer les données validées
        save_result = save_geodata(gdf, couple_display_number, section)
        if not save_result["success"]:
            return save_result

        # Message de réussite
        return {"success": True, "message": save_result["message"]}

    except Exception as e:
        message = f"Erreur lors de la validation ou de l'enregistrement des données : {e}"
        logging.exception(message)
        return {"success": False, "message": message}


def update_json_file(data, log_area):
    """
    Met à jour le fichier JSON avec les données fournies.

    Args:
        data (dict): Données à écrire dans le fichier JSON.
        log_area (QTextEdit): Référence à la zone de log pour enregistrer les messages.
    """
    # Écrire les données dans le fichier JSON
    json_file_path = os.path.join("temp", "data", "report.json")
    os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
    try:
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        log_area.append(f"JSON enregistré avec succès dans {json_file_path}\n")
    except Exception as e:
        log_area.append(f"Erreur lors de l'enregistrement du fichier JSON : {e}\n")