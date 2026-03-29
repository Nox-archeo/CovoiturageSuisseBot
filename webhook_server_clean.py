#!/usr/bin/env python3
"""
Version webhook PROPRE pour Render - SANS persistence pickle
ConversationHandlers configurés en mode non-persistant
"""

import os
import sys
import logging
import re
from dotenv import load_dotenv

# Nettoyer les variables d'environnement
load_dotenv()

def clean_env_variable(value):
    """Nettoie une variable d'environnement des caractères non-ASCII"""
    if not value:
        return value
    cleaned = re.sub(r'[^\x20-\x7E]', '', value)
    return cleaned.strip()

# Nettoyer les variables critiques
critical_vars = ['TELEGRAM_BOT_TOKEN', 'PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET']
for var_name in critical_vars:
    value = os.getenv(var_name)
    if value:
        cleaned_value = clean_env_variable(value)
        if len(cleaned_value) != len(value):
            print(f"🔧 Variable {var_name}: {len(value) - len(cleaned_value)} caractères non-ASCII supprimés")
        os.environ[var_name] = cleaned_value
        print(f"✅ Variable {var_name} nettoyée")

# Marquer l'environnement Render
os.environ['RENDER'] = 'true'
os.environ['ENVIRONMENT'] = 'production'

print("✅ Variables d'environnement nettoyées")

# Imports
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from telegram import Update
from telegram.ext import Application

# Configuration logging
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
    logger.info("🚀 Démarrage bot webhook RENDER - SANS pickle")
    
    try:
        telegram_app = await create_bot_app_render()
        logger.info("✅ Application bot créée")
        
        # Configurer webhook
        webhook_url = os.getenv('WEBHOOK_URL', 'https://covoituragesuissebot.onrender.com')
        webhook_endpoint = f"{webhook_url}/webhook"
        
        await telegram_app.bot.set_webhook(url=webhook_endpoint)
        logger.info(f"✅ Webhook configuré: {webhook_endpoint}")
        
    except Exception as e:
        logger.error(f"❌ Erreur startup: {e}")
        # Créer app minimale pour éviter crash
        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        await telegram_app.initialize()

async def create_bot_app_render():
    """Crée l'application bot pour Render SANS persistence"""
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("Token Telegram manquant")
    
    # Initialiser PostgreSQL
    logger.info("Initialisation PostgreSQL...")
    try:
        from database.db_manager import init_db
        init_db()
        logger.info("✅ PostgreSQL initialisé")
    except Exception as e:
        logger.error(f"❌ Erreur PostgreSQL: {e}")
        raise
    
    # Créer application SANS persistence
    application = Application.builder().token(BOT_TOKEN).build()
    logger.info("🚀 Application créée SANS persistence pickle")
    
    # Configurer handlers en mode NON-PERSISTANT
    await setup_handlers_no_persistence(application)
    
    # Initialiser
    await application.initialize()
    return application

async def setup_handlers_no_persistence(application):
    """Configure les handlers en mode NON-PERSISTANT"""
    logger.info("Configuration handlers non-persistants...")
    
    # Imports
    from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler
    from telegram import Update
    
    # Handlers de base
    async def start_command(update: Update, context):
        """Commande /start"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("🚗 Créer un trajet", callback_data="menu:create_trip")],
            [InlineKeyboardButton("🔍 Chercher un trajet", callback_data="menu:search_trip")],
            [InlineKeyboardButton("👤 Mon profil", callback_data="menu:profile")],
            [InlineKeyboardButton("📋 Mes trajets", callback_data="menu:my_trips")],
            [InlineKeyboardButton("❓ Aide", callback_data="menu:help")]
        ]
        
        await update.message.reply_text(
            "🚗 **Bienvenue sur CovoiturageSuisse !**\n\n"
            "Que souhaitez-vous faire ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_callbacks(update: Update, context):
        """Gestionnaire de callbacks simple"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "menu:create_trip":
            await query.edit_message_text(
                "🚗 **Création de trajet**\n\n"
                "Cette fonctionnalité est temporairement en maintenance.\n"
                "Utilisez /start pour revenir au menu principal.",
                parse_mode='Markdown'
            )
        elif data == "menu:search_trip":
            await query.edit_message_text(
                "🔍 **Recherche de trajet**\n\n"
                "Cette fonctionnalité est temporairement en maintenance.\n"
                "Utilisez /start pour revenir au menu principal.",
                parse_mode='Markdown'
            )
        elif data == "menu:profile":
            await query.edit_message_text(
                "👤 **Mon profil**\n\n"
                "Cette fonctionnalité est temporairement en maintenance.\n"
                "Utilisez /start pour revenir au menu principal.",
                parse_mode='Markdown'
            )
        elif data == "menu:my_trips":
            await query.edit_message_text(
                "📋 **Mes trajets**\n\n"
                "Cette fonctionnalité est temporairement en maintenance.\n"
                "Utilisez /start pour revenir au menu principal.",
                parse_mode='Markdown'
            )
        elif data == "menu:help":
            await query.edit_message_text(
                "❓ **Aide et support**\n\n"
                "📧 Contact: support@covoiturage-suisse.ch\n"
                "🌐 Site web: https://covoiturage-suisse.ch\n\n"
                "Utilisez /start pour revenir au menu principal.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "⚠️ Fonction en cours de développement.\n"
                "Utilisez /start pour revenir au menu principal."
            )
    
    # Enregistrer les handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    
    # Commandes du menu hamburger
    from telegram import BotCommand
    commands = [
        BotCommand("start", "🏠 Menu principal"),
        BotCommand("profile", "👤 Mon profil"),
        BotCommand("aide", "❓ Aide et support")
    ]
    
    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ Menu hamburger configuré (version simplifiée)")
    except Exception as e:
        logger.warning(f"⚠️ Erreur menu: {e}")
    
    logger.info("✅ Handlers configurés en mode non-persistant")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Gère les webhooks Telegram"""
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, telegram_app.bot)
        
        # Log minimal
        if update.message:
            user_id = update.message.from_user.id
            text = update.message.text[:50] if update.message.text else "media"
            logger.info(f"📱 Message: {text}... de {user_id}")
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            data = update.callback_query.data[:30]
            logger.info(f"🔘 Callback: {data}... de {user_id}")
        
        # Traiter l'update
        await telegram_app.process_update(update)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"❌ Erreur webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    """Point de santé"""
    return {"status": "healthy", "mode": "webhook_render", "bot": "online"}

@app.get("/")
async def root():
    """Page d'accueil"""
    return {"message": "CovoiturageSuisse Bot Webhook - Render", "status": "running"}

@app.post("/admin/test-bot")
async def test_bot_functionality():
    """Tester le bot"""
    try:
        global telegram_app
        
        if not telegram_app:
            return {"error": "Bot non initialisé"}
        
        # Test simple
        me = await telegram_app.bot.get_me()
        
        # Test notification
        await telegram_app.bot.send_message(
            chat_id=5932296330,  # Ton ID
            text="🧪 **TEST RENDER**\n\nLe bot fonctionne correctement ! ✅",
            parse_mode='Markdown'
        )
        
        return {
            "success": True,
            "bot_username": me.username,
            "bot_id": me.id,
            "message": "Test réussi - Notification envoyée"
        }
        
    except Exception as e:
        logger.error(f"❌ Test bot: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Démarrage serveur port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
