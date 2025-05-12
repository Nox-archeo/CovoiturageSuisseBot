import os
import sys
from database.db_manager import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initialisation de la base de données...")
    
    # Créer le dossier database s'il n'existe pas
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    try:
        init_db()
        logger.info("Base de données initialisée avec succès!")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
