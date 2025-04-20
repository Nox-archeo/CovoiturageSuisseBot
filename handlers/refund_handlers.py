from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import stripe
from database.models import Booking, Payment
import os

stripe.api_key = os.getenv('STRIPE_API_KEY')

async def process_refund(update: Update, context):
    """Traite une demande de remboursement"""
    booking_id = context.args[0] if context.args else None
    if not booking_id:
        await update.message.reply_text("ID de réservation requis")
        return
    
    booking = Booking.get(booking_id)
    if not booking.payment_id:
        await update.message.reply_text("Aucun paiement trouvé pour cette réservation")
        return
    
    try:
        refund = stripe.Refund.create(
            payment_intent=booking.payment_id,
            reason='requested_by_customer'
        )
        
        # Enregistrer le remboursement
        booking.status = 'refunded'
        Payment.create(
            booking_id=booking_id,
            amount=refund.amount,
            type='refund',
            stripe_id=refund.id
        )
        
        await update.message.reply_text("✅ Remboursement traité avec succès")
        
    except stripe.error.StripeError as e:
        await update.message.reply_text(f"❌ Erreur lors du remboursement: {str(e)}")
