import logging
import os
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, PicklePersistence
from dotenv import load_dotenv
from handlers import (
    trip_handlers, user_handlers, booking_handlers, payment_handlers,
    menu_handlers, menu_action_handlers, profile_handlers, verification_handlers
)

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def get_clean_token():
    """Récupère et nettoie le token"""
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("Token Telegram non trouvé dans .env")
    
    # Nettoyer le token de toute altération possible
    token = token.encode().decode('unicode_escape')  # Gère les caractères échappés
    token = token.strip().strip('"').strip("'")  # Enlève les guillemets/espaces
    if not token or '\\' in token or '%' in token:
        raise ValueError("Token invalide")
    return token

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
    token = get_clean_token()
    
    # Configuration de la persistence
    persistence = PicklePersistence(filepath="conversation_states.pickle")
    
    # Création de l'application
    app = Application.builder().token(token).persistence(persistence).build()
    
    # Ajouter les commandes de base
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("aide", help_command))
    
    # Enregistrer les handlers des différents modules dans un ordre optimisé
    # Enregistrer les handlers de conversation spécifiques qui utilisent des commandes
    profile_handlers.register(app)
    verification_handlers.register(app)
    
    # Enregistrer les handlers de création et recherche de trajet
    trip_handlers.register(app)
    
    # Puis les handlers généraux qui capturent les boutons de menu
    menu_handlers.register(app)
    menu_action_handlers.register(app)
    
    # Et enfin les handlers pour les commandes simples
    booking_handlers.register(app)
    payment_handlers.register(app)
    user_handlers.register(app)
    
    # Démarrer le bot
    logger.info("Démarrage du bot...")
    await app.initialize()
    await app.start()
    await app.run_polling(drop_pending_updates=True)

def main():
    """Point d'entrée principal"""
    try:
        # Utiliser asyncio.run() pour gérer la boucle d'événements
        asyncio.run(run_polling())
    except KeyboardInterrupt:
        logger.info("Bot arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        raise

if __name__ == '__main__':
    print("🚀 Démarrage du bot CovoiturageSuisse...")
    main()
