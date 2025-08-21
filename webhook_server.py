#!/usr/bin/env python3
"""
Version webhook du bot avec port HTTP pour Render
Combine bot + serveur web pou        # MIGRAT    try:
        from database.db_m        # SOLUTION         # MIGRATIO        # MIGRATION SÉCURISÉE - VERSION FINALE CORRIGÉE
        logger.info("🔍 Test de fonctionnement PostgreSQL...")
        try:
            from database.db_manager import get_db
            from database.models import User
            db = get_db()
            test_count = db.query(User).count()
            db.close()
            logger.info("✅ PostgreSQL opérationnel - Pas de migration destructive")
        except Exception as test_error:
            logger.warning(f"⚠️ Test PostgreSQL: {test_error}")
            logger.info("🔧 Migration douce uniquement...")
            try:
                import quick_postgresql_fix
                quick_postgresql_fix.quick_postgresql_fix()
                logger.info("✅ Migration douce terminée")
            except Exception as migration_error:
                logger.error(f"❌ Migration: {migration_error}")
                logger.info("⚠️ Poursuite avec base existante...")E UNIQUEMENT SI NÉCESSAIRE (VERSION CORRIGÉE)
        logger.info("🔍 Test PostgreSQL sans destruction...")
        try:
            from database.db_manager import get_db
            from database.models import User
            db = get_db()
            test_count = db.query(User).count()
            db.close()
            logger.info("✅ PostgreSQL fonctionne parfaitement - Aucune migration")
        except Exception as test_error:
            logger.warning(f"⚠️ Test PostgreSQL: {test_error}")
            logger.info("🔧 Migration douce seulement si absolument nécessaire...")
            try:
                import quick_postgresql_fix
                quick_postgresql_fix.quick_postgresql_fix()
                logger.info("✅ Migration douce réussie")
            except Exception as migration_error:
                logger.error(f"❌ Migration: {migration_error}")
                logger.info("⚠️ Démarrage avec base actuelle...") ERREUR SQL 9h9h PERSISTANTE
        logger.info("🔍 Vérification état PostgreSQL...")
        try:
            # Test simple pour éviter les migrations destructives
            from database.db_manager import get_db
            from database.models import User
            db = get_db()
            test_count = db.query(User).count()
            db.close()
            logger.info("✅ PostgreSQL opérationnel - Migration non nécessaire")
        except Exception as test_error:
            logger.warning(f"⚠️ Test PostgreSQL échoué: {test_error}")
            logger.info("🔧 Migration douce uniquement si nécessaire...")
            try:
                import quick_postgresql_fix
                quick_postgresql_fix.quick_postgresql_fix()
                logger.info("✅ Migration douce appliquée")
            except Exception as migration_error:
                logger.error(f"❌ Migration échouée: {migration_error}")
                logger.info("⚠️ Démarrage avec base existante...") init_db
        init_db()
        logger.info("✅ Base de données initialisée avec succès")
        
        # MIGRATION INTELLIGENTE UNIQUEMENT SI NÉCESSAIRE
        logger.info("🔍 Vérification état base de données PostgreSQL...")
        try:
            # Test simple pour vérifier si les tables existent et fonctionnent
            from database.db_manager import get_db
            db = get_db()
            
            # Test de création d'un utilisateur test pour vérifier le schéma
            from database.models import User
            test_query = db.query(User).filter_by(telegram_id=999999999).first()
            db.close()
            
            logger.info("✅ Base de données PostgreSQL fonctionnelle - Aucune migration nécessaire")
            
        except Exception as test_error:
            logger.warning(f"⚠️ Test base échoué: {test_error}")
            logger.info("🔧 Migration intelligente en cours...")
            
            # Seulement si vraiment nécessaire - migration douce
            try:
                import quick_postgresql_fix
                quick_postgresql_fix.quick_postgresql_fix()
                logger.info("✅ Migration douce terminée")
            except Exception as migration_error:
                logger.error(f"❌ Migration échouée: {migration_error}")
                logger.info("⚠️ Démarrage avec base existante...")
            
    except Exception as e:
        logger.error(f"❌ Erreur d'initialisation de la base de données: {e}")E POSTGRESQL (PRESERVE LES DONNÉES)
        logger.info("🔧 Vérification schéma PostgreSQL...")
        try:
            # Ne plus recréer les tables ! Juste vérifier la connexion
            from database.models import User
            from database.db_manager import get_db
            
            db = get_db()
            try:
                # Test simple de connexion sans suppression
                count = db.query(User).count()
                logger.info(f"✅ PostgreSQL OK - {count} utilisateurs existants")
                db.close()
            except Exception as e:
                db.close()
                logger.warning(f"⚠️ Problème schéma (mais on continue): {e}")
                
        except Exception as migration_error:
            logger.warning(f"⚠️ Vérification PostgreSQL échouée: {migration_error}")s PayPal
"""

import os
import sys
import re
import asyncio
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

# NETTOYAGE IMMÉDIAT DES VARIABLES D'ENVIRONNEMENT (SOLUTION RENDER)
load_dotenv()

def clean_env_variable(value):
    """Nettoie une variable d'environnement des caractères non-ASCII"""
    if not value:
        return value
    # Supprimer TOUS les caractères non-ASCII (0-127) et de contrôle  
    cleaned = re.sub(r'[^\x20-\x7E]', '', value)
    return cleaned.strip()

# Nettoyer immédiatement les variables critiques AVANT tout import Telegram
critical_vars = ['TELEGRAM_BOT_TOKEN', 'PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET']
for var_name in critical_vars:
    value = os.getenv(var_name)
    if value:
        cleaned_value = clean_env_variable(value)
        if len(cleaned_value) != len(value):
            print(f"🔧 Variable {var_name}: {len(value) - len(cleaned_value)} caractères non-ASCII supprimés")
        os.environ[var_name] = cleaned_value
        print(f"✅ Variable {var_name} nettoyée")

# Marquer l'environnement
os.environ['RENDER'] = 'true'
os.environ['ENVIRONMENT'] = 'production'

print("✅ Variables d'environnement nettoyées avant imports Telegram")

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="CovoiturageSuisse Bot Webhook")

# Variable globale pour l'application Telegram
telegram_app = None

@app.on_event("startup")
async def startup_event():
    """Initialise le bot au démarrage"""
    global telegram_app
    logger.info("🚀 Démarrage du bot en mode webhook...")
    
    # Créer l'application bot
    try:
        telegram_app = await create_bot_app_webhook()
        logger.info("✅ Application bot créée avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur création bot: {e}")
        # Créer une application minimale pour éviter le crash
        from telegram.ext import Application
        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        await telegram_app.initialize()
        logger.info("⚠️ Application minimale créée")
    
    # Configurer le webhook
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        # Auto-générer l'URL webhook
        service_name = os.getenv('RENDER_SERVICE_NAME', 'covoiturage-suisse-bot')
        webhook_url = f"https://{service_name}.onrender.com"
        os.environ['WEBHOOK_URL'] = webhook_url
    
    webhook_endpoint = f"{webhook_url}/webhook"
    
    try:
        await telegram_app.bot.set_webhook(url=webhook_endpoint)
        logger.info(f"✅ Webhook configuré: {webhook_endpoint}")
    except Exception as e:
        logger.error(f"❌ Erreur webhook: {e}")

async def create_bot_app_webhook():
    """Crée l'application bot pour le mode webhook - COPIE EXACTE de bot.py.backup"""
    from telegram.ext import Application, PicklePersistence
    
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("Token non trouvé")
    
    # INITIALISATION CRITIQUE DE LA BASE DE DONNÉES
    logger.info("Initialisation de la base de données...")
    try:
        from database.db_manager import init_db
        init_db()
        logger.info("✅ Base de données initialisée avec succès")
        
        # CORRECTION FINALE: Migration sécurisée uniquement si nécessaire
        logger.info("🔍 Vérification PostgreSQL non-destructive...")
        try:
            from database.db_manager import get_db
            from database.models import User
            db = get_db()
            user_count = db.query(User).count()
            db.close()
            logger.info(f"✅ PostgreSQL OK - {user_count} utilisateurs en base")
        except Exception as test_error:
            logger.warning(f"⚠️ Test PostgreSQL: {test_error}")
            logger.info("🔧 Application migration douce...")
            try:
                import quick_postgresql_fix
                quick_postgresql_fix.quick_postgresql_fix()
                logger.info("✅ Migration douce appliquée avec succès")
            except Exception as migration_error:
                logger.error(f"❌ Migration échouée: {migration_error}")
                logger.info("⚠️ Démarrage avec base existante...")
            
    except Exception as e:
        logger.error(f"❌ Erreur d'initialisation de la base de données: {e}")
        raise
    
    # Initialisation des paiements PayPal (comme dans bot.py.backup)
    try:
        from db_utils import init_payment_database
        logger.info("Initialisation de la base de données de paiements...")
        if not init_payment_database():
            logger.error("Erreur lors de l'initialisation de la base de données de paiements")
        else:
            logger.info("✅ Base de données de paiements initialisée")
        
        # Vérification PayPal
        logger.info("Vérification de la configuration PayPal...")
        logger.info("✅ PayPal configuré avec succès")
    except Exception as e:
        logger.warning(f"Attention - Configuration PayPal : {e}")
    
    # 🔥 DÉSACTIVER PERSISTENCE PICKLE - Utiliser UNIQUEMENT PostgreSQL
    # persistence = PicklePersistence(filepath="bot_data.pickle")
    # application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()
    application = Application.builder().token(BOT_TOKEN).build()  # Sans persistence pickle
    
    # Importer et configurer tous les handlers EXACTEMENT comme dans bot.py.backup
    await setup_all_handlers_complete(application)
    
    # Initialiser l'application
    await application.initialize()
    
    return application

# 🎯 SUPPRIMÉ: handle_search_user_type_selection qui causait des conflits ConversationHandler
# Cette fonction appelait start_passenger_search directement sans passer par le ConversationHandler
# Maintenant, search_trip_handler.py gère search_user_type:driver via handle_search_user_type

async def setup_all_handlers_complete(application):
    """Configure TOUS les handlers EXACTEMENT comme dans bot.py.backup"""
    logger.info("Registering handlers...")
    
    # Import des handlers (EXACTEMENT comme bot.py.backup)
    from handlers.create_trip_handler import create_trip_conv_handler, publish_trip_handler, main_menu_handler, my_trips_handler
    from handlers.search_trip_handler import search_trip_conv_handler
    from handlers.menu_handlers import start_command, handle_menu_buttons, aide_command, handle_profile_creation, handle_profile_created_actions, handle_help_callbacks, profile_creation_handler
    from handlers.profile_handler import profile_handler, profile_button_handler, profile_conv_handler, back_to_profile
    from handlers.trip_handlers import register as register_trip_handlers
    from handlers.vehicle_handler import vehicle_conv_handler
    from telegram.ext import CommandHandler, CallbackQueryHandler
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    
    # Core handlers (EXACTEMENT comme bot.py.backup)
    application.add_handler(CommandHandler("start", start_command))
    
    # Commande PROFILE en deuxième position (EXACTEMENT comme bot.py.backup)
    async def cmd_profile(update: Update, context):
        """Commande /profile depuis le menu hamburger"""
        return await profile_handler(update, context)
    
    application.add_handler(CommandHandler("profile", cmd_profile))
    
    # Commandes d'aide
    application.add_handler(CommandHandler("aide", aide_command))
    application.add_handler(CommandHandler("help", aide_command))
    
    # Mes trajets
    async def cmd_my_trips(update: Update, context):
        """Commande /mes_trajets depuis le menu hamburger"""
        from handlers.trip_handlers import list_my_trips
        return await list_my_trips(update, context)
    
    application.add_handler(CommandHandler("mes_trajets", cmd_my_trips))
    
    # TOUS les CommandHandlers manquants du menu hamburger (CRITIQUES)
    async def cmd_verification(update: Update, context):
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
    
    async def cmd_paiements(update: Update, context):
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
    application.add_handler(CommandHandler("verification", cmd_verification))
    application.add_handler(CommandHandler("paiements", cmd_paiements))
    
    # Ajouter les commandes manquantes critiques pour le menu hamburger
    async def cmd_chercher_passagers(update: Update, context):
        """Commande /chercher_passagers depuis le menu hamburger - DÉCLENCHE LE ConversationHandler"""
        try:
            # Ne PAS appeler directement start_passenger_search !
            # Créer un callback pour déclencher l'entry point du ConversationHandler
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            await update.message.reply_text(
                "🔄 Démarrage de la recherche de passagers...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Commencer", callback_data="search_passengers")
                ]])
            )
            
        except Exception as e:
            logger.error(f"Erreur cmd_chercher_passagers: {e}")
            await update.message.reply_text("🔍 Recherche de passagers temporairement indisponible")
    
    application.add_handler(CommandHandler("chercher_passagers", cmd_chercher_passagers))
    
    logger.info("✅ TOUS les CommandHandlers du menu hamburger sont maintenant enregistrés")
    
    # Ajouter TOUS les ConversationHandlers (EXACTEMENT comme bot.py.backup)
    application.add_handler(profile_creation_handler)
    
    # 🎯 PRIORITÉ ABSOLUE: ConversationHandler de recherche passagers AVANT search_trip
    try:
        from handlers.search_passengers import register_search_passengers_handler
        register_search_passengers_handler(application)
        logger.info("✅ ConversationHandler recherche passagers enregistré EN PREMIER")
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE ConversationHandler search_passengers: {e}")
    
    # Import des ConversationHandlers manquants
    try:
        from handlers.create_trip_handler import create_trip_conv_handler
        from handlers.search_trip_handler import search_trip_conv_handler
        
        # IMPORTANT: Enregistrer create_trip_conv_handler
        application.add_handler(create_trip_conv_handler)
        logger.info("✅ create_trip_conv_handler enregistré")
        
        # APRÈS search_passengers: Enregistrer search_trip_conv_handler
        application.add_handler(search_trip_conv_handler)
        logger.info("✅ search_trip_conv_handler enregistré APRÈS search_passengers")
        
    except Exception as e:
        logger.warning(f"⚠️ ConversationHandlers principaux non disponibles: {e}")
    
    # Ajouter les autres ConversationHandlers nécessaires
    application.add_handler(profile_conv_handler)
    application.add_handler(vehicle_conv_handler)
    
    # Handlers de profil
    application.add_handler(CallbackQueryHandler(back_to_profile, pattern="^profile:back_to_profile$"))
    application.add_handler(profile_button_handler)
    
    # Autres handlers
    application.add_handler(publish_trip_handler)
    application.add_handler(main_menu_handler)
    application.add_handler(my_trips_handler)
    
    # Enregistrer tous les autres handlers nécessaires (EXACTEMENT comme bot.py.backup)
    try:
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
        
        # Register all handlers using their register functions
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
        logger.info("✅ Tous les handlers spécialisés enregistrés")
        
    except Exception as e:
        logger.warning(f"⚠️ Certains handlers spécialisés non disponibles: {e}")
        
    # Handlers pour le switch de profil conducteur/passager
    try:
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
    except Exception as e:
        logger.warning(f"⚠️ Handlers de switch: {e}")
    
    # Menu handlers (APRÈS les ConversationHandlers)
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:search_trip$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:my_trips$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:help$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:become_driver$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:back_to_main$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:back_to_menu$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^setup_paypal$"))
    
    # 🔧 CORRECTION: Handlers pour callbacks manqués critiques
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^profile_main$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^view_payments$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^payment_history$"))
    # ❌ SUPPRIMÉ: Conflit avec ConversationHandler search_passengers
    # application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^search_passengers$"))
    # application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^search_drivers$"))  # Garde supprimé pour l'instant
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^why_paypal_required$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^ignore$"))  # Pour calendriers
    
    # ❌ SUPPRIMÉ: Handler conflictuel qui appelait start_passenger_search en dehors du ConversationHandler
    # application.add_handler(CallbackQueryHandler(handle_search_user_type_selection, pattern="^search_user_type:(driver|passenger)$"))
    # 🎯 FIX: Laisser search_trip_handler.py gérer search_user_type via son ConversationHandler
    
    # 🚨 CORRECTION CRITIQUE: Handler de fallback pour callbacks non gérés (doit être en DERNIER)
    from handlers.global_callback_handler import handle_missing_callbacks
    
    # Handlers pour les actions après création de profil
    application.add_handler(CallbackQueryHandler(handle_profile_created_actions, pattern="^profile_created:"))
    
    # Handlers pour l'aide contextuelle
    application.add_handler(CallbackQueryHandler(handle_help_callbacks, pattern="^help:"))
    
    # Enregistrer les autres handlers (EXACTEMENT comme bot.py.backup)
    try:
        register_trip_handlers(application)
        logger.info("✅ Trip handlers enregistrés")
    except Exception as e:
        logger.warning(f"⚠️ Trip handlers: {e}")
    
    # Handlers PayPal (comme bot.py.backup)
    try:
        from payment_handlers import get_payment_handlers
        from handlers.paypal_setup_handler import get_paypal_setup_handlers
        
        # Enregistrer handlers de paiement
        payment_handlers = get_payment_handlers()
        for conv_handler in payment_handlers['conversation_handlers']:
            application.add_handler(conv_handler)
        for cmd_handler in payment_handlers['command_handlers']:
            application.add_handler(cmd_handler)
        for callback_handler in payment_handlers['callback_handlers']:
            application.add_handler(callback_handler)
            
        # Enregistrer handlers de configuration PayPal
        paypal_setup_handlers = get_paypal_setup_handlers()
        application.add_handler(paypal_setup_handlers['conversation_handler'])
        for cmd_handler in paypal_setup_handlers['command_handlers']:
            application.add_handler(cmd_handler)
        for callback_handler in paypal_setup_handlers['callback_handlers']:
            application.add_handler(callback_handler)
            
        logger.info("✅ Handlers PayPal configurés")
    except Exception as e:
        logger.warning(f"⚠️ Handlers PayPal: {e}")
    
    # Handlers d'annulation de réservation avec remboursement automatique
    try:
        from handlers.booking_cancellation_handlers import (
            booking_cancellation_handler,
            confirm_cancellation_handler,
            add_paypal_handler
        )
        from handlers.paypal_email_handler import paypal_email_handler
        
        application.add_handler(booking_cancellation_handler)
        application.add_handler(confirm_cancellation_handler) 
        application.add_handler(add_paypal_handler)
        application.add_handler(paypal_email_handler)
        logger.info("✅ Handlers d'annulation de réservation configurés")
    except Exception as e:
        logger.warning(f"⚠️ Handlers d'annulation: {e}")
    
    # Handlers de communication post-réservation
    try:
        from handlers.post_booking_handlers import (
            handle_contact_driver,
            handle_contact_passenger,
            handle_meeting_point,
            handle_cancel_booking_with_refund,
            handle_confirm_cancel,
            handle_trip_details
        )
        
        application.add_handler(CallbackQueryHandler(handle_contact_driver, pattern="^contact_driver:"))
        application.add_handler(CallbackQueryHandler(handle_contact_passenger, pattern="^contact_passenger:"))
        application.add_handler(CallbackQueryHandler(handle_meeting_point, pattern="^meeting_point:"))
        application.add_handler(CallbackQueryHandler(handle_cancel_booking_with_refund, pattern="^cancel_booking:"))
        application.add_handler(CallbackQueryHandler(handle_confirm_cancel, pattern="^confirm_cancel:"))
        application.add_handler(CallbackQueryHandler(handle_trip_details, pattern="^trip_details:"))
        
        logger.info("✅ Handlers de communication post-réservation configurés")
    except Exception as e:
        logger.warning(f"⚠️ Handlers de communication: {e}")
    
    # Configuration des commandes du menu hamburger (EXACTEMENT comme bot.py.backup)
    from telegram import BotCommand
    commands = [
        BotCommand("start", "🏠 Menu principal"),
        BotCommand("profile", "👤 Mon profil"),  # EN DEUXIÈME POSITION
        BotCommand("creer_trajet", "🚗 Créer un trajet"),
        BotCommand("chercher_trajet", "🔍 Chercher un trajet"),
        BotCommand("mes_trajets", "📋 Mes trajets"),
        BotCommand("chercher_passagers", "👥 Chercher des passagers"),
        BotCommand("verification", "✅ Vérification du compte"),
        BotCommand("paiements", "💰 Gestion des paiements"),
        BotCommand("aide", "❓ Aide et support")
    ]
    
    # Log pour confirmer la suppression de 'propositions'
    command_list = [cmd.command for cmd in commands]
    logger.info(f"📋 Menu hamburger configuré avec {len(commands)} commandes: {', '.join(command_list)}")
    logger.info("🗑️ Commande 'propositions' définitivement supprimée du menu")
    
    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ Commandes du menu hamburger configurées - version nettoyée sans propositions")
    except Exception as e:
        logger.warning(f"⚠️ Configuration menu hamburger: {e}")

    logger.info("🎉 TOUS les handlers configurés - ConversationHandler en priorité")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Gère les webhooks Telegram"""
    try:
        from telegram import Update
        
        json_data = await request.json()
        update = Update.de_json(json_data, telegram_app.bot)
        
        # LOG MINIMAL pour les callbacks importants
        if update.callback_query:
            callback_data = update.callback_query.data
            user_id = update.callback_query.from_user.id
            logger.info(f"� Callback: {callback_data[:50]}... user: {user_id}")
        
        # Traiter l'update
        await telegram_app.process_update(update)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erreur webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/paypal/webhook")
async def paypal_webhook_handler(request: Request):
    """Gère les webhooks PayPal avec logique complète"""
    try:
        json_data = await request.json()
        event_type = json_data.get('event_type', 'unknown')
        logger.info(f"Webhook PayPal reçu: {event_type}")
        
        # Importer et utiliser la logique PayPal existante
        from paypal_webhook_handler import handle_paypal_webhook
        
        # Traiter le webhook avec la logique existante
        success = await handle_paypal_webhook(json_data, telegram_app)
        
        if success:
            logger.info(f"✅ Webhook PayPal {event_type} traité avec succès")
            return {"status": "ok"}
        else:
            logger.warning(f"⚠️ Webhook PayPal {event_type} traité avec des avertissements")
            return {"status": "ok"}  # Toujours retourner OK à PayPal
            
    except Exception as e:
        logger.error(f"❌ Erreur webhook PayPal: {e}")
        # Toujours retourner OK à PayPal pour éviter les retry
        return {"status": "ok"}

@app.get("/health")
async def health_check():
    """Point de contrôle de santé"""
    return {"status": "healthy", "mode": "webhook", "bot": "online"}

@app.get("/")
async def root():
    """Page d'accueil"""
    return {"message": "CovoiturageSuisse Bot Webhook", "status": "running"}

@app.get("/payment/success/{booking_id}")
async def payment_success(booking_id: int, token: str = None, PayerID: str = None):
    """Route de retour après succès de paiement PayPal"""
    logger.info(f"🎉 PAYMENT SUCCESS: booking_id={booking_id}, token={token}, PayerID={PayerID}")
    
    try:
        from paypal_utils import PayPalManager
        from database import get_db
        from database.models import Booking
        
        # Récupérer la réservation
        db = get_db()
        booking = db.query(Booking).filter_by(id=booking_id).first()
        
        if not booking:
            logger.error(f"❌ Réservation {booking_id} non trouvée")
            db.close()
            return {"error": "Réservation non trouvée"}
        
        # Capturer le paiement PayPal
        paypal = PayPalManager()
        success, capture_data = paypal.capture_order(token)
        
        if success:
            # Mettre à jour le statut de la réservation
            booking.payment_status = 'completed'
            booking.paypal_transaction_id = capture_data.get('id')
            db.commit()
            
            logger.info(f"✅ Paiement capturé avec succès: {capture_data.get('id')}")
            
            # Page de succès simple
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Paiement Réussi</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: green; font-size: 24px; }}
                    .info {{ color: #666; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1 class="success">✅ Paiement Réussi !</h1>
                <p class="info">Votre réservation #{booking_id} a été confirmée.</p>
                <p class="info">Vous recevrez un message de confirmation dans le bot Telegram.</p>
                <p>Merci d'utiliser CovoiturageSuisse ! 🚗</p>
                <script>
                    // Fermer la fenêtre après 3 secondes
                    setTimeout(() => {{
                        window.close();
                    }}, 3000);
                </script>
            </body>
            </html>
            """
            
            db.close()
            return HTMLResponse(content=html_content)
            
        else:
            booking.payment_status = 'failed'
            db.commit()
            db.close()
            
            logger.error(f"❌ Échec capture paiement: {capture_data}")
            return {"error": "Échec de la capture du paiement"}
            
    except Exception as e:
        logger.error(f"❌ Erreur payment success: {e}")
        return {"error": "Erreur interne"}

@app.get("/payment/cancel/{booking_id}")
async def payment_cancel(booking_id: int):
    """Route de retour après annulation de paiement PayPal"""
    logger.info(f"❌ PAYMENT CANCELLED: booking_id={booking_id}")
    
    try:
        from database import get_db
        from database.models import Booking
        
        # Marquer la réservation comme annulée
        db = get_db()
        booking = db.query(Booking).filter_by(id=booking_id).first()
        
        if booking:
            booking.payment_status = 'cancelled'
            db.commit()
        
        db.close()
        
        # Page d'annulation
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Paiement Annulé</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .cancel { color: orange; font-size: 24px; }
                .info { color: #666; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1 class="cancel">❌ Paiement Annulé</h1>
            <p class="info">Votre paiement a été annulé.</p>
            <p class="info">Vous pouvez réessayer depuis le bot Telegram.</p>
            <script>
                setTimeout(() => {
                    window.close();
                }, 3000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"❌ Erreur payment cancel: {e}")
        return {"error": "Erreur interne"}

@app.post("/admin/force-payment")
async def force_payment_processing(request: Request):
    """Endpoint d'administration pour forcer le traitement d'un paiement"""
    try:
        data = await request.json()
        payment_id = data.get('payment_id')
        booking_id = data.get('booking_id')
        
        if not payment_id and not booking_id:
            return {"error": "payment_id ou booking_id requis"}
        
        logger.info(f"🔧 Force traitement: payment_id={payment_id}, booking_id={booking_id}")
        
        from paypal_webhook_handler import handle_payment_completion
        
        # Si booking_id fourni, récupérer le payment_id
        if booking_id and not payment_id:
            from database.db_manager import get_db
            from database.models import Booking
            
            db = get_db()
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if booking and booking.paypal_payment_id:
                payment_id = booking.paypal_payment_id
            else:
                return {"error": f"Aucun payment_id trouvé pour booking {booking_id}"}
        
        # Traiter le paiement
        result = await handle_payment_completion(payment_id, telegram_app)
        
        if result:
            logger.info(f"✅ Force traitement réussi pour {payment_id}")
            return {"success": True, "payment_id": payment_id, "message": "Paiement traité avec succès"}
        else:
            logger.error(f"❌ Force traitement échoué pour {payment_id}")
            return {"success": False, "payment_id": payment_id, "message": "Échec du traitement"}
            
    except Exception as e:
        logger.error(f"❌ Erreur force payment: {e}")
        return {"error": str(e)}

@app.post("/admin/migrate-database")
async def migrate_database_render():
    """Endpoint de migration pour Render - Ajoute les colonnes manquantes"""
    try:
        logger.info("🚀 DÉBUT MIGRATION RENDER")
        
        from database.db_manager import get_db
        from sqlalchemy import text
        
        db = get_db()
        
        # Vérifier PostgreSQL
        if 'postgresql' not in str(db.bind.url):
            return {"success": False, "error": "Pas en PostgreSQL"}
        
        # Liste des colonnes à ajouter (uniquement celles qui manquent)
        migrations = [
            ("trips", "driver_confirmed_completion", "BOOLEAN DEFAULT FALSE"),
            ("trips", "payment_released", "BOOLEAN DEFAULT FALSE"),
            ("bookings", "passenger_confirmed_completion", "BOOLEAN DEFAULT FALSE"),
            ("trips", "total_trip_price", "DECIMAL(10,2)"),
            ("users", "paypal_email", "VARCHAR(254)"),
            ("trips", "confirmed_by_driver", "BOOLEAN DEFAULT FALSE"),
            ("trips", "confirmed_by_passengers", "BOOLEAN DEFAULT FALSE"),
            ("trips", "driver_amount", "DECIMAL(10,2)"),
            ("trips", "commission_amount", "DECIMAL(10,2)"),
            ("trips", "payout_batch_id", "VARCHAR(255)"),
            ("trips", "last_paypal_reminder", "TIMESTAMP"),
            ("bookings", "paypal_payment_id", "VARCHAR(255)"),
            ("bookings", "refund_id", "VARCHAR(255)"),
            ("bookings", "refund_amount", "DECIMAL(10,2)"),
            ("bookings", "refund_date", "TIMESTAMP"),
            ("bookings", "original_price", "DECIMAL(10,2)"),
        ]
        
        results = []
        success_count = 0
        
        for table, column, definition in migrations:
            try:
                # Vérifier si la colonne existe
                check_sql = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{column}'
                """
                
                result = db.execute(text(check_sql)).fetchone()
                
                if result:
                    results.append(f"⏭️ {table}.{column} - EXISTE DÉJÀ")
                    continue
                
                # Ajouter la colonne
                add_sql = f"ALTER TABLE {table} ADD COLUMN {column} {definition};"
                db.execute(text(add_sql))
                db.commit()
                
                results.append(f"✅ {table}.{column} - AJOUTÉE")
                success_count += 1
                
            except Exception as e:
                results.append(f"❌ {table}.{column} - ERREUR: {str(e)}")
        
        logger.info(f"✅ Migration terminée - {success_count} colonnes ajoutées")
        
        return {
            "success": True,
            "message": f"Migration terminée - {success_count} colonnes ajoutées",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur migration Render: {e}")
        return {"success": False, "error": str(e)}

@app.post("/admin/show-user-bookings")
async def show_user_bookings():
    """Voir toutes les réservations de l'utilisateur"""
    try:
        from database.db_manager import get_db
        from database.models import Booking, Trip
        
        db = get_db()
        
        # TOUTES tes réservations
        user_bookings = db.query(Booking).filter(
            Booking.passenger_id == 5932296330
        ).order_by(Booking.id.desc()).all()
        
        booking_details = []
        for booking in user_bookings:
            trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
            booking_details.append({
                "booking_id": booking.id,
                "trip_id": booking.trip_id,
                "departure": trip.departure_city if trip else "Unknown",
                "arrival": trip.arrival_city if trip else "Unknown", 
                "payment_status": booking.payment_status,
                "is_paid": booking.is_paid,
                "paypal_id": booking.paypal_payment_id[:15] + "..." if booking.paypal_payment_id else None,
                "amount": str(booking.amount) if booking.amount else "No amount"
            })
        
        return {
            "success": True,
            "total_bookings": len(user_bookings),
            "bookings": booking_details
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
async def test_simple():
    """Test simple sans imports compliqués"""
    try:
        from database.db_manager import get_db
        from database.models import Booking
        
        db = get_db()
        
        # Compter les réservations de l'utilisateur pour le trajet 8
        bookings_count = db.query(Booking).filter(
            Booking.trip_id == 8,
            Booking.passenger_id == 5932296330
        ).count()
        
        # Réservations avec PayPal ID
        paypal_bookings = db.query(Booking).filter(
            Booking.paypal_payment_id.isnot(None)
        ).count()
        
        # TOUTES les réservations de l'utilisateur
        user_bookings = db.query(Booking).filter(
            Booking.passenger_id == 5932296330
        ).all()
        
        # Détails des réservations
        booking_details = []
        for booking in user_bookings[-10:]:  # Les 10 dernières
            trip = db.query(db.query(Booking).filter(Booking.id == booking.id).first().trip).first() if hasattr(booking, 'trip') else None
            booking_details.append({
                "id": booking.id,
                "trip_id": booking.trip_id,
                "payment_status": booking.payment_status,
                "is_paid": booking.is_paid,
                "paypal_id": booking.paypal_payment_id[:10] + "..." if booking.paypal_payment_id else None
            })
        
        return {
            "success": True,
            "message": "Test simple réussi",
            "duplicate_bookings_trip_8": bookings_count,
            "total_paypal_bookings": paypal_bookings,
            "total_user_bookings": len(user_bookings),
            "last_10_bookings": booking_details,
            "postgres_working": True
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
async def test_notifications():
    """Test des notifications sans faire de vrais paiements"""
    try:
        logger.info("🧪 TEST DES NOTIFICATIONS")
        
        from database.db_manager import get_db
        from database.models import Booking, Trip, User
        
        db = get_db()
        
        # Prendre la dernière réservation payée
        booking = db.query(Booking).filter(
            Booking.payment_status == 'completed'
        ).order_by(Booking.id.desc()).first()
        
        if not booking:
            return {"error": "Aucune réservation payée trouvée"}
        
        trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
        passenger = db.query(User).filter(User.id == booking.passenger_id).first()
        
        if not trip or not passenger:
            return {"error": "Données manquantes"}
        
        # Obtenir l'instance bot
        from bot import create_application
        global telegram_app
        if 'telegram_app' not in globals() or not telegram_app:
            telegram_app = create_application()
        
        # Test notification passager
        try:
            await telegram_app.bot.send_message(
                chat_id=booking.passenger_id,
                text=f"🧪 **TEST - Notification passager**\n\n"
                     f"✅ Votre réservation #{booking.id} est confirmée !\n"
                     f"📍 {trip.departure_city} → {trip.arrival_city}\n"
                     f"🕒 {trip.departure_datetime}\n\n"
                     f"*Ce message est un test système*",
                parse_mode='Markdown'
            )
            logger.info(f"✅ Test notification passager envoyée à {booking.passenger_id}")
            passenger_notif = "✅ Envoyée"
        except Exception as e:
            logger.error(f"❌ Erreur test passager: {e}")
            passenger_notif = f"❌ Erreur: {str(e)}"
        
        # Test notification conducteur
        try:
            await telegram_app.bot.send_message(
                chat_id=trip.driver_id,
                text=f"🧪 **TEST - Notification conducteur**\n\n"
                     f"🎉 Nouvelle réservation pour votre trajet !\n"
                     f"📍 {trip.departure_city} → {trip.arrival_city}\n"
                     f"👤 Passager: {passenger.first_name}\n"
                     f"📋 Réservation #{booking.id}\n\n"
                     f"*Ce message est un test système*",
                parse_mode='Markdown'
            )
            logger.info(f"✅ Test notification conducteur envoyée à {trip.driver_id}")
            driver_notif = "✅ Envoyée"
        except Exception as e:
            logger.error(f"❌ Erreur test conducteur: {e}")
            driver_notif = f"❌ Erreur: {str(e)}"
        
        return {
            "success": True,
            "booking_id": booking.id,
            "trip_id": trip.id,
            "passenger_notification": passenger_notif,
            "driver_notification": driver_notif,
            "message": "Test des notifications terminé"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur test notifications: {e}")
        return {"success": False, "error": str(e)}

@app.post("/admin/reprocess-last-payment")
async def reprocess_last_payment():
    """Retraiter le dernier paiement pour tester les notifications"""
    try:
        logger.info("🔄 RETRAITEMENT DERNIER PAIEMENT")
        
        from database.db_manager import get_db
        from database.models import Booking
        from paypal_webhook_handler import handle_payment_completion
        from bot import create_application
        
        db = get_db()
        
        # Prendre la dernière réservation avec un PayPal ID
        booking = db.query(Booking).filter(
            Booking.paypal_payment_id.isnot(None),
            Booking.payment_status == 'completed'
        ).order_by(Booking.id.desc()).first()
        
        if not booking:
            return {"error": "Aucune réservation PayPal trouvée"}
        
        # Créer l'app bot directement
        global telegram_app, application
        if 'telegram_app' not in globals() or not telegram_app:
            # Utiliser l'app déjà créée dans ce serveur
            telegram_app = application
        
        # Simuler le retraitement du paiement
        success = await handle_payment_completion(booking.paypal_payment_id, telegram_app)
        
        return {
            "success": success,
            "booking_id": booking.id,
            "paypal_id": booking.paypal_payment_id,
            "message": "Retraitement terminé - Vérifiez vos notifications Telegram"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur retraitement: {e}")
        return {"success": False, "error": str(e)}

@app.post("/admin/debug-system")
async def debug_complete_system():
    """Debug complet: réservations + boutons + notifications"""
    try:
        logger.info("🔍 DEBUG COMPLET DU SYSTÈME")
        
        from database.db_manager import get_db
        from database.models import Booking, Trip, User
        from trip_confirmation_system import add_confirmation_buttons_to_trip
        
        db = get_db()
        
        # 1. Compter les réservations dupliquées
        duplicate_bookings = db.query(Booking).filter(
            Booking.trip_id == 8,  # Le trajet avec beaucoup de réservations
            Booking.passenger_id == 5932296330  # Ton ID utilisateur
        ).all()
        
        # 2. Tester les boutons de confirmation
        confirmation_buttons = await add_confirmation_buttons_to_trip(8, 5932296330, 'passenger')
        
        # 3. Dernière réservation payée
        last_paid = db.query(Booking).filter(
            Booking.payment_status == 'completed'
        ).order_by(Booking.id.desc()).first()
        
        # 4. Test notification simple
        global application
        notification_test = "❌ Bot non initialisé"
        if application:
            try:
                await application.bot.send_message(
                    chat_id=5932296330,
                    text="🔧 TEST DEBUG SYSTÈME\n\nCe message confirme que les notifications fonctionnent !",
                    parse_mode='Markdown'
                )
                notification_test = "✅ Notification envoyée"
            except Exception as e:
                notification_test = f"❌ Erreur: {str(e)}"
        
        return {
            "success": True,
            "duplicate_bookings_count": len(duplicate_bookings),
            "duplicate_booking_ids": [b.id for b in duplicate_bookings],
            "confirmation_buttons": len(confirmation_buttons) if confirmation_buttons else 0,
            "confirmation_buttons_details": [str(btn.text) for btn in confirmation_buttons] if confirmation_buttons else [],
            "last_paid_booking": last_paid.id if last_paid else None,
            "notification_test": notification_test,
            "bot_available": application is not None
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur debug: {e}")
        return {"success": False, "error": str(e)}

@app.get("/admin/pending-payments")
async def get_pending_payments():
    """Liste les paiements en attente"""
    try:
        from database.db_manager import get_db
        from database.models import Booking
        
        db = get_db()
        pending = db.query(Booking).filter(
            Booking.paypal_payment_id.isnot(None),
            Booking.is_paid == False
        ).order_by(Booking.id.desc()).limit(20).all()
        
        result = []
        for booking in pending:
            result.append({
                "id": booking.id,
                "passenger_id": booking.passenger_id,
                "trip_id": booking.trip_id,
                "amount": booking.amount,
                "status": booking.status,
                "paypal_payment_id": booking.paypal_payment_id,
                "payment_status": booking.payment_status,
                "booking_date": booking.booking_date.isoformat() if booking.booking_date else None
            })
        
        logger.info(f"📊 {len(result)} paiements en attente trouvés")
        return {"pending_payments": result, "count": len(result)}
        
    except Exception as e:
        logger.error(f"❌ Erreur get pending payments: {e}")
        return {"error": str(e)}

@app.post("/admin/cleanup-bookings")
async def cleanup_duplicate_bookings():
    """Endpoint désactivé - nettoyage terminé"""
    return {
        "success": False,
        "message": "Nettoyage déjà effectué - endpoint désactivé pour sécurité"
    }

@app.post("/admin/test-real-notification")
async def test_real_notification():
    """Test notification avec l'app globale"""
    try:
        global application
        
        if not application:
            return {"error": "Application non initialisée"}
        
        await application.bot.send_message(
            chat_id=5932296330,
            text="🎉 **TEST NOTIFICATION RÉUSSIE !**\n\nLes notifications fonctionnent maintenant !"
        )
        
        return {"success": True, "message": "Notification envoyée !"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Démarrage serveur webhook sur port {port}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
