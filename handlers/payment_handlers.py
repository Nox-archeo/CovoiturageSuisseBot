from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from database.models import Booking, Trip
import stripe
import os
from datetime import datetime, timedelta

stripe.api_key = os.getenv('STRIPE_API_KEY')
COMMISSION_RATE = float(os.getenv('COMMISSION_RATE', 12)) / 100

PAYMENT_STEPS = range(1)
COMMISSION = 0.10  # 10% de commission

async def initiate_payment(update: Update, context):
    """Démarre le processus de paiement"""
    booking_id = context.user_data.get('current_booking')
    if not booking_id:
        await update.message.reply_text("Aucune réservation en cours.")
        return
    
    db = get_db()
    booking = db.query(Booking).get(booking_id)
    
    # Calculer le montant total avec commission
    amount = booking.trip.price_per_seat
    commission_amount = amount * COMMISSION
    total_amount = amount + commission_amount
    
    try:
        # Créer un intent de paiement Stripe
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_amount * 100),  # Convertir en centimes
            currency='chf',
            payment_method_types=['card'],
            metadata={
                'booking_id': booking_id,
                'trip_id': booking.trip_id
            }
        )
        
        keyboard = [
            [InlineKeyboardButton("💳 Payer maintenant", url=payment_intent.client_secret)],
            [InlineKeyboardButton("❌ Annuler", callback_data="cancel_payment")]
        ]
        
        await update.message.reply_text(
            f"💳 Paiement pour le trajet\n\n"
            f"De: {booking.trip.departure_city}\n"
            f"À: {booking.trip.arrival_city}\n"
            f"Prix: {amount:.2f} CHF\n"
            f"Commission: {commission_amount:.2f} CHF\n"
            f"Total: {total_amount:.2f} CHF",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except stripe.error.StripeError as e:
        await update.message.reply_text(
            "❌ Erreur lors de l'initialisation du paiement.\n"
            "Veuillez réessayer plus tard."
        )
        print(f"Erreur Stripe: {e}")

async def handle_payment_success(update: Update, context):
    """Gère le succès du paiement"""
    booking_id = context.user_data.get('current_booking')
    db = get_db()
    booking = db.query(Booking).get(booking_id)
    
    booking.status = 'confirmed'
    booking.payment_confirmed = True
    db.commit()
    
    # Notifier le conducteur
    await context.bot.send_message(
        chat_id=booking.trip.driver.telegram_id,
        text=f"💰 Nouveau paiement reçu pour le trajet {booking.trip.departure_city} → {booking.trip.arrival_city}"
    )
    
    # Notifier le passager
    keyboard = [[InlineKeyboardButton("📱 Contacter le conducteur", callback_data=f"contact_driver_{booking.trip.driver_id}")]]
    await update.message.reply_text(
        "✅ Paiement confirmé!\n\n"
        "Vous recevrez bientôt les détails du point de rendez-vous.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def register(application):
    """Enregistre les handlers de paiement"""
    application.add_handler(CallbackQueryHandler(initiate_payment, pattern="^pay_booking_"))
    application.add_handler(CallbackQueryHandler(handle_payment_success, pattern="^payment_success"))
