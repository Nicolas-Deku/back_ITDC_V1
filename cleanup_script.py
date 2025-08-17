# cleanup_script.py

import sys
import os

# Ajoutez le répertoire parent au PYTHONPATH pour les importations relatives
# Cela permet d'importer des modules de l'application (app.database, app.repositories)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.database import SessionLocal, engine, Base
from app.repositories.user_repository import UserRepository
from app.models import db_models # Assurez-vous que les modèles sont importés pour Base.metadata

def run_cleanup():
    """
    Fonction principale pour exécuter le processus de nettoyage.
    """
    # Assurez-vous que les tables existent avant d'essayer de les nettoyer
    # (utile si ce script est exécuté avant create_db_tables.py)
    Base.metadata.create_all(bind=engine) 

    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user_repo.cleanup_expired_entries()
    except Exception as e:
        print(f"Erreur lors de l'exécution du nettoyage : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Démarrage du script de nettoyage des données expirées...")
    run_cleanup()
    print("Script de nettoyage terminé.")
