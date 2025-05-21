import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, ConversationHandler
from database.models import User
from database import get_db

logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    """Handler pour la commande /start"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Rechercher", callback_data="rechercher"),
            InlineKeyboardButton("➕ Créer", callback_data="creer_trajet")
        ],
        [
            InlineKeyboardButton("👤 Mon Profil", callback_data="profil"),
            InlineKeyboardButton("🗂️ Mes Trajets", callback_data="mes_trajets")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Sauvegarder l'utilisateur dans la BDD
    try:
        db = get_db()
        user = update.effective_user
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        if not db_user:
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(new_user)
            db.commit()
            logger.info(f"Nouvel utilisateur créé: {user.id}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de l'utilisateur: {e}")

    await update.message.reply_text(
        "🚗 Bienvenue sur CovoiturageSuisse!\n\n"
        "Je suis votre assistant pour trouver ou proposer des trajets en Suisse.\n\n"
        "Que souhaitez-vous faire ?",
        reply_markup=reply_markup
    )

start_handler = CommandHandler('start', start)
