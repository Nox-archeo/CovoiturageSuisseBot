from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler
from database.models import Booking, Trip, User
from datetime import datetime

CONFIRM_BOOKING = range(1)

async def book_trip(update: Update, context: CallbackContext):
    """Démarre le processus de réservation"""
    trip_id = context.args[0] if context.args else None
    if not trip_id:
        await update.message.reply_text("Veuillez spécifier un ID de trajet.")
        return

    trip = Trip.query.get(trip_id)
    if not trip:
        await update.message.reply_text("Trajet non trouvé.")
        return

    keyboard = [
        [
            InlineKeyboardButton("Confirmer", callback_data=f"confirm_booking_{trip_id}"),
            InlineKeyboardButton("Annuler", callback_data="cancel_booking")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Réservation du trajet:\n"
        f"De: {trip.departure_city}\n"
        f"À: {trip.arrival_city}\n"
        f"Date: {trip.departure_time}\n"
        f"Prix: {trip.price_per_seat} CHF\n\n"
        f"Voulez-vous confirmer la réservation?",
        reply_markup=reply_markup
    )

async def confirm_booking_callback(update: Update, context: CallbackContext):
    """Confirme la réservation et redirige vers le paiement"""
    query = update.callback_query
    trip_id = query.data.split('_')[-1]
    
    # Créer la réservation
    booking = Booking(
        trip_id=trip_id,
        passenger_id=update.effective_user.id,
        status='pending'
    )
    # Sauvegarder dans la base de données
    
    context.user_data['booking_id'] = booking.id
    await query.edit_message_text(
        "Réservation enregistrée! Procédons au paiement.",
    )
    await process_payment(update, context)

def register(application):
    """Enregistre les handlers de réservation"""
    application.add_handler(CommandHandler("reserver", book_trip))
    application.add_handler(CallbackQueryHandler(
        confirm_booking_callback,
        pattern='^confirm_booking_'
    ))
