import subprocess

def list_pip_packages():
    """Liste les paquets installés via pip et attend une confirmation pour quitter."""
    try:
        print("Liste des paquets installés (pip list) :\n")
        # Exécuter la commande `pip list` et afficher le résultat
        result = subprocess.run(["pip", "list"], text=True, capture_output=True)
        print(result.stdout)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    finally:
        # Attendre que l'utilisateur appuie sur Entrée
        input("\nAppuyez sur 'Entrée' pour quitter...")

if __name__ == "__main__":
    list_pip_packages()
