"""
Système de confirmation automatique des trajets
Gère la confirmation des trajets et le déclenchement des paiements
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Trip, Booking, User
from database import get_db
from paypal_utils import pay_driver

logger = logging.getLogger(__name__)

class TripConfirmationSystem:
    """Système pour gérer la confirmation des trajets et les paiements automatiques"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_trip_completion_reminders(self):
        """Envoie des rappels pour confirmer les trajets terminés"""
        try:
            db = get_db()
            
            # Récupérer les trajets qui se sont terminés dans les dernières 24h
            yesterday = datetime.now() - timedelta(days=1)
            recent_trips = db.query(Trip).filter(
                Trip.departure_time < datetime.now(),
                Trip.departure_time > yesterday,
                Trip.status != 'completed',
                Trip.status != 'cancelled'
            ).all()
            
            for trip in recent_trips:
                await self._send_completion_reminder(trip)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des rappels: {e}")
    
    async def _send_completion_reminder(self, trip: Trip):
        """Envoie un rappel de confirmation pour un trajet spécifique"""
        try:
            # Récupérer les réservations payées
            db = get_db()
            paid_bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.payment_status == 'completed'
            ).all()
            
            if not paid_bookings:
                return  # Pas de réservations payées
            
            # Message au conducteur pour confirmation OBLIGATOIRE
            driver = trip.driver
            if driver and driver.telegram_id:
                keyboard = [
                    [InlineKeyboardButton("✅ Confirmer le trajet", callback_data=f"confirm_trip:{trip.id}")],
                    [InlineKeyboardButton("❌ Signaler un problème", callback_data=f"report_issue:{trip.id}")]
                ]
                
                total_amount = sum(float(b.total_price) for b in paid_bookings)
                driver_amount = round(total_amount * 0.88, 2)
                
                message = (
                    f"🚗 *Confirmation de trajet REQUISE*\n\n"
                    f"Votre trajet {trip.departure_city} → {trip.arrival_city} "
                    f"du {trip.departure_time.strftime('%d/%m/%Y à %H:%M')} s'est terminé.\n\n"
                    f"👥 {len(paid_bookings)} passager(s) ont payé\n"
                    f"💰 Montant total: {total_amount} CHF\n"
                    f"💵 Votre part (88%): {driver_amount} CHF\n\n"
                    f"⚠️ **IMPORTANT** : Vous devez confirmer que le trajet s'est bien déroulé "
                    f"pour recevoir votre paiement automatiquement."
                )
                
                await self.bot.send_message(
                    chat_id=driver.telegram_id,
                    text=message,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            # Messages aux passagers
            for booking in paid_bookings:
                passenger = booking.passenger
                if passenger and passenger.telegram_id:
                    keyboard = [
                        [InlineKeyboardButton("✅ Trajet OK", callback_data=f"rate_trip:{trip.id}:5")],
                        [InlineKeyboardButton("👍 Trajet correct", callback_data=f"rate_trip:{trip.id}:4")],
                        [InlineKeyboardButton("👎 Problème", callback_data=f"report_trip_issue:{trip.id}")]
                    ]
                    
                    message = (
                        f"🚗 *Comment s'est passé votre trajet ?*\n\n"
                        f"Trajet: {trip.departure_city} → {trip.arrival_city}\n"
                        f"Date: {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                        f"Conducteur: {driver.first_name if driver else 'Inconnu'}\n\n"
                        f"Votre retour nous aide à améliorer le service !"
                    )
                    
                    await self.bot.send_message(
                        chat_id=passenger.telegram_id,
                        text=message,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    
        except Exception as e:
            logger.error(f"Erreur envoi rappel trajet {trip.id}: {e}")
    
    async def handle_trip_confirmation(self, trip_id: int, confirmed_by_driver: bool = False, confirmed_by_passenger: bool = False):
        """Gère la confirmation d'un trajet"""
        try:
            db = get_db()
            trip = db.query(Trip).filter(Trip.id == trip_id).first()
            
            if not trip:
                return False
            
            # Marquer la confirmation
            if confirmed_by_driver:
                trip.confirmed_by_driver = True
            if confirmed_by_passenger:
                trip.confirmed_by_passengers = True
            
            db.commit()
            
            # Si confirmé par le conducteur ET au moins un passager, déclencher le paiement
            if trip.confirmed_by_driver and self._has_passenger_confirmations(trip_id):
                await self._trigger_driver_payment(trip)
                
            return True
            
        except Exception as e:
            logger.error(f"Erreur confirmation trajet {trip_id}: {e}")
            return False
    
    def _has_passenger_confirmations(self, trip_id: int) -> bool:
        """Vérifie si au moins un passager a confirmé le trajet"""
        try:
            db = get_db()
            
            # Vérifier s'il y a des réservations confirmées avec payment_status = 'completed'
            confirmed_bookings = db.query(Booking).filter(
                Booking.trip_id == trip_id,
                Booking.payment_status == 'completed',
                Booking.status == 'completed'  # Le passager a confirmé via trip_completion_handlers
            ).count()
            
            return confirmed_bookings > 0
            
        except Exception as e:
            logger.error(f"Erreur vérification confirmations passagers: {e}")
            return False
    
    async def _trigger_driver_payment(self, trip: Trip):
        """Déclenche le paiement au conducteur"""
        try:
            if trip.status == 'completed':
                return  # Déjà payé
            
            db = get_db()
            
            # Récupérer les réservations payées
            paid_bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.payment_status == 'completed'
            ).all()
            
            if not paid_bookings:
                return
            
            driver = trip.driver
            if not driver or not driver.paypal_email:
                # Email PayPal manquant - Notifier le conducteur
                if driver and driver.telegram_id:
                    keyboard = [
                        [InlineKeyboardButton("💳 Configurer PayPal", callback_data="setup_paypal")],
                        [InlineKeyboardButton("ℹ️ Plus d'infos", callback_data="paypal_info")]
                    ]
                    
                    await self.bot.send_message(
                        chat_id=driver.telegram_id,
                        text=(
                            "⚠️ *Paiement bloqué - Email PayPal manquant*\n\n"
                            f"Votre trajet {trip.departure_city} → {trip.arrival_city} "
                            f"a été confirmé, mais nous ne pouvons pas vous envoyer "
                            f"votre paiement car aucun email PayPal n'est configuré.\n\n"
                            f"💰 Montant en attente : {total_amount} CHF\n"
                            f"💵 Votre part (88%) : {round(total_amount * 0.88, 2)} CHF\n\n"
                            f"🔧 Configurez votre email PayPal maintenant pour recevoir "
                            f"votre paiement automatiquement."
                        ),
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                
                # Marquer le trajet comme complété mais sans paiement
                trip.status = 'completed_payment_pending'
                
                # Marquer les réservations comme complétées
                for booking in paid_bookings:
                    booking.status = 'completed'
                
                db.commit()
                
                logger.warning(f"Paiement bloqué pour le trajet {trip.id} - Email PayPal manquant pour le conducteur {trip.driver_id}")
                return
            
            # Calculer le montant total
            total_amount = sum(float(booking.total_price) for booking in paid_bookings)
            
            # Effectuer le paiement (88% au conducteur)
            success, payout_batch_id = pay_driver(
                driver_email=driver.paypal_email,
                trip_amount=total_amount
            )
            
            if success:
                # Marquer le trajet comme complété
                trip.status = 'completed'
                trip.payout_batch_id = payout_batch_id
                trip.driver_amount = round(total_amount * 0.88, 2)
                trip.commission_amount = round(total_amount * 0.12, 2)
                
                # Marquer les réservations comme complétées
                for booking in paid_bookings:
                    booking.status = 'completed'
                
                db.commit()
                
                # Notifier le conducteur
                await self.bot.send_message(
                    chat_id=driver.telegram_id,
                    text=(
                        f"💰 *Paiement envoyé !*\n\n"
                        f"Montant reçu: {trip.driver_amount} CHF\n"
                        f"Trajet: {trip.departure_city} → {trip.arrival_city}\n\n"
                        f"Le paiement a été envoyé sur votre compte PayPal."
                    ),
                    parse_mode="Markdown"
                )
                
                # Notifier les passagers
                for booking in paid_bookings:
                    passenger = booking.passenger
                    if passenger and passenger.telegram_id:
                        await self.bot.send_message(
                            chat_id=passenger.telegram_id,
                            text=(
                                f"✅ *Trajet confirmé !*\n\n"
                                f"Le conducteur a reçu son paiement.\n"
                                f"Merci d'avoir utilisé notre service !"
                            ),
                            parse_mode="Markdown"
                        )
                
                logger.info(f"Paiement automatique effectué pour le trajet {trip.id}")
                
        except Exception as e:
            logger.error(f"Erreur paiement automatique trajet {trip.id}: {e}")

# Callbacks pour les boutons de confirmation
async def handle_confirm_trip_callback(update, context):
    """Callback pour la confirmation de trajet par le conducteur"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[1])
    
    # Utiliser le système de confirmation
    system = TripConfirmationSystem(context.bot)
    success = await system.handle_trip_confirmation(trip_id, confirmed_by_driver=True)
    
    if success:
        await query.edit_message_text(
            "✅ *Trajet confirmé !*\n\n"
            "Votre paiement sera traité automatiquement.",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Erreur lors de la confirmation. Veuillez réessayer."
        )

async def handle_rate_trip_callback(update, context):
    """Callback pour l'évaluation de trajet par le passager"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(":")
    trip_id = int(data_parts[1])
    rating = int(data_parts[2]) if len(data_parts) > 2 else 5
    
    # Enregistrer l'évaluation (à implémenter selon vos besoins)
    # ...
    
    await query.edit_message_text(
        f"✅ *Merci pour votre retour !*\n\n"
        f"Note attribuée: {rating}/5 ⭐\n"
        f"Cela nous aide à améliorer le service.",
        parse_mode="Markdown"
    )
