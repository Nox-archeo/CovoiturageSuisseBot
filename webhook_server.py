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
    """Crée l'application bot pour le mode webhook"""
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
    
    # Créer l'application
    persistence = PicklePersistence(filepath="bot_data.pickle")
    application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()
    
    # Importer et configurer tous les handlers comme dans bot.py
    await setup_all_handlers(application)
    
    # Initialiser l'application
    await application.initialize()
    
    return application

async def setup_all_handlers(application):
    """Configure les handlers de base du bot"""
    try:
        # Import des handlers de base
        from handlers.menu_handlers import start_command
        from telegram.ext import CommandHandler
        
        # Commandes de base
        application.add_handler(CommandHandler("start", start_command))
        logger.info("✅ Handlers de base configurés")
        
        # Essayer d'ajouter les autres handlers
        try:
            from handlers.profile_handler import profile_handler
            async def cmd_profile(update, context):
                return await profile_handler(update, context)
            application.add_handler(CommandHandler("profile", cmd_profile))
            logger.info("✅ Handler profile ajouté")
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'ajouter profile handler: {e}")
            
    except Exception as e:
        logger.error(f"❌ Erreur configuration handlers: {e}")
        # Au minimum, ajouter un handler start basique
        from telegram.ext import CommandHandler
        async def basic_start(update, context):
            await update.message.reply_text("🤖 Bot en mode maintenance - Webhook actif")
        application.add_handler(CommandHandler("start", basic_start))
    
    logger.info("✅ Handlers principaux configurés pour webhook")

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
    """Gère les webhooks PayPal"""
    try:
        json_data = await request.json()
        logger.info(f"Webhook PayPal reçu: {json_data.get('event_type', 'unknown')}")
        
        # Traiter le webhook PayPal
        # TODO: Ajouter la logique de traitement PayPal
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erreur webhook PayPal: {e}")
        return {"status": "error", "message": str(e)}

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
