import os
import subprocess
import platform
import sys

def run_command(command):
    """Exécute une commande shell et arrête si elle échoue."""
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Error: Command '{command}' failed!")
        exit(1)

# Étape 1 : Changer le répertoire courant pour simuler une exécution depuis le répertoire parent
script_dir = os.path.abspath(os.path.dirname(__file__))  # Chemin absolu vers le fichier actuel
root_dir = os.path.dirname(script_dir)  # Supposons que 'routefinder' est le dossier parent
os.chdir(root_dir)  # Change le répertoire courant pour le dossier parent

# Étape 2 : Définir les chemins pour venv et le script à exécuter
venv_dir = os.path.join(root_dir, "venv")
file_to_execute = os.path.join("src", "dataPickerUI.py")  # Chemin relatif depuis le nouveau répertoire courant

# Étape 3 : Activer l'environnement virtuel
print("\nActivation de l'environnement virtuel...")
if platform.system() == "Windows":
    activation_command = f"{os.path.join(venv_dir, 'Scripts', 'activate')} && "
else:
    activation_command = f"source {os.path.join(venv_dir, 'bin', 'activate')} && "

# Étape 4 : Exécuter directement le script principal
if os.path.exists(file_to_execute):
    print(f"\nApplication lancée\n")
    run_command(f"{activation_command}python {file_to_execute}")
    
else:
    print(f"Le fichier '{file_to_execute}' est introuvable.")
