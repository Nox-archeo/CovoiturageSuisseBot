#!/usr/bin/env python3
"""
Script de démarrage simplifié pour tester le bot
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("🚀 Démarrage du test bot...")
        
        # Charger les variables d'environnement
        load_dotenv()
        
        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not BOT_TOKEN:
            logger.error("❌ Token Telegram non trouvé dans .env")
            return 1
            
        logger.info("✅ Token Telegram trouvé")
        
        # Test des imports critiques
        try:
            from database.models import User, Trip, Booking
            logger.info("✅ Modèles importés")
            
            from handlers.menu_handlers import start_command, profile_creation_handler
            logger.info("✅ Menu handlers importés")
            
            from handlers.create_trip_handler import create_trip_conv_handler
            logger.info("✅ Create trip handler importé")
            
            from telegram.ext import Application
            logger.info("✅ Telegram API importée")
            
        except Exception as e:
            logger.error(f"❌ Erreur d'import: {e}")
            return 1
        
        # Test de création d'application
        try:
            app = Application.builder().token(BOT_TOKEN).build()
            logger.info("✅ Application Telegram créée")
            
            # Test d'ajout des handlers
            app.add_handler(profile_creation_handler)
            app.add_handler(create_trip_conv_handler)
            logger.info("✅ Handlers ajoutés avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur de configuration: {e}")
            return 1
        
        logger.info("🎉 Le bot est correctement configuré!")
        logger.info("Vous pouvez maintenant démarrer le bot avec: python bot.py")
        
        return 0
        
    except Exception as e:
        logger.error(f"💥 Erreur critique: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
