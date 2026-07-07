import subprocess
from pathlib import Path

# On suppose que le repo Git est à la racine du projet
PROJECT_ROOT = Path(__file__).parent.parent.parent

def commit_and_push(fichiers_generes: list[str], message_commit: str) -> bool:
    """
    Effectue un git add, commit et push pour les fichiers générés.
    
    Args:
        fichiers_generes: Liste des chemins absolus des fichiers générés
        message_commit: Message de commit
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        # S'assurer d'être sur la branche principale et à jour
        subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=str(PROJECT_ROOT),
            check=False, # Si ça rate (ex: pas de réseau), on continue
            capture_output=True
        )

        # Ajouter chaque fichier
        for fichier in fichiers_generes:
            subprocess.run(
                ["git", "add", fichier],
                cwd=str(PROJECT_ROOT),
                check=True,
                capture_output=True
            )
            
        # Commit
        res_commit = subprocess.run(
            ["git", "commit", "-m", message_commit],
            cwd=str(PROJECT_ROOT),
            check=False, # Peut échouer s'il n'y a pas de changements
            capture_output=True
        )
        
        # S'il n'y a rien à commiter, on renvoie True quand même
        if "nothing to commit" in res_commit.stdout.decode("utf-8", errors="ignore"):
            return True

        # Push
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(PROJECT_ROOT),
            check=True,
            capture_output=True
        )
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Erreur Git: {e.stderr.decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"Erreur inattendue Git: {str(e)}")
        return False
