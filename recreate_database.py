#!/usr/bin/env python3
"""
Script pour recréer la base de données avec le nouveau schéma
"""

import os
import sys
import logging
import shutil
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def backup_existing_db():
    """Crée une sauvegarde de la base de données existante"""
    db_path = '/Users/margaux/CovoiturageSuisse/covoiturage.db'
    
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f'/Users/margaux/CovoiturageSuisse/covoiturage_backup_{timestamp}.db'
        
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"✅ Sauvegarde créée: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            return None
    else:
        logger.info("ℹ️  Aucune base de données existante à sauvegarder")
        return None

def recreate_database():
    """Recrée la base de données avec le nouveau schéma"""
    try:
        # Importer les modèles pour s'assurer qu'ils sont corrects
        from database.models import User, Trip, Booking, Message, Review
        logger.info("✅ Modèles importés avec succès")
        
        # Supprimer l'ancienne base si elle existe
        db_path = '/Users/margaux/CovoiturageSuisse/covoiturage.db'
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info("🗑️  Ancienne base de données supprimée")
        
        # Initialiser la nouvelle base
        from database.db_manager import init_db
        init_db()
        logger.info("✅ Nouvelle base de données créée avec le schéma corrigé")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la recréation: {e}")
        return False

def verify_database_schema():
    """Vérifie que le schéma est correct"""
    try:
        from database import get_db
        from database.models import User, Trip
        
        db = get_db()
        
        # Vérifier les champs User
        user_columns = [col.name for col in User.__table__.columns]
        required_user_fields = ['telegram_id', 'full_name', 'age', 'paypal_email', 'is_driver', 'is_passenger']
        
        for field in required_user_fields:
            if field in user_columns:
                logger.info(f"✅ Champ User.{field} présent")
            else:
                logger.error(f"❌ Champ User.{field} manquant")
                return False
        
        # Vérifier les champs Trip
        trip_columns = [col.name for col in Trip.__table__.columns]
        required_trip_fields = ['departure_city', 'arrival_city', 'seats_available', 'recurring']
        
        for field in required_trip_fields:
            if field in trip_columns:
                logger.info(f"✅ Champ Trip.{field} présent")
            else:
                logger.error(f"❌ Champ Trip.{field} manquant")
                return False
        
        logger.info("✅ Schéma de base de données vérifié avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur de vérification: {e}")
        return False

def main():
    logger.info("🚀 Recréation de la base de données")
    logger.info("=" * 50)
    
    # Étape 1: Sauvegarde
    logger.info("📋 Étape 1: Sauvegarde de l'ancienne base")
    backup_path = backup_existing_db()
    
    # Étape 2: Recréation
    logger.info("\n📋 Étape 2: Recréation de la base avec le nouveau schéma")
    if not recreate_database():
        logger.error("❌ Échec de la recréation")
        return 1
    
    # Étape 3: Vérification
    logger.info("\n📋 Étape 3: Vérification du schéma")
    if not verify_database_schema():
        logger.error("❌ Échec de la vérification")
        return 1
    
    # Résumé
    logger.info("\n" + "=" * 50)
    logger.info("🎉 BASE DE DONNÉES RECRÉÉE AVEC SUCCÈS!")
    logger.info("=" * 50)
    logger.info("✅ Nouveau schéma appliqué")
    logger.info("✅ Tous les champs requis présents")
    
    if backup_path:
        logger.info(f"💾 Sauvegarde disponible: {backup_path}")
    
    logger.info("\n🚀 Le bot est prêt à être démarré!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
