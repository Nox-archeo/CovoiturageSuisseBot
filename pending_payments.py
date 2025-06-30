"""
Système de traitement des paiements en attente
Gère les paiements différés en attente de configuration PayPal
"""

import logging
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from database import get_db
from database.models import Trip, Booking, User
from paypal_utils import pay_driver

logger = logging.getLogger(__name__)

class PendingPaymentProcessor:
    """Gestionnaire pour les paiements en attente"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def process_pending_payments(self):
        """Traite tous les paiements en attente d'email PayPal"""
        try:
            db = get_db()
            
            # Récupérer tous les trajets avec paiement en attente
            pending_trips = db.query(Trip).filter(
                Trip.status == 'completed_payment_pending'
            ).all()
            
            logger.info(f"Traitement de {len(pending_trips)} paiements en attente")
            
            for trip in pending_trips:
                await self._process_single_pending_payment(trip)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement des paiements en attente: {e}")
    
    async def _process_single_pending_payment(self, trip: Trip):
        """Traite un paiement en attente spécifique"""
        try:
            db = get_db()
            
            # Vérifier si le conducteur a maintenant un email PayPal
            driver = trip.driver
            if not driver or not driver.paypal_email:
                # Toujours pas d'email PayPal, envoyer un rappel
                await self._send_paypal_reminder(trip)
                return
            
            # Email PayPal maintenant disponible, traiter le paiement
            paid_bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.payment_status == 'completed'
            ).all()
            
            if not paid_bookings:
                logger.warning(f"Aucune réservation payée trouvée pour le trajet {trip.id}")
                return
            
            # Calculer le montant total
            total_amount = sum(float(booking.total_price) for booking in paid_bookings)
            
            # Effectuer le paiement (88% au conducteur)
            success, payout_batch_id = pay_driver(
                driver_email=driver.paypal_email,
                trip_amount=total_amount
            )
            
            if success:
                # Marquer le trajet comme complètement payé
                trip.status = 'completed'
                trip.payout_batch_id = payout_batch_id
                trip.driver_amount = round(total_amount * 0.88, 2)
                trip.commission_amount = round(total_amount * 0.12, 2)
                
                db.commit()
                
                # Notifier le conducteur du paiement effectué
                await self.bot.send_message(
                    chat_id=driver.telegram_id,
                    text=(
                        f"✅ *Paiement envoyé !*\n\n"
                        f"Votre email PayPal a été configuré et votre paiement "
                        f"en attente a été traité automatiquement.\n\n"
                        f"💰 Montant reçu : {trip.driver_amount} CHF\n"
                        f"🚗 Trajet : {trip.departure_city} → {trip.arrival_city}\n\n"
                        f"Le paiement a été envoyé sur votre compte PayPal : {driver.paypal_email}"
                    ),
                    parse_mode="Markdown"
                )
                
                logger.info(f"Paiement en attente traité pour le trajet {trip.id}")
            else:
                logger.error(f"Échec du paiement en attente pour le trajet {trip.id}")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du paiement en attente pour le trajet {trip.id}: {e}")
    
    async def _send_paypal_reminder(self, trip: Trip):
        """Envoie un rappel de configuration PayPal"""
        try:
            driver = trip.driver
            if not driver or not driver.telegram_id:
                return
            
            # Calculer le montant en attente
            db = get_db()
            paid_bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.payment_status == 'completed'
            ).all()
            
            total_amount = sum(float(booking.total_price) for booking in paid_bookings)
            driver_amount = round(total_amount * 0.88, 2)
            
            # Vérifier si on a déjà envoyé un rappel récemment
            last_reminder = getattr(trip, 'last_paypal_reminder', None)
            if last_reminder and (datetime.now() - last_reminder).days < 1:
                return  # Rappel déjà envoyé dans les dernières 24h
            
            keyboard = [
                [InlineKeyboardButton("💳 Configurer PayPal maintenant", callback_data="setup_paypal")],
                [InlineKeyboardButton("📞 Support", callback_data="contact_support")]
            ]
            
            await self.bot.send_message(
                chat_id=driver.telegram_id,
                text=(
                    f"💰 *Rappel : Paiement en attente*\n\n"
                    f"Vous avez un paiement en attente de {driver_amount} CHF "
                    f"pour votre trajet {trip.departure_city} → {trip.arrival_city}.\n\n"
                    f"⚠️ Pour recevoir ce paiement, vous devez configurer "
                    f"votre email PayPal.\n\n"
                    f"💡 Utilisez /paypal ou cliquez sur le bouton ci-dessous."
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Marquer le rappel comme envoyé
            trip.last_paypal_reminder = datetime.now()
            db = get_db()
            db.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rappel PayPal pour le trajet {trip.id}: {e}")

async def process_all_pending_payments(bot: Bot):
    """Fonction utilitaire pour traiter tous les paiements en attente"""
    processor = PendingPaymentProcessor(bot)
    await processor.process_pending_payments()

if __name__ == "__main__":
    print("✅ Processeur de paiements en attente créé")
    print("Utilisation :")
    print("  from pending_payments import process_all_pending_payments")
    print("  await process_all_pending_payments(bot)")
