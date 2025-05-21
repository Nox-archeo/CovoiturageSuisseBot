from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from database.models import Booking, Trip, User
import os

DESCRIBE_ISSUE, UPLOAD_PROOF = range(2)
ADMIN_IDS = os.getenv('ADMIN_USER_IDS').split(',')

async def open_dispute(update: Update, context):
    """Ouvre un litige pour une réservation"""
    booking_id = context.args[0] if context.args else None
    if not booking_id:
        keyboard = []
        # Récupérer les réservations récentes
        bookings = get_recent_bookings(update.effective_user.id)
        for booking in bookings:
            keyboard.append([
                InlineKeyboardButton(
                    f"{booking.trip.departure_city} → {booking.trip.arrival_city}",
                    callback_data=f"dispute_{booking.id}"
                )
            ])
        
        await update.message.reply_text(
            "Pour quel trajet souhaitez-vous ouvrir un litige?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return DESCRIBE_ISSUE

async def handle_dispute_description(update: Update, context):
    """Traite la description du litige"""
    dispute_text = update.message.text
    booking_id = context.user_data.get('dispute_booking_id')
    
    # Notifier les admins
    for admin_id in ADMIN_IDS:
        keyboard = [
            [
                InlineKeyboardButton("✅ Rembourser", callback_data=f"refund_{booking_id}"),
                InlineKeyboardButton("❌ Rejeter", callback_data=f"reject_dispute_{booking_id}")
            ]
        ]
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"⚠️ Nouveau litige\n\nRéservation: {booking_id}\n\n{dispute_text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    await update.message.reply_text(
        "Votre litige a été enregistré. Un administrateur va examiner votre demande."
    )
    return ConversationHandler.END

# Fonction manquante pour get_recent_bookings
def get_recent_bookings(user_id):
    """Récupère les réservations récentes d'un utilisateur"""
    from database import get_db
    db = get_db()
    return db.query(Booking).filter_by(passenger_id=user_id).all()

def register(application):
    """Enregistre les handlers de litige"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("litige", open_dispute)],
        states={
            DESCRIBE_ISSUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dispute_description),
                CallbackQueryHandler(
                    lambda u, c: u.callback_query.answer("Sélection du litige"),
                    pattern="^dispute_"
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_message=True,
        per_chat=True
    )
    
    application.add_handler(conv_handler)
    
    # Handler pour les boutons de résolution de litige (admin)
    application.add_handler(CallbackQueryHandler(
        lambda u, c: u.callback_query.answer("Demande de remboursement transmise"),
        pattern="^refund_"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda u, c: u.callback_query.answer("Litige rejeté"),
        pattern="^reject_dispute_"
    ))
