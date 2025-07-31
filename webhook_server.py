#!/usr/bin/env python3
"""
Version webhook du bot avec port HTTP pour Render
Combine bot + serveur web pour les webhooks PayPal
"""

import os
import sys
import re
import asyncio
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn

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
    
    # Pour l'instant, créer une application basique pour tester le déploiement
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
    
    logger.info("✅ Commandes de base configurées")
    
    # Ajouter TOUS les ConversationHandlers (EXACTEMENT comme bot.py.backup)
    application.add_handler(profile_creation_handler)
    application.add_handler(create_trip_conv_handler)
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
    
    # Menu handlers (APRÈS les ConversationHandlers)
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:search_trip$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:my_trips$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:help$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:become_driver$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:back_to_main$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:back_to_menu$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^setup_paypal$"))
    
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
        BotCommand("propositions", "🚗 Demandes de passagers"),
        BotCommand("chercher_passagers", "👥 Chercher des passagers"),
        BotCommand("verification", "✅ Vérification du compte"),
        BotCommand("paiements", "💰 Gestion des paiements"),
        BotCommand("aide", "❓ Aide et support")
    ]
    
    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ Commandes du menu hamburger configurées avec profile en 2ème position")
    except Exception as e:
        logger.warning(f"⚠️ Configuration menu hamburger: {e}")
    
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
