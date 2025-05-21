from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from database.models import User, Trip, Booking
from database import get_db

async def rate_trip(update: Update, context):
    """Permet de noter un trajet"""
    booking_id = context.args[0] if context.args else None
    if not booking_id:
        await update.message.reply_text("Veuillez spécifier une réservation à noter.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{i} ⭐", callback_data=f"rate_{booking_id}_{i}") 
         for i in range(1, 6)]
    ]
    await update.message.reply_text(
        "Notez votre expérience:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_rating(update: Update, context):
    """Traite la note donnée"""
    query = update.callback_query
    await query.answer()
    
    _, booking_id, rating = query.data.split('_')
    rating = int(rating)
    
    db = get_db()
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if booking:
        # Mettre à jour la note du conducteur/passager
        if booking.passenger_id == update.effective_user.id:
            driver = booking.trip.driver
            driver.driver_rating = (driver.driver_rating + rating) / 2
        else:
            passenger = booking.passenger
            passenger.passenger_rating = (passenger.passenger_rating + rating) / 2
        db.commit()
        
    await query.edit_message_text("Merci pour votre évaluation! ⭐")

def register(application):
    """Enregistre les handlers de notation"""
    application.add_handler(CommandHandler("noter", rate_trip))
    application.add_handler(CallbackQueryHandler(handle_rating, pattern="^rate_"))
