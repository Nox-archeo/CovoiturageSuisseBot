import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chargement du token
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start_command(update, context):
    await update.message.reply_text(
        "Bienvenue sur CovoiturageSuisse! 🚗\n\n"
        "/chercher - Rechercher un trajet\n"
        "/creer - Créer un nouveau trajet\n"
        "/aide - Obtenir de l'aide"
    )

async def help_command(update, context):
    await update.message.reply_text("Comment puis-je vous aider ?")

async def run_polling():
    """Fonction séparée pour le polling pour éviter les problèmes d'Updater"""
    app = Application.builder().token(TOKEN).build()
    
    # Ajouter les commandes
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("aide", help_command))
    
    # Démarrer le bot
    logger.info("Démarrage du bot...")
    await app.initialize()
    await app.start()
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        # Utiliser asyncio.run() pour gérer la boucle d'événements
        asyncio.run(run_polling())
    except KeyboardInterrupt:
        logger.info("Bot arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur: {e}")

