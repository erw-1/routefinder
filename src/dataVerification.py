import os
import json
import logging
from geoUtils import (
    load_geodata,
    load_geodata_from_api,
    save_geodata,
    load_geodata_from_url,
    process_points_with_zone,
)

def verify_and_update_json(
    couple_display_number, section, name, source, expected_type,
    source_type="local", api_params=None
):
    """
    Vérifie les données géospatiales et les enregistre sous forme de fichier FlatGeobuf.

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
        # Charger ou valider la source de données
        if source_type == "local":
            result = load_geodata(source, expected_type)
        elif source_type == "url":
            result = load_geodata_from_url(source, expected_type)
        elif source_type == "api":
            method = api_params.pop('method', 'GET') if api_params else 'GET'
            result = load_geodata_from_api(source, params=api_params, expected_type=expected_type, method=method)
        else:
            return {"success": False, "message": f"Type de source non pris en charge : {source_type}"}

        if not result["success"]:
            return result

        gdf = result["data"]
        original_size = result.get("original_size", None)

        # Ajouter au log la taille originelle
        if original_size:
            logging.info(f"Fichier chargé avec une taille originelle de {original_size:.2f} Mo.")

        # Vérification et traitement spécifique pour les points
        if section == "points":
            # Vérifier l'existence de la couche zone pour le découpage
            zone_file_path = os.path.join("temp", "data", f"couple{couple_display_number}_zone.fgb")
            if not os.path.exists(zone_file_path):
                message = "La couche zone doit être remplie avant de traiter les points."
                logging.error(message)
                return {"success": False, "message": message}

            # Charger la couche zone et valider son contenu
            zone_result = load_geodata(zone_file_path, "zone")
            if not zone_result["success"] or zone_result["data"].empty:
                message = "La couche zone est vide ou invalide. Assurez-vous qu'elle est correctement définie."
                logging.error(message)
                return {"success": False, "message": message}

            # Découper les points avec la zone
            process_result = process_points_with_zone(source, zone_file_path, "points", "zone")
            if not process_result["success"]:
                return process_result

            gdf = process_result["data"]

        # Enregistrer les données validées
        save_result = save_geodata(gdf, couple_display_number, section)
        if not save_result["success"]:
            return save_result

        # Taille du fichier sauvegardé
        file_path = save_result.get("file_path")
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Taille en Mo
        logging.info(f"Données sauvegardées dans {file_path} avec une taille de {file_size:.2f} Mo.")

        # Enrichir le message de retour avec la taille originelle et la taille sauvegardée
        save_result["message"] += f" Taille du fichier sauvegardé : {file_size:.2f} Mo."
        if original_size:
            save_result["message"] = (
                f"Taille originelle : {original_size:.2f} Mo. " + save_result["message"]
            )

        # Afficher le message enrichi dans les logs
        logging.info(save_result["message"])

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
    json_file_path = os.path.join("temp", "data", "report.json")
    os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
    try:
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        log_area.append(f"JSON enregistré avec succès dans {json_file_path}\n")
    except Exception as e:
        log_area.append(f"Erreur lors de l'enregistrement du fichier JSON : {e}\n")
