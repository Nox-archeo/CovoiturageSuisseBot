#!/usr/bin/env python3
"""
Script d'urgence pour recréer les tables PostgreSQL avec le bon schéma
À utiliser si la migration normale échoue
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

def recreate_postgresql_tables():
    """Recrée toutes les tables avec le schéma corrigé"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL or not DATABASE_URL.startswith(('postgres://', 'postgresql://')):
        logger.info("🏠 SQLite détecté - aucune action nécessaire")
        return
    
    logger.info("🚨 RECREATION URGENTE DES TABLES POSTGRESQL")
    
    try:
        with engine.connect() as conn:
            # ATTENTION: Supprime toutes les données existantes
            logger.warning("⚠️ SUPPRESSION DE TOUTES LES DONNÉES...")
            
            # Supprimer toutes les tables dans l'ordre inverse des dépendances
            drop_commands = [
                "DROP TABLE IF EXISTS reviews CASCADE",
                "DROP TABLE IF EXISTS messages CASCADE", 
                "DROP TABLE IF EXISTS driver_proposals CASCADE",
                "DROP TABLE IF EXISTS bookings CASCADE",
                "DROP TABLE IF EXISTS trips CASCADE",
                "DROP TABLE IF EXISTS users CASCADE",
            ]
            
            for cmd in drop_commands:
                try:
                    conn.execute(text(cmd))
                    logger.info(f"✅ Table supprimée: {cmd}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur suppression (ignorée): {e}")
            
            conn.commit()
            
            # Recréer avec le bon schéma
            logger.info("🔨 RECREATION AVEC BON SCHEMA...")
            Base.metadata.create_all(bind=engine)
            
            logger.info("🎉 Tables recréées avec succès!")
            logger.warning("⚠️ TOUTES LES DONNÉES ONT ÉTÉ PERDUES")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la recréation: {e}")
        raise

if __name__ == "__main__":
    response = input("⚠️ ATTENTION: Ceci va SUPPRIMER TOUTES LES DONNÉES. Continuer? (oui/non): ")
    if response.lower() == 'oui':
        recreate_postgresql_tables()
    else:
        print("❌ Opération annulée")
