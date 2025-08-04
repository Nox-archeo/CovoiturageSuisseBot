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
    
    # Créer l'application EXACTEMENT comme dans bot.py.backup
    persistence = PicklePersistence(filepath="bot_data.pickle")
    application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()
    
    # Importer et configurer tous les handlers EXACTEMENT comme dans bot.py.backup
    await setup_all_handlers_complete(application)
    
    # Initialiser l'application
    await application.initialize()
    
    return application

async def handle_search_user_type_selection(update: Update, context: CallbackContext):
    """Gère la sélection du type d'utilisateur (conducteur/passager) en dehors du ConversationHandler"""
    from telegram.ext import CallbackContext
    query = update.callback_query
    await query.answer()
    
    user_type = query.data.split(":")[1]  # "driver" ou "passenger"
    
    if user_type == "driver":
        # Rediriger vers la recherche de passagers
        from handlers.search_passengers import start_passenger_search
        return await start_passenger_search(update, context)
    elif user_type == "passenger":
        # Rediriger vers la recherche de trajets normale
        from handlers.search_trip_handler import start_search_trip
        context.user_data.clear()
        context.user_data['search_user_type'] = 'passenger'
        return await start_search_trip(update, context)
    else:
        await query.edit_message_text(
            "❌ Option non reconnue. Veuillez réessayer.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Menu principal", callback_data="main_menu")
            ]])
        )

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
        """Commande /chercher_passagers depuis le menu hamburger"""
        try:
            from handlers.search_passengers import cmd_search_passengers
            return await cmd_search_passengers(update, context)
        except Exception as e:
            logger.error(f"Erreur cmd_chercher_passagers: {e}")
            await update.message.reply_text("🔍 Recherche de passagers temporairement indisponible")
    
    application.add_handler(CommandHandler("chercher_passagers", cmd_chercher_passagers))
    
    logger.info("✅ TOUS les CommandHandlers du menu hamburger sont maintenant enregistrés")
    
    # Ajouter TOUS les ConversationHandlers (EXACTEMENT comme bot.py.backup)
    application.add_handler(profile_creation_handler)
    
    # Import des ConversationHandlers manquants
    try:
        from handlers.create_trip_handler import create_trip_conv_handler
        from handlers.search_trip_handler import search_trip_conv_handler
        
        # IMPORTANT: Enregistrer create_trip_conv_handler EN PREMIER
        application.add_handler(create_trip_conv_handler)
        logger.info("✅ create_trip_conv_handler enregistré")
        
    except Exception as e:
        logger.warning(f"⚠️ ConversationHandlers principaux non disponibles: {e}")
    
    # Handlers de recherche spécialisés
    try:
        # Fonction register_menu_search_handlers n'existe pas encore
        # from handlers.menu_handlers import register_menu_search_handlers
        from handlers.search_passengers import register_search_passengers_handler
        # register_menu_search_handlers(application)
        register_search_passengers_handler(application)
        logger.info("✅ Handlers de recherche spécialisés enregistrés")
    except Exception as e:
        logger.warning(f"⚠️ Handlers de recherche: {e}")
    
    # Ajouter les autres ConversationHandlers nécessaires
    application.add_handler(search_trip_conv_handler)
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
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^search_passengers$"))  # 🔧 Remis - menu handler redirige maintenant
    # application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^search_drivers$"))  # Garde supprimé pour l'instant
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^why_paypal_required$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^ignore$"))  # Pour calendriers
    
    # 🔧 NOUVEAU: Handlers pour types de recherche (fix boutons non-fonctionnels)
    application.add_handler(CallbackQueryHandler(handle_search_user_type_selection, pattern="^search_user_type:(driver|passenger)$"))
    
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
    
    # 🚨 HANDLER GLOBAL DE FALLBACK - DOIT ÊTRE EN DERNIER POUR NE PAS INTERCEPTER LES AUTRES
    logger.info("🔧 Ajout du handler global de fallback en dernier...")
    # 🚨 CRITIQUE: Le handler global ne doit PAS capturer les callbacks de recherche
    # Motif simplifié pour exclure tous les callbacks commençant par search_
    application.add_handler(CallbackQueryHandler(
        handle_missing_callbacks, 
        pattern=r"^(?!search_|contact_driver_|profile:|menu:|pay_proposal:|enter_price:|reject_proposal:|cancel_payment_|confirm_payment_|view_payments|payment_history|book_|trip_|edit_).*"
    ))
    logger.info("✅ Handler global de fallback ajouté - exclut search_ prefix")
    
    logger.info("🎉 TOUS les handlers configurés comme dans bot.py.backup")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Gère les webhooks Telegram"""
    try:
        from telegram import Update
        
        json_data = await request.json()
        update = Update.de_json(json_data, telegram_app.bot)
        
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

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Démarrage serveur webhook sur port {port}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
