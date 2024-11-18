import os
import json

def disable_scroll_wheel(widget):
    """Désactive la molette de défilement pour un QComboBox."""
    def wheelEvent(event):
        event.ignore()
    widget.wheelEvent = wheelEvent

def remove_layer_data(couple_display_number, section):
    """Supprime les données de la couche du fichier JSON et efface le fichier associé."""
    # Supprimer la section du fichier JSON
    json_file = os.path.join("temp", "data", "report.json")
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        couple_key = f"Couple {couple_display_number}"
        section_name = section.capitalize()

        if couple_key in data and section_name in data[couple_key]:
            del data[couple_key][section_name]

            # Si le couple n'a plus de sections, supprimer l'entrée du couple
            if not data[couple_key]:
                del data[couple_key]

            # Enregistrer le JSON mis à jour
            with open(json_file, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
    except (FileNotFoundError, json.JSONDecodeError):
        # Le fichier JSON n'existe pas ou est invalide ; rien à supprimer
        pass

    # Supprimer le fichier GeoJSON associé en utilisant le numéro d'affichage
    file_path = os.path.join(
        "temp", "data", f"couple{couple_display_number}_{section}.fgb"
    )
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier {file_path} : {e}")

def remove_couple_data(couple_display_number):
    """Supprime les données du couple du fichier JSON et efface les fichiers associés."""
    # Supprimer du fichier JSON
    json_file = os.path.join("temp", "data", "report.json")
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        couple_key = f"Couple {couple_display_number}"

        if couple_key in data:
            del data[couple_key]

            # Enregistrer le JSON mis à jour
            with open(json_file, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
    except (FileNotFoundError, json.JSONDecodeError):
        # Le fichier JSON n'existe pas ou est invalide ; rien à supprimer
        pass

    # Supprimer les fichiers GeoJSON associés en utilisant le numéro d'affichage
    for section in ['zone', 'points']:
        file_path = os.path.join(
            "temp", "data", f"couple{couple_display_number}_{section}.fgb"
        )
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier {file_path} : {e}")
