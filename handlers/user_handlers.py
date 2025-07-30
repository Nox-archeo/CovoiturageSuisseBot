from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, ConversationHandler
from database.models import User
from sqlalchemy.orm import Session

async def start(update: Update, context: CallbackContext):
    """Commande de démarrage, enregistre l'utilisateur"""
    user = update.effective_user
    welcome_text = (
        f"Bienvenue {user.full_name} sur CovoiturageSuisse! 🚗\n\n"
        "Voici les commandes disponibles:\n"
        "/chercher - Rechercher un trajet\n"
        "/creer - Créer un nouveau trajet\n"
        "/profil - Voir votre profil\n"
        "/aide - Obtenir de l'aide"
    )
    await update.message.reply_text(welcome_text)

async def profile(update: Update, context: CallbackContext):
    """Affiche le profil de l'utilisateur"""
    user = update.effective_user
    profile_text = (
        f"Profil de {user.full_name}\n\n"
        "Vos trajets à venir:\n"
        "Vos réservations:\n"
        "Votre note moyenne:"
    )
    await update.message.reply_text(profile_text)

def register(application):
    """Enregistre les handlers pour les utilisateurs"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profil", profile))
