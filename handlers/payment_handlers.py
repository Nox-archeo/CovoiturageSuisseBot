from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from database.models import Booking, Trip
import stripe
import os
from datetime import datetime

stripe.api_key = os.getenv('STRIPE_API_KEY')
COMMISSION_RATE = float(os.getenv('COMMISSION_RATE', 12)) / 100

async def process_payment(update: Update, context: CallbackContext):
    """Traite le paiement d'une réservation"""
    booking_id = context.user_data.get('booking_id')
    if not booking_id:
        await update.message.reply_text("Aucune réservation en cours.")
        return

    try:
        booking = Booking.query.get(booking_id)
        amount = int(booking.trip.price_per_seat * 100)  # Conversion en centimes
        commission = int(amount * COMMISSION_RATE)
        
        # Créer la session de paiement Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'chf',
                    'unit_amount': amount,
                    'product_data': {
                        'name': f'Trajet {booking.trip.departure_city} - {booking.trip.arrival_city}',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://t.me/votre_bot?start=payment_success',
            cancel_url='https://t.me/votre_bot?start=payment_cancel',
        )
        
        # Créer le bouton de paiement
        keyboard = [[InlineKeyboardButton("Payer maintenant", url=session.url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Cliquez ci-dessous pour procéder au paiement:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await update.message.reply_text("Erreur lors du traitement du paiement.")
        print(f"Erreur de paiement: {e}")

def register(application):
    """Enregistre les handlers de paiement"""
    application.add_handler(CommandHandler("payer", process_payment))
