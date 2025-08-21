#!/usr/bin/env python3
"""
Script pour nettoyer le fichier pickle au démarrage
Évite les conflits entre persistance pickle et PostgreSQL
"""

import os
import logging

logger = logging.getLogger(__name__)

def clean_pickle_on_startup():
    """Supprime le fichier pickle au démarrage pour éviter les conflits"""
    try:
        pickle_files = ["bot_data.pickle", "bot_data.pickle.backup"]
        
        for pickle_file in pickle_files:
            if os.path.exists(pickle_file):
                os.remove(pickle_file)
                logger.info(f"🗑️ Fichier pickle supprimé: {pickle_file}")
            else:
                logger.info(f"ℹ️ Fichier pickle absent: {pickle_file}")
        
        logger.info("✅ Nettoyage pickle terminé - Démarrage propre")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage pickle: {e}")
        return False

if __name__ == "__main__":
    clean_pickle_on_startup()
