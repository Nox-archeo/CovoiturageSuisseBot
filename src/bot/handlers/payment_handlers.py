import stripe
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db
from database.models import Payment, Trip, User
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

COMMISSION_RATE = 0.12  # 12% de commission

async def process_payment(update: Update, context):
    """Traite un paiement via Stripe"""
    query = update.callback_query
    trip_id = context.user_data.get('booking_trip_id')
    
    trip = db.query(Trip).filter_by(id=trip_id).first()
    
    try:
        # Calcul du prix avec commission
        base_price = trip.price
        commission = round(base_price * COMMISSION_RATE, 2)
        total_price = base_price + commission
        
        # Crée la session de paiement Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'chf',
                    'unit_amount': int(total_price * 100),
                    'product_data': {
                        'name': f'Trajet {trip.departure} → {trip.destination}',
                        'description': f'Trajet avec {trip.driver.first_name}'
                    },
                },
                'quantity': 1,
            }],
            payment_intent_data={
                'application_fee_amount': int(commission * 100),
            },
            mode='payment',
            success_url=f"{os.getenv('BOT_URL')}?start=payment_success_{session.id}",
            cancel_url=f"{os.getenv('BOT_URL')}?start=payment_cancel",
            metadata={
                'trip_id': trip_id,
                'passenger_id': update.effective_user.id,
                'commission': commission
            }
        )
        
        # Sauvegarde la session
        payment = Payment(
            trip_id=trip_id,
            passenger_id=update.effective_user.id,
            driver_id=trip.driver_id,
            stripe_session_id=session.id,
            amount=base_price,
            commission=commission,
            total_amount=total_price,
            status='pending'
        )
        db.add(payment)
        db.commit()
        
        # Envoie le lien de paiement
        keyboard = [[
            InlineKeyboardButton("💳 Payer maintenant", url=session.url)
        ]]
        
        await query.edit_message_text(
            f"""💳 <b>Paiement du trajet</b>

Prix du trajet: {base_price} CHF
Frais de service: {commission} CHF
Total à payer: {total_price} CHF

<i>Le paiement est sécurisé via Stripe.
Le montant sera transféré au conducteur après le trajet.</i>""",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Erreur paiement: {str(e)}")
        await query.edit_message_text(
            "❌ Une erreur est survenue. Veuillez réessayer."
        )

async def handle_payment_success(update: Update, context):
    """Gère le succès du paiement"""
    session_id = context.args[0] if context.args else None
    if not session_id:
        return
        
    db = get_db()
    payment = db.query(Payment).filter_by(stripe_session_id=session_id).first()
    
    if payment and payment.status == 'pending':
        # Vérifie le statut Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            # Met à jour le paiement
            payment.status = 'completed'
            # Met à jour le trajet
            trip = payment.trip
            trip.seats_available -= 1
            db.commit()
            
            await update.message.reply_text(
                """✅ <b>Paiement confirmé!</b>

🎟️ Votre place est réservée
💳 Le conducteur recevra le paiement après le trajet
📧 Un récapitulatif a été envoyé par email

<i>Bon voyage!</i>""",
                parse_mode='HTML'
            )

async def handle_payment_webhook(request):
    """Gère les webhooks Stripe"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
        
        if event.type == 'checkout.session.completed':
            session = event.data.object
            payment = Payment.query.filter_by(
                stripe_session_id=session.id
            ).first()
            
            if payment:
                payment.status = 'completed'
                payment.stripe_payment_intent = session.payment_intent
                db.session.commit()
                
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {'error': str(e)}, 400
        
    return {'status': 'success'}, 200
