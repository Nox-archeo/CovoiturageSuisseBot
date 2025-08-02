#!/usr/bin/env python3
"""
Migration PostgreSQL simplifiée et rapide
Correction du schéma sans bloquer le serveur
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import engine
from sqlalchemy import text

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_postgresql_fix():
    """Correction rapide et ciblée pour PostgreSQL"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL or not DATABASE_URL.startswith(('postgres://', 'postgresql://')):
        logger.info("🏠 SQLite détecté - aucune correction nécessaire")
        return True
    
    logger.info("🔧 CORRECTION RAPIDE POSTGRESQL...")
    
    try:
        with engine.connect() as conn:
            # Corrections essentielles uniquement (rapides)
            essential_fixes = [
                # Nettoyer les chaînes vides qui causent l'erreur
                "UPDATE users SET paypal_email = NULL WHERE paypal_email = '';",
                "UPDATE users SET car_model = NULL WHERE car_model = '';",
                "UPDATE users SET username = NULL WHERE username = '';",
                "UPDATE users SET license_plate = NULL WHERE license_plate = '';",
                "UPDATE users SET gender = NULL WHERE gender = '';",
                "UPDATE users SET full_name = NULL WHERE full_name = '';",
            ]
            
            for fix in essential_fixes:
                try:
                    result = conn.execute(text(fix))
                    logger.info(f"✅ {fix[:30]}... → {result.rowcount} lignes modifiées")
                except Exception as e:
                    logger.warning(f"⚠️ {fix[:30]}... → Ignoré: {str(e)[:50]}")
            
            conn.commit()
            logger.info("🎉 CORRECTION RAPIDE TERMINÉE - Création profils devrait fonctionner")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur correction rapide: {e}")
        return False

if __name__ == "__main__":
    success = quick_postgresql_fix()
    if success:
        print("✅ Migration rapide réussie")
    else:
        print("❌ Migration rapide échouée")
        sys.exit(1)
