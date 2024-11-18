import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import logging
import shutil

def generate_web_page(json_path):
    """
    Génère une page web à partir des données d'un fichier JSON donné.

    Args:
        json_path (str): Chemin vers le fichier JSON.

    Returns:
        str: Chemin vers le fichier HTML généré.
    """
    # Configuration du journal (logging)
    logger = logging.getLogger("generate_web_page")
    logger.setLevel(logging.DEBUG)  # Capture tous les niveaux de logs

    # Évite d'ajouter plusieurs gestionnaires si la fonction est appelée plusieurs fois
    if not logger.handlers:
        handler = logging.StreamHandler()  # Journalisation vers la console
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.info("Démarrage de la génération de la page web.")
    logger.debug(f"Chemin du JSON fourni : {json_path}")

    # Vérifie si le fichier JSON existe
    if not os.path.isfile(json_path):
        logger.error(f"Le fichier JSON n'existe pas au chemin : {json_path}")
        raise FileNotFoundError(f"Fichier JSON non trouvé : {json_path}")

    # Chargement des données JSON
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        logger.info("Données JSON chargées avec succès.")
    except json.JSONDecodeError as e:
        logger.error(f"Erreur lors du décodage du fichier JSON : {e}")
        raise

    # Préparation des options pour le menu déroulant
    dropdown_options = []
    for couple_key, couple_data in report.items():
        try:
            option = {
                "value": couple_key,
                "text": f"{couple_data['Zone']['name']} - {couple_data['Points']['name']}",
                "zone_source": couple_data["Zone"]["source"],
                "points_source": couple_data["Points"]["source"],
            }
            dropdown_options.append(option)
        except KeyError as e:
            logger.error(f"Clé manquante dans les données JSON : {e} dans l'ensemble {couple_key}")
            continue
    logger.debug(f"Options du menu déroulant préparées : {dropdown_options}")

    # Définition du répertoire des templates
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Répertoire où se trouve le script
    template_dir = os.path.join(script_dir, 'template')
    logger.debug(f"Répertoire des templates défini sur : {template_dir}")

    # Vérifie si le répertoire des templates existe
    if not os.path.isdir(template_dir):
        logger.error(f"Le répertoire des templates n'existe pas : {template_dir}")
        raise FileNotFoundError(f"Répertoire des templates non trouvé : {template_dir}")

    # Création d'un environnement Jinja2 et chargement des templates
    try:
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('index.html')
        logger.info("Template HTML chargé avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors du chargement du template HTML : {e}")
        raise

    # Rendu du template avec les options du menu déroulant
    try:
        html_content = template.render(options=dropdown_options)
        logger.info("Template rendu avec succès avec les options fournies.")
    except Exception as e:
        logger.error(f"Erreur lors du rendu du template : {e}")
        raise

    # Définition du répertoire et du fichier de sortie
    # Remplace les antislashs par des slashs pour la compatibilité multiplateforme
    json_path_normalized = json_path.replace("\\", "/")
    # Supprime '/data' du chemin pour obtenir le répertoire d'exportation
    output_dir = os.path.dirname(json_path_normalized.replace("/data", ""))
    output_dir = os.path.abspath(output_dir)  # Obtient le chemin absolu
    logger.debug(f"Répertoire de sortie déterminé comme : {output_dir}")

    # S'assure que le répertoire de sortie existe
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Répertoire de sortie créé : {output_dir}")
        except Exception as e:
            logger.error(f"Échec de la création du répertoire de sortie : {e}")
            raise

    # Copie les fichiers statiques dans le répertoire de sortie
    static_src = os.path.join(script_dir, 'static')
    static_dst = os.path.join(output_dir, 'static')
    if os.path.isdir(static_src):
        try:
            if os.path.exists(static_dst):
                logger.debug(f"Le répertoire de destination statique existe déjà : {static_dst}. Suppression en cours.")
                shutil.rmtree(static_dst)
            shutil.copytree(static_src, static_dst)
            logger.info(f"Fichiers statiques copiés de {static_src} vers {static_dst}.")
        except Exception as e:
            logger.error(f"Erreur lors de la copie des fichiers statiques : {e}")
            raise
    else:
        logger.error(f"Le répertoire source des fichiers statiques n'existe pas : {static_src}")
        raise FileNotFoundError(f"Répertoire source des fichiers statiques non trouvé : {static_src}")

    # Définition du chemin du fichier HTML de sortie
    output_file = os.path.join(output_dir, "index.html")
    logger.debug(f"Chemin du fichier HTML de sortie : {output_file}")

    # Sauvegarde du contenu HTML rendu dans le fichier de sortie
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Page HTML sauvegardée avec succès à : {output_file}")
    except Exception as e:
        logger.error(f"Erreur lors de l'écriture du fichier HTML : {e}")
        raise

    return output_file

# Exemple d'utilisation :
if __name__ == "__main__":
    # Remplacez 'chemin/vers/votre_fichier.json' par le chemin réel de votre fichier JSON
    chemin_json = 'chemin/vers/votre_fichier.json'
    try:
        output = generate_web_page(chemin_json)
        print(f"Page web générée à : {output}")
    except Exception as e:
        print(f"Une erreur est survenue lors de la génération de la page web : {e}")
