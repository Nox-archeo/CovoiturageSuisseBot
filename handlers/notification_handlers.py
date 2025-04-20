from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from database.models import User, Trip, Booking
from datetime import datetime, timedelta

async def send_trip_reminder(context):
    """Envoie des rappels pour les trajets à venir"""
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    # Récupérer les trajets de demain
    db = get_db()
    trips = db.query(Trip).filter(
        Trip.departure_time.between(tomorrow, tomorrow + timedelta(days=1))
    ).all()
    
    for trip in trips:
        # Notification au conducteur
        driver_message = (
            "🚗 Rappel: Vous avez un trajet demain\n\n"
            f"De: {trip.departure_city}\n"
            f"À: {trip.arrival_city}\n"
            f"Heure: {trip.departure_time.strftime('%H:%M')}\n"
            f"Passagers: {len(trip.bookings)}/{trip.seats_available}"
        )
        await context.bot.send_message(
            chat_id=trip.driver.telegram_id,
            text=driver_message
        )
        
        # Notification aux passagers
        for booking in trip.bookings:
            passenger_message = (
                "🚗 Rappel: Vous avez un trajet demain\n\n"
                f"De: {trip.departure_city}\n"
                f"À: {trip.arrival_city}\n"
                f"Heure: {trip.departure_time.strftime('%H:%M')}\n"
                f"Conducteur: {trip.driver.username}"
            )
            await context.bot.send_message(
                chat_id=booking.passenger.telegram_id,
                text=passenger_message
            )

async def notify_booking_request(trip_id, passenger_id):
    """Notifie le conducteur d'une nouvelle demande de réservation"""
    db = get_db()
    trip = db.query(Trip).get(trip_id)
    passenger = db.query(User).get(passenger_id)
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Accepter", callback_data=f"accept_booking_{trip_id}_{passenger_id}"),
            InlineKeyboardButton("❌ Refuser", callback_data=f"reject_booking_{trip_id}_{passenger_id}")
        ]
    ]
    
    await context.bot.send_message(
        chat_id=trip.driver.telegram_id,
        text=f"📝 Nouvelle demande de réservation\n"
             f"De: {passenger.username}\n"
             f"Pour: {trip.departure_city} → {trip.arrival_city}\n"
             f"Le: {trip.departure_time.strftime('%d/%m/%Y %H:%M')}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def register(application):
    """Enregistre les jobs de notification"""
    job_queue = application.job_queue
    # Exécuter tous les jours à 20h
    job_queue.run_daily(
        send_trip_reminder,
        time=datetime.time(hour=20, minute=0)
    )
