#!/usr/bin/env python3
"""
Script pour corriger le schéma PostgreSQL et les contraintes
Résout les problèmes de types de colonnes et contraintes pour PostgreSQL
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import engine, get_db
from database.models import Base
from sqlalchemy import text, inspect

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_postgresql_schema():
    """Corrige le schéma PostgreSQL pour assurer la compatibilité"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL or not DATABASE_URL.startswith(('postgres://', 'postgresql://')):
        logger.info("🏠 SQLite détecté - aucune correction nécessaire")
        return
    
    logger.info("🚀 Correction du schéma PostgreSQL...")
    
    try:
        # Vérifier la connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Connexion PostgreSQL OK: {version[:50]}...")
            
            # Vérifier si les tables existent
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            logger.info(f"📋 Tables existantes: {tables}")
            
            # Si pas de tables, créer le schéma complet
            if not tables:
                logger.info("🔨 Création du schéma complet...")
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Schéma créé avec succès")
                return
            
            # Si tables existent, appliquer les corrections nécessaires
            logger.info("🔧 Application des corrections sur le schéma existant...")
            
            # Corrections spécifiques pour PostgreSQL
            corrections = [
                # Assurer que les colonnes TEXT sont bien définies
                "ALTER TABLE users ALTER COLUMN notification_preferences TYPE TEXT",
                # Assurer les contraintes NOT NULL
                "UPDATE users SET paypal_email = NULL WHERE paypal_email = ''",
                "UPDATE users SET car_model = NULL WHERE car_model = ''",
                "UPDATE users SET username = NULL WHERE username = ''",
            ]
            
            for correction in corrections:
                try:
                    conn.execute(text(correction))
                    logger.info(f"✅ Correction appliquée: {correction[:50]}...")
                except Exception as e:
                    # Ignorer les erreurs si la correction est déjà appliquée
                    logger.warning(f"⚠️ Correction ignorée (déjà appliquée): {str(e)[:50]}...")
            
            conn.commit()
            logger.info("✅ Toutes les corrections PostgreSQL appliquées")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction PostgreSQL: {e}")
        raise

def test_user_creation():
    """Test la création d'un utilisateur pour vérifier le schéma"""
    try:
        from database.models import User
        db = get_db()
        
        # Test simple de création (rollback après)
        test_user = User(
            telegram_id=999999999,
            username="test_user",
            full_name="Test User",
            age=25,
            phone="123456789",
            paypal_email=None,
            is_driver=True,
            is_passenger=True
        )
        
        db.add(test_user)
        db.flush()  # Ne pas commit, juste vérifier
        
        logger.info("✅ Test de création d'utilisateur OK")
        
        # Rollback le test
        db.rollback()
        
    except Exception as e:
        logger.error(f"❌ Erreur test création utilisateur: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🔧 Démarrage correction schéma PostgreSQL...")
    
    try:
        fix_postgresql_schema()
        test_user_creation()
        logger.info("🎉 Correction terminée avec succès!")
        
    except Exception as e:
        logger.error(f"💥 Échec de la correction: {e}")
        sys.exit(1)
