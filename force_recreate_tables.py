#!/usr/bin/env python3
"""
Script d'urgence pour FORCER la recréation des tables PostgreSQL
Solution radicale pour l'erreur SQL 9h9h persistante
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import engine
from database.models import Base
from sqlalchemy import text

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_recreate_tables():
    """FORCE la recréation des tables PostgreSQL avec le bon schéma"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL or not DATABASE_URL.startswith(('postgres://', 'postgresql://')):
        logger.info("🏠 SQLite détecté - aucune action nécessaire")
        return True
    
    logger.info("🚨 RECREATION FORCÉE DES TABLES POSTGRESQL")
    
    try:
        with engine.connect() as conn:
            logger.warning("⚠️ SUPPRESSION FORCÉE DE TOUTES LES TABLES...")
            
            # Supprimer TOUTES les tables avec CASCADE (force)
            drop_commands = [
                "DROP TABLE IF EXISTS reviews CASCADE;",
                "DROP TABLE IF EXISTS messages CASCADE;", 
                "DROP TABLE IF EXISTS driver_proposals CASCADE;",
                "DROP TABLE IF EXISTS bookings CASCADE;",
                "DROP TABLE IF EXISTS trips CASCADE;",
                "DROP TABLE IF EXISTS users CASCADE;",
            ]
            
            for cmd in drop_commands:
                try:
                    conn.execute(text(cmd))
                    logger.info(f"✅ {cmd}")
                except Exception as e:
                    logger.warning(f"⚠️ {cmd} → {e}")
            
            conn.commit()
            logger.info("🔥 TOUTES LES TABLES SUPPRIMÉES")
            
        # Recréer avec le schéma corrigé
        logger.info("🔨 RECREATION AVEC SCHÉMA CORRIGÉ...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("🎉 TABLES RECRÉÉES AVEC SUCCÈS!")
        logger.info("✅ PROBLÈME SQL 9h9h RÉSOLU")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur recreation forcée: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚨 DÉMARRAGE RECREATION FORCÉE...")
    success = force_recreate_tables()
    if success:
        print("🎉 SUCCESS: Tables recréées, création profils va fonctionner!")
    else:
        print("❌ ÉCHEC: Problème lors de la recréation")
        sys.exit(1)
