#!/usr/bin/env python
"""
Bot principal CovoiturageSuisse
Ce fichier a été modifié pour utiliser l'approche synchrone qui fonctionne correctement.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from telegram.ext import (
    Application, 
    CommandHandler, 
    PicklePersistence,
    CallbackQueryHandler
)

# Import handlers (correction des imports)
from handlers.create_trip_handler import create_trip_conv_handler, publish_trip_handler
from handlers.search_trip_handler import search_trip_conv_handler
from handlers.menu_handlers import start_command, handle_menu_buttons  # Changé menu_handler en start_command
from handlers.profile_handlers import profile_conv_handler
from handlers.trip_handlers import register as register_trip_handlers
from handlers.booking_handlers import register as register_booking_handlers
from handlers.message_handlers import register as register_message_handlers
from handlers.verification_handlers import register as register_verification_handlers
from handlers.subscription_handlers import register as register_subscription_handlers
from handlers.admin_handlers import register as register_admin_handlers
from handlers.user_handlers import register as register_user_handlers
from handlers.contact_handlers import register as register_contact_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main function to start the bot"""
    try:
        # Récupérer le token depuis .env
        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not BOT_TOKEN:
            raise ValueError("Token non trouvé dans le fichier .env")
        
        # Initialize persistence
        persistence = PicklePersistence(filepath="bot_data.pickle")
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()

        # Add handlers in correct order
        logger.info("Registering handlers...")
        
        # Core handlers
        application.add_handler(CommandHandler("start", start_command))  # Utiliser start_command au lieu de menu_handler
        
        # Feature handlers
        application.add_handler(profile_conv_handler)
        application.add_handler(create_trip_conv_handler)
        application.add_handler(publish_trip_handler)
        application.add_handler(search_trip_conv_handler)
        
        # Register other handlers using their register functions
        register_trip_handlers(application)
        register_booking_handlers(application)
        register_message_handlers(application)
        register_verification_handlers(application)
        register_subscription_handlers(application)
        register_admin_handlers(application)
        register_user_handlers(application)
        register_contact_handlers(application)
        
        # Add general button handler last
        application.add_handler(CallbackQueryHandler(handle_menu_buttons))

        # Start polling
        logger.info("Bot started successfully!")
        application.run_polling()

    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
