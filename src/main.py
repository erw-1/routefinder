import subprocess
import os
import platform

def run_command(command):
    """Exécute une commande shell et arrête si elle échoue."""
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Error: Command '{command}' failed!")
        exit(1)

venv_dir = "venv"

 # Étape 5 : Activer l'environnement virtuel
if platform.system() == "Windows":
    activation_command = f"{venv_dir}\\Scripts\\activate && "
else:
    activation_command = f"source {venv_dir}/bin/activate && "

# Étape 6 : Proposer d'exécuter src/buildApp.py
file_to_execute = os.path.join("src", "dataPickerUI.py")
run_command(f"{activation_command}python {file_to_execute}")
