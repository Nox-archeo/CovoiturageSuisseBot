from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
import sys
import os

# Ajout du chemin parent au chemin d'importation Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from database import get_db
from database.models import User

CHOOSING_PROFILE = 0
EDITING_PROFILE = 1

async def profile_menu(update: Update, context):
    """Menu principal du profil"""
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()

    keyboard = [
        [
            InlineKeyboardButton("🚗 Mode Conducteur", 
                callback_data="toggle_driver"),
            InlineKeyboardButton("🧍 Mode Passager", 
                callback_data="toggle_passenger")
        ],
        [InlineKeyboardButton("📊 Mes Statistiques", callback_data="stats")],
        [InlineKeyboardButton("💳 Gestion Paiements", callback_data="payments")]
    ]

    status = []
    if user.is_driver:
        status.append("✅ Profil conducteur actif")
    if user.is_passenger:
        status.append("✅ Profil passager actif")
    
    rating = f"⭐ Note: {user.rating}/5" if user.rating else "Pas encore de note"

    await update.message.reply_text(
        f"""👤 <b>Votre Profil</b>

{user.first_name}
{rating}
{', '.join(status)}

Trajets effectués: {user.trips_completed}

<i>Que souhaitez-vous faire ?</i>""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return CHOOSING_PROFILE

async def toggle_driver_mode(update: Update, context):
    """Active/désactive le mode conducteur"""
    query = update.callback_query
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    user.is_driver = not user.is_driver
    db.commit()
    
    status = "activé ✅" if user.is_driver else "désactivé ❌"
    await query.answer(f"Mode conducteur {status}")
    await show_profile(update, context)
    
async def toggle_passenger_mode(update: Update, context):
    """Active/désactive le mode passager"""
    query = update.callback_query
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    user.is_passenger = not user.is_passenger
    db.commit()
    
    status = "activé ✅" if user.is_passenger else "désactivé ❌"
    await query.answer(f"Mode passager {status}")
    await show_profile(update, context)

# ... existing code ...
