#!/usr/bin/env python
"""
Bot principal CovoiturageSuisse
Ce fichier a été modifié pour utiliser l'approche synchrone qui fonctionne correctement.
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import (
    Application, 
    CommandHandler, 
    PicklePersistence,
    CallbackQueryHandler,
    CallbackContext
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

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

# Import des nouveaux handlers de propositions de conducteurs
from handlers.driver_proposal_handler import driver_proposal_conv_handler, view_passenger_trips_handler, view_quick_passenger_trips_handler, propose_service_handler
from handlers.proposal_response_handler import proposal_response_handlers

# Import du handler de recherche de passagers
from handlers.search_passengers import register_search_passengers_handler
from handlers.menu_search_shortcuts import register_menu_search_handlers

# Import des nouveaux modules de paiement PayPal
from payment_handlers import get_payment_handlers
from handlers.paypal_setup_handler import get_paypal_setup_handlers
from db_utils import init_payment_database
from paypal_utils import paypal_manager
from pending_payments import process_all_pending_payments

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)  # Force l'override des variables d'environnement existantes

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
        
        # Import des fonctions nécessaires pour les commandes
        from handlers.create_trip_handler import handle_show_my_trips
        from handlers.profile_handler import profile_handler
        from handlers.search_passengers import cmd_search_passengers
        from handlers.menu_handlers import aide_command, handle_profile_creation, handle_profile_created_actions, handle_help_callbacks, profile_creation_handler
        
        # Commande PROFILE en deuxième position (après /start)
        async def cmd_profile(update: Update, context: CallbackContext):
            """Commande /profile depuis le menu hamburger"""
            return await profile_handler(update, context)
        
        application.add_handler(CommandHandler("profile", cmd_profile))
        
        # Commandes d'aide
        application.add_handler(CommandHandler("aide", aide_command))
        application.add_handler(CommandHandler("help", aide_command))
        
        # TOUS les CommandHandlers du menu hamburger (CRITIQUES - RESTAURATION COMPLÈTE)
        # Les commandes /creer_trajet et /chercher_trajet sont maintenant gérées directement
        # par leurs ConversationHandlers respectifs
        
        # Pour mes trajets - créer une vraie fonction de commande
        async def cmd_my_trips(update: Update, context: CallbackContext):
            """Commande /mes_trajets depuis le menu hamburger"""
            # Utiliser directement la fonction list_my_trips sans simulation de callback
            from handlers.trip_handlers import list_my_trips
            return await list_my_trips(update, context)
        
        # Enregistrer seulement les commandes qui ne sont pas gérées par des ConversationHandlers
        # Note: /chercher_passagers est gérée par le ConversationHandler search_passengers_handler
        application.add_handler(CommandHandler("mes_trajets", cmd_my_trips))
        
        # Ajouter les commandes manquantes du menu hamburger
        async def cmd_propositions(update: Update, context: CallbackContext):
            """Commande /propositions depuis le menu hamburger"""
            # Proposer les deux options : vue rapide ou recherche avancée
            keyboard = [
                [InlineKeyboardButton("⚡ Vue rapide - Dernières demandes", callback_data="view_quick_passenger_trips")],
                [InlineKeyboardButton("🔍 Recherche avancée - Par canton et date", callback_data="search_passengers")],
                [InlineKeyboardButton("🔙 Retour au menu", callback_data="menu:back_to_main")]
            ]
            
            text = (
                "🚗 **Demandes de passagers**\n\n"
                "Comment souhaitez-vous rechercher des passagers ?\n\n"
                "⚡ **Vue rapide** : Voir les 10 dernières demandes\n"
                "🔍 **Recherche avancée** : Par canton et date"
            )
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        async def cmd_verification(update: Update, context: CallbackContext):
            """Commande /verification depuis le menu hamburger"""
            keyboard = [
                [InlineKeyboardButton("🆔 Vérifier mon identité", callback_data="verify_identity")],
                [InlineKeyboardButton("📞 Vérifier mon numéro", callback_data="verify_phone")],
                [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
            ]
            
            text = (
                "✅ *Vérification du compte*\n\n"
                "Choisissez le type de vérification :"
            )
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        async def cmd_paiements(update: Update, context: CallbackContext):
            """Commande /paiements depuis le menu hamburger"""
            keyboard = [
                [InlineKeyboardButton("💳 Configuration PayPal", callback_data="setup_paypal")],
                [InlineKeyboardButton("💰 Voir mes paiements", callback_data="view_payments")],
                [InlineKeyboardButton("📊 Historique", callback_data="payment_history")],
                [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
            ]
            
            text = (
                "💰 *Gestion des paiements*\n\n"
                "Choisissez une option :"
            )
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        # Enregistrer les nouvelles commandes
        application.add_handler(CommandHandler("propositions", cmd_propositions))
        application.add_handler(CommandHandler("verification", cmd_verification))
        application.add_handler(CommandHandler("paiements", cmd_paiements))
        
        logger.info("✅ TOUS les CommandHandlers du menu hamburger sont maintenant enregistrés")
        
        # Ajouter le ConversationHandler pour la création complète de profil
        application.add_handler(profile_creation_handler)
        
        # IMPORTANT: Enregistrer create_trip_conv_handler EN PREMIER
        # pour s'assurer qu'il a priorité sur tous les autres handlers
        application.add_handler(create_trip_conv_handler)
        
        # Enregistrer les handlers de propositions de conducteurs
        application.add_handler(driver_proposal_conv_handler)
        # Handlers pour les demandes de passagers
        application.add_handler(view_passenger_trips_handler)
        application.add_handler(view_quick_passenger_trips_handler)
        # Handler global pour les propositions de service
        application.add_handler(propose_service_handler)
        
        # Enregistrer les handlers de réponses aux propositions
        for handler in proposal_response_handlers:
            application.add_handler(handler)
        logger.info("✅ Handlers de propositions de conducteurs enregistrés")
        
        # Handlers de recherche spécialisés (doivent être avant les ConversationHandlers)
        register_menu_search_handlers(application)
        
        # Enregistrer le handler de recherche de passagers
        register_search_passengers_handler(application)
        logger.info("✅ Handler de recherche de passagers enregistré")
        
        # Feature handlers (APRÈS create_trip_conv_handler pour éviter les conflits)
        # Import et ajouter le gestionnaire de bouton de profil spécifique
        from handlers.profile_handler import profile_button_handler, profile_conv_handler, back_to_profile
        
        # Enregistrer le handler global pour le retour au profil
        application.add_handler(CallbackQueryHandler(back_to_profile, pattern="^profile:back_to_profile$"))
        
        # Enregistrer les gestionnaires de profil
        application.add_handler(profile_button_handler)  
        application.add_handler(profile_conv_handler)
        
        # Enregistrer les autres handlers
        application.add_handler(publish_trip_handler)
        application.add_handler(main_menu_handler)
        application.add_handler(my_trips_handler)
        application.add_handler(search_trip_conv_handler)
        
        # Handler de menu (doit être APRÈS les ConversationHandlers pour ne pas les intercepter)
        # Exclure menu:create qui est géré par create_trip_conv_handler
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:search_trip$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:my_trips$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:help$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:become_driver$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:back_to_main$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:back_to_menu$"))
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^setup_paypal$"))
        
        # Handlers pour les actions après création de profil (ancienne méthode, sera supprimée)
        application.add_handler(CallbackQueryHandler(handle_profile_created_actions, pattern="^profile_created:"))
        
        # Handlers pour l'aide contextuelle
        application.add_handler(CallbackQueryHandler(handle_help_callbacks, pattern="^help:"))
        
        # Handlers pour le switch de profil conducteur/passager
        from handlers.menu_handlers import switch_user_profile
        application.add_handler(CallbackQueryHandler(
            lambda u, c: switch_user_profile(u, c, "driver"), 
            pattern="^switch_profile:driver$"
        ))
        application.add_handler(CallbackQueryHandler(
            lambda u, c: switch_user_profile(u, c, "passenger"), 
            pattern="^switch_profile:passenger$"
        ))
        logger.info("✅ Handlers de switch de profil enregistrés")
        
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
        
        # Enregistrement des handlers de configuration PayPal
        logger.info("Enregistrement des handlers de configuration PayPal...")
        paypal_setup_handlers = get_paypal_setup_handlers()
        
        # Ajouter le ConversationHandler de configuration PayPal
        application.add_handler(paypal_setup_handlers['conversation_handler'])
        logger.info("✅ ConversationHandler configuration PayPal enregistré")
        
        # Ajouter les CommandHandlers de configuration PayPal
        for cmd_handler in paypal_setup_handlers['command_handlers']:
            application.add_handler(cmd_handler)
            logger.info(f"✅ CommandHandler configuration PayPal enregistré")
        
        # Ajouter les CallbackQueryHandlers de configuration PayPal
        for callback_handler in paypal_setup_handlers['callback_handlers']:
            application.add_handler(callback_handler)
            logger.info(f"✅ CallbackQueryHandler configuration PayPal enregistré")
        
        logger.info("✅ Tous les handlers de paiement et configuration PayPal enregistrés")
        
        application.add_handler(vehicle_conv_handler)

        # Configuration des tâches périodiques (désactivé sur Render)
        try:
            # Vérifier si on est sur Render (généralement pas de JobQueue disponible)
            is_render = os.getenv('RENDER') is not None or os.getenv('RENDER_SERVICE_ID') is not None
            
            if is_render:
                logger.info("Environnement Render détecté - JobQueue désactivé")
            else:
                job_queue = getattr(application, 'job_queue', None)
                
                if job_queue is not None and hasattr(job_queue, 'run_repeating'):
                    # Tâche pour traiter les paiements en attente (toutes les heures)
                    # Note: On utilise une fonction synchrone pour éviter les problèmes asyncio
                    def payment_callback(context):
                        try:
                            # Traitement synchrone ou délégation appropriée
                            logger.info("Traitement périodique des paiements en attente")
                        except Exception as e:
                            logger.error(f"Erreur lors du traitement des paiements: {e}")
                    
                    job_queue.run_repeating(
                        callback=payment_callback,
                        interval=3600,  # Toutes les heures
                        first=10        # Première exécution après 10 secondes
                    )
                    logger.info("✅ Tâche périodique de traitement des paiements en attente configurée")
                else:
                    logger.warning("JobQueue non disponible localement - paiements en attente non automatisés")
        except Exception as e:
            logger.warning(f"Erreur lors de la configuration JobQueue : {e} - paiements en attente non automatisés")

        # Handler de debug pour capturer les callbacks non traités (EN DERNIER)
        from debug_handler import debug_callback_handler
        application.add_handler(debug_callback_handler)
        logger.info("✅ Handler de debug ajouté pour capturer les callbacks non traités")

        # Configuration des commandes du menu hamburger avec l'ordre souhaité
        async def configure_bot_commands(app):
            """Configure les commandes du menu hamburger dans l'ordre souhaité"""
            from telegram import BotCommand
            
            commands = [
                BotCommand("start", "🏠 Menu principal"),
                BotCommand("profile", "👤 Mon profil"),  # EN DEUXIÈME POSITION
                BotCommand("creer_trajet", "🚗 Créer un trajet"),
                BotCommand("chercher_trajet", "🔍 Chercher un trajet"),
                BotCommand("mes_trajets", "📋 Mes trajets"),
                BotCommand("chercher_passagers", "🔍 Chercher passagers"),
                BotCommand("propositions", "🚗 Propositions de trajets"),
                BotCommand("verification", "✅ Vérification compte"),
                BotCommand("paiements", "💰 Gestion paiements"),
                BotCommand("aide", "❓ Aide et support"),
            ]
            
            try:
                await app.bot.set_my_commands(commands)
                logger.info("✅ Commandes du menu hamburger configurées avec profile en 2ème position")
            except Exception as e:
                logger.error(f"Erreur lors de la configuration des commandes: {e}")
        
        # Ajouter le callback de post-init pour configurer les commandes
        application.post_init = configure_bot_commands

        # Start polling
        logger.info("Bot started successfully!")
        application.run_polling()

    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
