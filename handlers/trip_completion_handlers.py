"""
Handlers pour la gestion de la fin des trajets et de leur validation
"""
import logging
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, ConversationHandler, CommandHandler
from database.models import Booking, Trip, User
from database import get_db

# Configuration du logger
logger = logging.getLogger(__name__)

async def check_completed_trips(context: CallbackContext):
    """
    Vérification quotidienne des trajets terminés (date passée) 
    et envoi de messages aux passagers pour validation
    """
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    try:
        db = get_db()
        # Récupérer les trajets qui se sont terminés hier
        completed_trips = db.query(Trip).filter(
            Trip.departure_time.between(yesterday - timedelta(hours=6), yesterday + timedelta(hours=18)),
            Trip.is_published == True,
            (Trip.is_cancelled == False) | (Trip.is_cancelled.is_(None))
        ).all()
        
        logger.info(f"Vérification des trajets terminés: {len(completed_trips)} trajets trouvés")
        
        for trip in completed_trips:
            if getattr(trip, 'is_cancelled', False):
                continue
            
            # Récupérer toutes les réservations confirmées pour ce trajet
            bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.status == "confirmed"  # Uniquement les réservations confirmées
            ).all()
            
            driver = db.query(User).get(trip.driver_id)
            if not driver:
                logger.error(f"Conducteur introuvable pour le trajet {trip.id}")
                continue
            
            for booking in bookings:
                try:
                    passenger = db.query(User).get(booking.passenger_id)
                    if not passenger:
                        logger.error(f"Passager introuvable pour la réservation {booking.id}")
                        continue
                    
                    # Créer les boutons pour la réponse
                    keyboard = [
                        [
                            InlineKeyboardButton("✅ Oui", callback_data=f"trip_completed_yes:{booking.id}"),
                            InlineKeyboardButton("❌ Non", callback_data=f"trip_completed_no:{booking.id}")
                        ]
                    ]
                    
                    # Envoyer le message au passager
                    driver_name = driver.username if driver.username else "le conducteur"
                    await context.bot.send_message(
                        chat_id=passenger.telegram_id,
                        text=f"🚗 *Validation du trajet*\n\n"
                             f"Avez-vous effectué ce trajet avec {driver_name} ?\n\n"
                             f"*Trajet* : {trip.departure_city} → {trip.arrival_city}\n"
                             f"*Date* : {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                    
                    logger.info(f"Message de validation envoyé au passager {passenger.telegram_id} pour la réservation {booking.id}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi du message de validation: {str(e)}")
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des trajets terminés: {str(e)}")

async def handle_trip_completed_response(update: Update, context: CallbackContext):
    """Gère la réponse du passager à la question de validation du trajet"""
    query = update.callback_query
    await query.answer()
    
    # Extraire les données du callback
    data = query.data.split(":")
    response_type = data[0]  # trip_completed_yes ou trip_completed_no
    booking_id = int(data[1])
    
    try:
        db = get_db()
        booking = db.query(Booking).get(booking_id)
        
        if not booking:
            await query.edit_message_text(
                "❌ Réservation introuvable. Veuillez contacter le support."
            )
            return
        
        trip = db.query(Trip).get(booking.trip_id)
        passenger = db.query(User).get(booking.passenger_id)
        driver = db.query(User).get(trip.driver_id)
        
        if response_type == "trip_completed_yes":
            # Le passager confirme que le trajet a eu lieu
            booking.status = "completed"
            db.commit()
            
            # Mise à jour des statistiques du conducteur
            driver.trips_completed += 1
            db.commit()
            
            await query.edit_message_text(
                "✅ Merci pour votre confirmation! Le trajet a été marqué comme terminé."
            )
            
            # Notifier le conducteur
            try:
                await context.bot.send_message(
                    chat_id=driver.telegram_id,
                    text=f"✅ Le passager {passenger.username} a confirmé que le trajet "
                         f"{trip.departure_city} → {trip.arrival_city} du "
                         f"{trip.departure_time.strftime('%d/%m/%Y')} a bien eu lieu."
                )
            except Exception as e:
                logger.error(f"Erreur lors de la notification au conducteur: {str(e)}")
            
        elif response_type == "trip_completed_no":
            # Le passager indique que le trajet n'a pas eu lieu -> litige
            await query.edit_message_text(
                "⚠️ Vous avez indiqué que le trajet n'a pas eu lieu.\n\n"
                "Veuillez nous expliquer brièvement pourquoi (annulation, non-présentation du conducteur, etc.):",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Annuler", callback_data=f"cancel_dispute:{booking_id}")
                ]])
            )
            
            # Stocker les informations nécessaires pour le litige
            context.user_data['dispute_booking_id'] = booking_id
            
            # Transition vers le gestionnaire de litiges
            from handlers.dispute_handlers import DESCRIBE_ISSUE
            return DESCRIBE_ISSUE
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la réponse de validation: {str(e)}")
        await query.edit_message_text(
            "❌ Une erreur est survenue. Veuillez réessayer ou contacter le support."
        )
    
    return ConversationHandler.END

async def cancel_dispute(update: Update, context: CallbackContext):
    """Annule le processus de litige"""
    query = update.callback_query
    await query.answer()
    
    booking_id = int(query.data.split(":")[1])
    
    await query.edit_message_text(
        "❌ Processus de litige annulé.\n\n"
        "Si vous rencontrez un problème, vous pouvez toujours ouvrir un litige "
        "avec la commande /litige."
    )
    
    return ConversationHandler.END

def register(application):
    """Enregistre les handlers pour la gestion de la fin des trajets"""
    # Job quotidien pour vérifier les trajets terminés (à 9h du matin)
    job_queue = application.job_queue
    if job_queue is not None:
        job_queue.run_daily(
            check_completed_trips,
            time=time(hour=9, minute=0)
        )
        logger.info("Job quotidien pour la vérification des trajets terminés configuré")
    else:
        logger.warning("JobQueue non disponible. Pour utiliser les jobs planifiés, installez python-telegram-bot[job-queue]")
        # Exécuter une fois au démarrage, en tant qu'alternative
        check_completed_trips(application)
    
    # Handler pour gérer les réponses aux messages de validation
    application.add_handler(
        CallbackQueryHandler(
            handle_trip_completed_response,
            pattern="^trip_completed_yes:|^trip_completed_no:"
        )
    )
    
    # Handler pour annuler un litige
    application.add_handler(
        CallbackQueryHandler(
            cancel_dispute,
            pattern="^cancel_dispute:"
        )
    )
    
    logger.info("Handlers de gestion de fin de trajet enregistrés.")
