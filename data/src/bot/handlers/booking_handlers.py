from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler
from database import get_db
from database.models import Booking, Trip, User

# États
SELECTING_TRIP = 0
CONFIRMING_BOOKING = 1
PAYMENT = 2

async def view_available_trips(update: Update, context):
    """Affiche les trajets disponibles"""
    db = get_db()
    trips = db.query(Trip).filter(
        Trip.seats_available > 0,
        Trip.status == 'active'
    ).all()
    
    if not trips:
        await update.message.reply_text(
            "❌ Aucun trajet disponible pour le moment."
        )
        return ConversationHandler.END
        
    buttons = []
    for trip in trips:
        buttons.append([
            InlineKeyboardButton(
                f"🚗 {trip.departure} → {trip.destination} ({trip.price} CHF)",
                callback_data=f"book_{trip.id}"
            )
        ])
    
    await update.message.reply_text(
        "🔍 <b>Trajets disponibles:</b>\n\n"
        "Sélectionnez un trajet pour réserver:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )
    return SELECTING_TRIP

async def book_trip(update: Update, context):
    """Gère la réservation d'un trajet"""
    query = update.callback_query
    trip_id = query.data.split('_')[1]
    
    trip = db.query(Trip).filter_by(id=trip_id).first()
    
    if trip.seats_available > 0:
        # Crée la réservation
        booking = Booking(
            trip_id=trip_id,
            passenger_id=update.effective_user.id,
            status='pending'
        )
        db.add(booking)
        db.commit()
        
        # Procède au paiement
        context.user_data['booking_trip_id'] = trip_id
        await process_payment(update, context)
    else:
        await query.edit_message_text(
            "❌ Désolé, ce trajet est complet."
        )

# ... existing code ...
