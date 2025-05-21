from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler
import sys
import os

# Ajout du chemin parent au chemin d'importation Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from database import get_db
from database.models import User, Trip, Rating

RATING = 0

async def start_rating(update: Update, context):
    """Démarre le processus de notation"""
    keyboard = [
        [
            InlineKeyboardButton("⭐", callback_data="rate_1"),
            InlineKeyboardButton("⭐⭐", callback_data="rate_2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_5")
        ]
    ]
    
    await update.message.reply_text(
        """🌟 <b>Noter votre trajet</b>

Comment s'est passé votre trajet ? 
Donnez une note de 1 à 5 étoiles.""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return RATING

async def handle_rating(update: Update, context):
    """Enregistre la note donnée"""
    query = update.callback_query
    stars = int(query.data.split('_')[1])
    trip_id = context.user_data.get('trip_to_rate')
    
    db = get_db()
    rating = Rating(
        trip_id=trip_id,
        user_id=update.effective_user.id,
        stars=stars
    )
    db.add(rating)
    
    # Met à jour la moyenne du conducteur
    trip = db.query(Trip).filter_by(id=trip_id).first()
    driver = db.query(User).filter_by(id=trip.driver_id).first()
    driver.update_rating()
    
    db.commit()
    
    await query.edit_message_text(
        f"✅ Merci pour votre note ! ({stars}⭐)"
    )
    return ConversationHandler.END

def register(application):
    """Enregistre les handlers de notation"""
    rating_conv = ConversationHandler(
        entry_points=[CommandHandler('noter', start_rating)],
        states={
            RATING: [CallbackQueryHandler(handle_rating, pattern='^rate_')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(rating_conv)
