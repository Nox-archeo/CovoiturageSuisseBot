import json
import os
import logging

logger = logging.getLogger(__name__)

def update_cities():
    """Met à jour le fichier cities.json avec les données validées"""
    try:
        # Vérifie que le chemin existe
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Création du dossier {output_dir}")
            
        output_file = os.path.join(output_dir, 'cities.json')
        logger.info(f"Mise à jour du fichier {output_file}")
        
        # ...existing code...
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_cities()