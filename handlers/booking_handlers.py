from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler
from database.models import Booking, Trip, User
from datetime import datetime
from paypal_utils import create_trip_payment
from database import get_db
import logging

logger = logging.getLogger(__name__)

CONFIRM_BOOKING = range(1)

async def book_trip(update: Update, context: CallbackContext):
    """Démarre le processus de réservation"""
    trip_id = context.args[0] if context.args else None
    if not trip_id:
        await update.message.reply_text("Veuillez spécifier un ID de trajet.")
        return

    trip = Trip.query.get(trip_id)
    # Correction : empêcher la réservation d'un trajet annulé
    if not trip or getattr(trip, 'is_cancelled', False):
        await update.message.reply_text("Trajet non trouvé ou annulé.")
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

# Fonction manquante qui est appelée dans confirm_booking_callback
async def process_payment(update, context):
    """Redirige vers le processus de paiement"""
    query = update.callback_query
    await query.answer()
    
    # Cette fonction devrait normalement être liée à payment_handlers.py
    keyboard = [
        [InlineKeyboardButton("💳 Payer maintenant", callback_data=f"pay_booking_{context.user_data.get('booking_id')}")],
        [InlineKeyboardButton("❌ Annuler", callback_data="cancel_booking")]
    ]
    
    await query.edit_message_text(
        "Votre réservation a été créée. Procédez au paiement pour la confirmer.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_booking_with_payment(update: Update, context: CallbackContext):
    """Confirme la réservation et déclenche automatiquement le paiement PayPal"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split('_')[-1])
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        
        # Vérifier que le trajet existe et n'est pas annulé
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip or getattr(trip, 'is_cancelled', False):
            await query.edit_message_text("❌ Trajet non trouvé ou annulé.")
            return
        
        # Vérifier les places disponibles
        if trip.available_seats <= 0:
            await query.edit_message_text("❌ Plus de places disponibles pour ce trajet.")
            return
        
        # Vérifier si l'utilisateur existe
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            await query.edit_message_text("❌ Utilisateur non trouvé. Utilisez /start d'abord.")
            return
        
        # Vérifier si une réservation existe déjà
        existing_booking = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.passenger_id == user.id,
            Booking.status.in_(['confirmed', 'pending'])
        ).first()
        
        if existing_booking:
            await query.edit_message_text("❌ Vous avez déjà une réservation pour ce trajet.")
            return
        
        # CORRECTION CRITIQUE: Calculer le prix dynamique basé sur le nombre de passagers
        from utils.swiss_pricing import calculate_price_per_passenger, round_to_nearest_0_05_up
        
        # Compter les passagers qui ont déjà payé
        existing_paid_passengers = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.payment_status.in_(['completed', 'paid'])
        ).count()
        
        # Le nouveau passager sera le (existing_paid_passengers + 1)ème
        new_passenger_count = existing_paid_passengers + 1
        
        # Récupérer le prix total du trajet
        # Si le trajet a été créé avec l'ancienne logique, utiliser price_per_seat * seats_available
        total_trip_price = getattr(trip, 'total_trip_price', None)
        if not total_trip_price:
            # Fallback: Recalculer le prix total depuis la distance ou utiliser l'ancien système
            if hasattr(trip, 'total_distance') and trip.total_distance:
                from handlers.trip_handlers import compute_price_auto
                total_trip_price, _ = compute_price_auto(trip.departure_city, trip.arrival_city)
            else:
                # Estimation basée sur le prix par place et le nombre de places
                total_trip_price = trip.price_per_seat * trip.seats_available
        
        # Calculer le prix par passager avec arrondi suisse
        price_per_passenger = calculate_price_per_passenger(total_trip_price, new_passenger_count)
        
        # Créer la réservation
        booking = Booking(
            trip_id=trip_id,
            passenger_id=user.id,
            status='pending',
            total_price=price_per_passenger,  # Prix dynamique calculé
            booking_date=datetime.utcnow(),
            payment_status='pending'
        )
        
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        # Créer automatiquement le paiement PayPal
        trip_description = f"{trip.departure_city} → {trip.arrival_city}"
        success, payment_id, approval_url = create_trip_payment(
            amount=float(price_per_passenger),  # Utiliser le prix dynamique
            trip_description=trip_description,
            booking_id=booking.id  # Pour le suivi
        )
        
        if success and payment_id and approval_url:
            # Sauvegarder l'ID de paiement PayPal
            booking.paypal_payment_id = payment_id
            db.commit()
            
            # Créer le clavier avec le lien de paiement
            keyboard = [
                [InlineKeyboardButton("💳 Payer maintenant avec PayPal", url=approval_url)],
                [InlineKeyboardButton("❌ Annuler la réservation", callback_data=f"cancel_booking_{booking.id}")]
            ]
            
            await query.edit_message_text(
                f"✅ *Réservation créée !*\n\n"
                f"🚗 **Détails du trajet :**\n"
                f"📍 De : {trip.departure_city}\n"
                f"📍 À : {trip.arrival_city}\n"
                f"📅 Date : {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                f"💰 Prix : {price_per_passenger:.2f} CHF par place\n"
                f"👤 Conducteur : {trip.driver.full_name if trip.driver else 'Inconnu'}\n\n"
                f"💳 **Paiement requis**\n"
                f"💡 *Prix calculé pour {new_passenger_count} passager(s)*\n"
                f"Cliquez sur le bouton ci-dessous pour payer avec PayPal.\n"
                f"Votre place sera confirmée après le paiement.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Notifier le conducteur de la nouvelle réservation
            if trip.driver and trip.driver.telegram_id:
                try:
                    await context.bot.send_message(
                        chat_id=trip.driver.telegram_id,
                        text=(
                            f"🎉 **Nouvelle réservation !**\n\n"
                            f"Un passager a réservé votre trajet :\n"
                            f"📍 {trip.departure_city} → {trip.arrival_city}\n"
                            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                            f"👤 Passager : {user.full_name or 'Nom non défini'}\n\n"
                            f"⏳ En attente du paiement PayPal..."
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Erreur notification conducteur: {e}")
            
            logger.info(f"Réservation créée avec paiement PayPal: booking_id={booking.id}, payment_id={payment_id}")
            
        else:
            # Erreur lors de la création du paiement PayPal
            db.delete(booking)
            db.commit()
            
            await query.edit_message_text(
                "❌ Erreur lors de la création du paiement PayPal.\n"
                "Veuillez réessayer plus tard ou contacter le support."
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la réservation avec paiement: {e}")
        await query.edit_message_text(
            "❌ Erreur lors de la réservation. Veuillez réessayer plus tard."
        )

async def cancel_booking_callback(update: Update, context: CallbackContext):
    """Annule une réservation en attente"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_booking":
        await query.edit_message_text("❌ Réservation annulée.")
        return
    
    # Format: cancel_booking_{booking_id}
    booking_id = int(query.data.split('_')[-1])
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        
        # Trouver la réservation
        user = db.query(User).filter(User.telegram_id == user_id).first()
        booking = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.passenger_id == user.id,
            Booking.status == 'pending'
        ).first()
        
        if not booking:
            await query.edit_message_text("❌ Réservation non trouvée ou déjà traitée.")
            return
        
        # Annuler la réservation
        booking.status = 'cancelled'
        booking.payment_status = 'cancelled'
        db.commit()
        
        await query.edit_message_text(
            "❌ **Réservation annulée**\n\n"
            "Votre réservation a été annulée avec succès.\n"
            "Si vous aviez commencé un paiement PayPal, il sera automatiquement annulé.",
            parse_mode="Markdown"
        )
        
        logger.info(f"Réservation {booking_id} annulée par l'utilisateur {user_id}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de réservation: {e}")
        await query.edit_message_text("❌ Erreur lors de l'annulation. Veuillez réessayer.")

async def check_booking_status(update: Update, context: CallbackContext):
    """Commande pour vérifier le statut des réservations"""
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await update.message.reply_text("❌ Utilisateur non trouvé. Utilisez /start d'abord.")
            return
        
        # Récupérer les réservations actives
        bookings = db.query(Booking).filter(
            Booking.passenger_id == user.id,
            Booking.status.in_(['pending', 'confirmed'])
        ).order_by(Booking.booking_date.desc()).limit(5).all()
        
        if not bookings:
            await update.message.reply_text(
                "📋 **Mes réservations**\n\n"
                "Vous n'avez aucune réservation active.",
                parse_mode="Markdown"
            )
            return
        
        message = "📋 **Mes réservations actives**\n\n"
        
        for booking in bookings:
            trip = booking.trip
            status_emoji = "⏳" if booking.status == 'pending' else "✅"
            payment_status = "💳 Paiement en attente" if booking.payment_status == 'pending' else "✅ Payé"
            
            message += (
                f"{status_emoji} **Réservation #{booking.id}**\n"
                f"📍 {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                f"💰 {booking.total_price} CHF\n"
                f"📊 Statut: {booking.status.title()}\n"
                f"💳 {payment_status}\n\n"
            )
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Erreur vérification statut réservations: {e}")
        await update.message.reply_text("❌ Erreur lors de la vérification. Veuillez réessayer.")

def register(application):
    """Enregistre les handlers de réservation"""
    application.add_handler(CommandHandler("reserver", book_trip))
    application.add_handler(CallbackQueryHandler(
        confirm_booking_callback,
        pattern='^confirm_booking_'
    ))
    application.add_handler(CallbackQueryHandler(
        lambda u, c: u.callback_query.edit_message_text("Réservation annulée."),
        pattern='^cancel_booking$'
    ))
    
    # Pour gérer les boutons book_{trip_id}
    application.add_handler(CallbackQueryHandler(
        lambda u, c: book_trip(u, c),
        pattern='^book_'
    ))
