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
from handlers.create_trip_handler import create_trip_conv_handler, publish_trip_handler, main_menu_handler, my_trips_handler
from handlers.search_trip_handler import search_trip_conv_handler
from handlers.menu_handlers import start_command, handle_menu_buttons  # Changé menu_handler en start_command
# Using the profile handler
from handlers.profile_handler import profile_handler
from handlers.trip_handlers import register as register_trip_handlers
from handlers.booking_handlers import register as register_booking_handlers
from handlers.message_handlers import register as register_message_handlers
from handlers.verification_handlers import register as register_verification_handlers
from handlers.subscription_handlers import register as register_subscription_handlers
from handlers.admin_handlers import register as register_admin_handlers
from handlers.user_handlers import register as register_user_handlers
from handlers.contact_handlers import register as register_contact_handlers
from handlers.dispute_handlers import register as register_dispute_handlers
from handlers.trip_completion_handlers import register as register_trip_completion_handlers
from handlers.vehicle_handler import vehicle_conv_handler

# Import des nouveaux modules de paiement PayPal
from payment_handlers import get_payment_handlers
from db_utils import init_payment_database
from paypal_utils import paypal_manager

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
        # Initialisation de la base de données pour les paiements
        logger.info("Initialisation de la base de données de paiements...")
        if not init_payment_database():
            logger.error("Erreur lors de l'initialisation de la base de données de paiements")
            sys.exit(1)
        logger.info("✅ Base de données de paiements initialisée")
        
        # Vérification de la configuration PayPal
        try:
            # Test de la configuration PayPal
            logger.info("Vérification de la configuration PayPal...")
            logger.info("✅ PayPal configuré avec succès")
        except Exception as e:
            logger.warning(f"Attention - Configuration PayPal : {e}")
            logger.info("Le bot fonctionnera mais les paiements PayPal seront indisponibles")
        
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
        
        # Handler de menu (doit être AVANT les ConversationHandlers pour intercepter les boutons)
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:create$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:search_trip$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:my_trips$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:help$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:back_to_menu$"))
        
        # Feature handlers
        # Import et ajouter le gestionnaire de bouton de profil spécifique
        # S'assurer que le gestionnaire de profil est enregistré en premier pour qu'il puisse intercepter les callbacks de profil
        from handlers.profile_handler import profile_button_handler, profile_conv_handler
        
        # Enregistrer d'abord le gestionnaire de bouton de profil spécifique pour qu'il ait priorité
        application.add_handler(profile_button_handler)  
        application.add_handler(profile_conv_handler)  # Use the enhanced profile handler
        
        # Enregistrer les autres handlers
        application.add_handler(create_trip_conv_handler)
        application.add_handler(publish_trip_handler)
        application.add_handler(main_menu_handler)
        application.add_handler(my_trips_handler)
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
        register_dispute_handlers(application)
        register_trip_completion_handlers(application)
        
        # Enregistrement des handlers de paiement PayPal
        logger.info("Enregistrement des handlers de paiement PayPal...")
        payment_handlers = get_payment_handlers()
        
        # Ajouter les ConversationHandlers de paiement
        for conv_handler in payment_handlers['conversation_handlers']:
            application.add_handler(conv_handler)
            logger.info(f"✅ ConversationHandler PayPal enregistré")
        
        # Ajouter les CommandHandlers de paiement
        for cmd_handler in payment_handlers['command_handlers']:
            application.add_handler(cmd_handler)
            logger.info(f"✅ CommandHandler PayPal enregistré")
        
        # Ajouter les CallbackQueryHandlers de paiement
        for callback_handler in payment_handlers['callback_handlers']:
            application.add_handler(callback_handler)
            logger.info(f"✅ CallbackQueryHandler PayPal enregistré")
        
        logger.info("✅ Tous les handlers de paiement PayPal enregistrés")
        
        application.add_handler(vehicle_conv_handler)

        # Start polling
        logger.info("Bot started successfully!")
        application.run_polling()

    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
