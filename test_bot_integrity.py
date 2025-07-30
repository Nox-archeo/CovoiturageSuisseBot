#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégrité du bot après les corrections
"""

import sys
import os
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_imports():
    """Teste tous les imports critiques"""
    logger.info("🔍 Test des imports...")
    
    try:
        # Test des modèles
        from database.models import User, Trip, Booking
        logger.info("✅ Modèles importés avec succès")
        
        # Test des handlers
        from handlers.menu_handlers import start_command, profile_creation_handler
        from handlers.create_trip_handler import create_trip_conv_handler
        from handlers.profile_handler import profile_button_handler
        logger.info("✅ Handlers importés avec succès")
        
        # Test des utilitaires
        from utils.group_trips import generate_group_id
        logger.info("✅ Utilitaires importés avec succès")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur d'import: {e}")
        return False

def test_database_models():
    """Teste la cohérence des modèles de base de données"""
    logger.info("🔍 Test des modèles de base de données...")
    
    try:
        from database.models import User, Trip
        
        # Vérifier les champs User
        user_fields = ['telegram_id', 'full_name', 'age', 'paypal_email', 'is_driver', 'is_passenger']
        user_obj = User.__table__.columns
        
        for field in user_fields:
            if field not in [col.name for col in user_obj]:
                logger.error(f"❌ Champ manquant dans User: {field}")
                return False
                
        logger.info("✅ Modèle User correct")
        
        # Vérifier les champs Trip
        trip_fields = ['departure_city', 'arrival_city', 'seats_available', 'recurring']
        trip_obj = Trip.__table__.columns
        
        for field in trip_fields:
            if field not in [col.name for col in trip_obj]:
                logger.error(f"❌ Champ manquant dans Trip: {field}")
                return False
                
        logger.info("✅ Modèle Trip correct")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur de modèles: {e}")
        return False

def test_database_connection():
    """Teste la connexion à la base de données"""
    logger.info("🔍 Test de la connexion à la base de données...")
    
    try:
        from database import get_db
        from database.models import User
        
        db = get_db()
        # Test simple de requête
        user_count = db.query(User).count()
        logger.info(f"✅ Base de données accessible - {user_count} utilisateurs")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur de base de données: {e}")
        return False

def test_handlers_configuration():
    """Teste la configuration des handlers"""
    logger.info("🔍 Test de la configuration des handlers...")
    
    try:
        from telegram.ext import Application
        from handlers.create_trip_handler import create_trip_conv_handler
        from handlers.menu_handlers import profile_creation_handler
        
        # Créer une application test
        app = Application.builder().token("test").build()
        
        # Tester l'ajout des handlers
        app.add_handler(create_trip_conv_handler)
        app.add_handler(profile_creation_handler)
        
        logger.info("✅ Handlers configurés avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur de configuration handlers: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Début des tests d'intégrité du bot")
    logger.info("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Modèles de base de données", test_database_models),
        ("Connexion base de données", test_database_connection),
        ("Configuration handlers", test_handlers_configuration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Test: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: RÉUSSI")
            else:
                logger.error(f"❌ {test_name}: ÉCHOUÉ")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERREUR CRITIQUE - {e}")
            results.append((test_name, False))
    
    # Résumé
    logger.info("\n" + "=" * 50)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        logger.info("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        logger.info("Le bot est prêt à fonctionner.")
        return 0
    else:
        logger.error("⚠️  CERTAINS TESTS ONT ÉCHOUÉ!")
        logger.error("Veuillez corriger les erreurs avant de démarrer le bot.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
