import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, 
    CallbackQueryHandler, 
    ConversationHandler, 
    MessageHandler, 
    filters, 
    CallbackContext
)
from database.models import Booking, Trip, User
from database import get_db
import os

# Configuration du logger
logger = logging.getLogger(__name__)

DESCRIBE_ISSUE, UPLOAD_PROOF = range(2)
ADMIN_IDS = os.getenv('ADMIN_USER_IDS', '').split(',') if os.getenv('ADMIN_USER_IDS') else []

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

async def handle_dispute_description(update: Update, context: CallbackContext):
    """Traite la description du litige"""
    dispute_text = update.message.text
    booking_id = context.user_data.get('dispute_booking_id')
    
    # Vérifier que le booking_id existe
    if not booking_id:
        await update.message.reply_text(
            "⚠️ Erreur: Information de réservation manquante. Veuillez réessayer avec /litige."
        )
        return ConversationHandler.END
    
    try:
        db = get_db()
        booking = db.query(Booking).get(booking_id)
        
        if booking:
            # Marquer la réservation comme en litige
            booking.status = "dispute"
            db.commit()
            
            # Récupérer les informations du trajet
            trip = db.query(Trip).get(booking.trip_id)
            if not trip or getattr(trip, 'is_cancelled', False):
                await update.message.reply_text("Ce trajet est annulé ou introuvable.")
                return ConversationHandler.END
            
            passenger = db.query(User).get(booking.passenger_id)
            driver = db.query(User).filter_by(id=trip.driver_id).first()
            
            # Créer un message pour les admins avec plus d'informations
            admin_message = (
                f"⚠️ *Nouveau litige*\n\n"
                f"*Réservation*: #{booking_id}\n"
                f"*Trajet*: {trip.departure_city} → {trip.arrival_city}\n"
                f"*Date*: {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                f"*Passager*: {passenger.username if passenger.username else 'Anonyme'} (ID: {passenger.telegram_id})\n"
                f"*Conducteur*: {driver.username if driver and driver.username else 'Anonyme'}\n\n"
                f"*Description du litige*:\n{dispute_text}"
            )
            
            # Notifier les admins
            for admin_id in ADMIN_IDS:
                try:
                    keyboard = [
                        [
                            InlineKeyboardButton("✅ Rembourser", callback_data=f"refund_{booking_id}"),
                            InlineKeyboardButton("❌ Rejeter", callback_data=f"reject_dispute_{booking_id}")
                        ]
                    ]
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Erreur lors de la notification à l'admin {admin_id}: {str(e)}")
            
            # Notifier le conducteur qu'un litige a été ouvert
            if driver:
                try:
                    driver_message = (
                        f"⚠️ *Un litige a été ouvert* pour un trajet que vous avez effectué\n\n"
                        f"*Trajet*: {trip.departure_city} → {trip.arrival_city}\n"
                        f"*Date*: {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                        f"Un administrateur va examiner ce litige et vous contactera si nécessaire."
                    )
                    await context.bot.send_message(
                        chat_id=driver.telegram_id,
                        text=driver_message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Erreur lors de la notification au conducteur: {str(e)}")
        
        await update.message.reply_text(
            "✅ Votre litige a été enregistré. Un administrateur va examiner votre demande "
            "et vous contactera sous peu."
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du litige: {str(e)}")
        await update.message.reply_text(
            "❌ Une erreur est survenue lors de l'enregistrement du litige. "
            "Veuillez réessayer ou contacter le support."
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
    # Handler principal pour ouvrir un litige avec une commande
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("litige", open_dispute)],
        states={
            DESCRIBE_ISSUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dispute_description),
                CallbackQueryHandler(
                    lambda u, c: handle_dispute_selection(u, c),
                    pattern="^dispute_"
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        name="dispute_conversation",
        persistent=True,
        per_message=False
    )
    
    application.add_handler(conv_handler)
    
    # Handler pour les boutons de résolution de litige (admin)
    application.add_handler(CallbackQueryHandler(
        handle_refund_request,
        pattern="^refund_"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_reject_dispute,
        pattern="^reject_dispute_"
    ))
    
    logger.info("Handlers de litige enregistrés.")

# Fonctions supplémentaires pour gérer les callbacks

async def handle_dispute_selection(update: Update, context: CallbackContext):
    """Gère la sélection d'une réservation pour un litige"""
    query = update.callback_query
    await query.answer()
    
    booking_id = int(query.data.split("_")[1])
    context.user_data['dispute_booking_id'] = booking_id
    
    db = get_db()
    booking = db.query(Booking).get(booking_id)
    
    if booking:
        trip = db.query(Trip).get(booking.trip_id)
        if not trip or getattr(trip, 'is_cancelled', False):
            await update.message.reply_text("Ce trajet est annulé ou introuvable.")
            return ConversationHandler.END
        
        message_text = (
            f"Vous allez ouvrir un litige pour le trajet:\n\n"
            f"{trip.departure_city} → {trip.arrival_city}\n"
            f"Date: {trip.departure_time.strftime('%d/%m/%Y')}\n\n"
            f"Veuillez décrire le problème rencontré:"
        )
        await query.edit_message_text(message_text)
    else:
        await query.edit_message_text("❌ Réservation introuvable.")
        return ConversationHandler.END
    
    return DESCRIBE_ISSUE

async def handle_refund_request(update: Update, context: CallbackContext):
    """Gère la demande de remboursement par un admin"""
    query = update.callback_query
    await query.answer("Demande de remboursement en cours de traitement")
    
    booking_id = int(query.data.split("_")[1])
    
    try:
        db = get_db()
        booking = db.query(Booking).get(booking_id)
        
        if booking:
            # Marquer comme remboursé
            booking.status = "refunded"
            db.commit()
            
            # Informer le passager
            trip = db.query(Trip).get(booking.trip_id)
            passenger = db.query(User).get(booking.passenger_id)
            
            await context.bot.send_message(
                chat_id=passenger.telegram_id,
                text=f"✅ *Litige résolu*\n\n"
                     f"Votre litige concernant le trajet {trip.departure_city} → {trip.arrival_city} "
                     f"du {trip.departure_time.strftime('%d/%m/%Y')} a été accepté.\n\n"
                     f"Un remboursement de {booking.amount} CHF va être traité.",
                parse_mode="Markdown"
            )
            
            await query.edit_message_text(
                f"✅ Remboursement approuvé pour la réservation #{booking_id}.\n"
                f"Le passager a été informé."
            )
    except Exception as e:
        logger.error(f"Erreur lors du traitement du remboursement: {str(e)}")
        await query.edit_message_text(
            f"❌ Erreur lors du traitement du remboursement: {str(e)}"
        )

async def handle_reject_dispute(update: Update, context: CallbackContext):
    """Gère le rejet d'un litige par un admin"""
    query = update.callback_query
    await query.answer("Litige rejeté")
    
    booking_id = int(query.data.split("_")[1])
    
    try:
        db = get_db()
        booking = db.query(Booking).get(booking_id)
        
        if booking:
            # Marquer comme résolu sans remboursement
            booking.status = "completed"  # On considère que le trajet a bien eu lieu
            db.commit()
            
            # Informer le passager
            trip = db.query(Trip).get(booking.trip_id)
            passenger = db.query(User).get(booking.passenger_id)
            
            await context.bot.send_message(
                chat_id=passenger.telegram_id,
                text=f"ℹ️ *Décision sur votre litige*\n\n"
                     f"Après examen de votre litige concernant le trajet {trip.departure_city} → {trip.arrival_city} "
                     f"du {trip.departure_time.strftime('%d/%m/%Y')}, nous n'avons pas pu valider votre demande.\n\n"
                     f"Le statut du trajet reste 'complété'.",
                parse_mode="Markdown"
            )
            
            await query.edit_message_text(
                f"✅ Litige rejeté pour la réservation #{booking_id}.\n"
                f"Le passager a été informé."
            )
    except Exception as e:
        logger.error(f"Erreur lors du rejet du litige: {str(e)}")
        await query.edit_message_text(
            f"❌ Erreur lors du rejet du litige: {str(e)}"
        )
