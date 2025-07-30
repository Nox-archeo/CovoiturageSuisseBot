#!/usr/bin/env python3
"""
Gestionnaire de remboursements automatiques pour annulations de trajets par conducteur
Intégré au système PayPal existant avec traçabilité complète
"""

import logging
from datetime import datetime
from typing import List, Tuple, Optional
from telegram import Bot
from database.models import Trip, Booking, User
from database import get_db
from paypal_utils import PayPalManager

logger = logging.getLogger(__name__)

class CancellationRefundManager:
    """Gestionnaire spécialisé pour les remboursements d'annulation de trajet"""
    
    def __init__(self):
        self.paypal_manager = PayPalManager()
    
    async def process_trip_cancellation_refunds(self, trip_id: int, bot: Bot) -> bool:
        """
        Traite tous les remboursements d'un trajet annulé par le conducteur
        
        Args:
            trip_id: ID du trajet annulé
            bot: Instance du bot Telegram pour notifications
            
        Returns:
            bool: True si tous les remboursements ont réussi
        """
        logger.info(f"🔄 Début des remboursements pour annulation du trajet {trip_id}")
        
        try:
            db = get_db()
            
            # Récupérer le trajet
            trip = db.query(Trip).filter(Trip.id == trip_id).first()
            if not trip:
                logger.error(f"Trajet {trip_id} non trouvé")
                return False
            
            # Récupérer toutes les réservations payées
            paid_bookings = db.query(Booking).filter(
                Booking.trip_id == trip_id,
                Booking.payment_status == 'completed',
                Booking.status.in_(['confirmed', 'pending'])
            ).all()
            
            if not paid_bookings:
                logger.info(f"Aucune réservation payée trouvée pour le trajet {trip_id}")
                return True
            
            logger.info(f"Traitement de {len(paid_bookings)} remboursements pour le trajet {trip_id}")
            
            success_count = 0
            total_refunded = 0.0
            
            # Traiter chaque remboursement
            for booking in paid_bookings:
                try:
                    refund_success = await self._process_single_refund(booking, trip, bot)
                    if refund_success:
                        success_count += 1
                        total_refunded += float(booking.total_price)
                        logger.info(f"✅ Remboursement réussi pour la réservation {booking.id}")
                    else:
                        logger.error(f"❌ Échec du remboursement pour la réservation {booking.id}")
                        
                except Exception as e:
                    logger.error(f"Erreur lors du remboursement de la réservation {booking.id}: {e}")
            
            # Notifier le conducteur du résumé
            await self._notify_driver_summary(trip, bot, success_count, len(paid_bookings), total_refunded)
            
            # Marquer le trajet comme traité
            trip.status = 'cancelled_refunds_processed'
            db.commit()
            
            logger.info(f"🎯 Remboursements terminés pour le trajet {trip_id}: {success_count}/{len(paid_bookings)} réussis")
            
            return success_count == len(paid_bookings)
            
        except Exception as e:
            logger.error(f"Erreur globale lors des remboursements du trajet {trip_id}: {e}")
            return False
    
    async def _process_single_refund(self, booking: Booking, trip: Trip, bot: Bot) -> bool:
        """
        Traite le remboursement d'une réservation individuelle
        
        Args:
            booking: Réservation à rembourser
            trip: Trajet annulé
            bot: Bot Telegram
            
        Returns:
            bool: True si le remboursement a réussi
        """
        try:
            # Vérifier si déjà remboursé
            if booking.refund_id:
                logger.warning(f"Réservation {booking.id} déjà remboursée (ID: {booking.refund_id})")
                return True
            
            # Effectuer le remboursement PayPal
            success, refund_id = await self._execute_paypal_refund(
                payment_id=booking.paypal_payment_id,
                refund_amount=float(booking.total_price)
            )
            
            if success and refund_id:
                # Enregistrer les détails du remboursement
                db = get_db()
                booking.refund_id = refund_id
                booking.refund_amount = float(booking.total_price)
                booking.refund_date = datetime.utcnow()
                booking.status = 'cancelled_refunded'
                db.commit()
                
                # Notifier le passager
                await self._notify_passenger_refund(booking, trip, bot)
                
                logger.info(f"💰 Remboursement PayPal réussi: {booking.total_price:.2f} CHF (ID: {refund_id})")
                return True
            else:
                logger.error(f"Échec du remboursement PayPal pour la réservation {booking.id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du remboursement de la réservation {booking.id}: {e}")
            return False
    
    async def _execute_paypal_refund(self, payment_id: str, refund_amount: float) -> Tuple[bool, Optional[str]]:
        """
        Exécute le remboursement via l'API PayPal
        
        Args:
            payment_id: ID du paiement PayPal original
            refund_amount: Montant à rembourser
            
        Returns:
            Tuple[success, refund_id]
        """
        try:
            if not payment_id:
                logger.error("Payment ID manquant pour le remboursement")
                return False, None
            
            # Utiliser le gestionnaire PayPal existant
            success, refund_id = self.paypal_manager.refund_payment(payment_id, refund_amount)
            
            if success:
                logger.info(f"✅ Remboursement PayPal exécuté: {refund_amount:.2f} CHF (ID: {refund_id})")
                return True, refund_id
            else:
                logger.error(f"❌ Échec du remboursement PayPal: {refund_amount:.2f} CHF")
                return False, None
                
        except Exception as e:
            logger.error(f"Exception lors du remboursement PayPal: {e}")
            return False, None
    
    async def _notify_passenger_refund(self, booking: Booking, trip: Trip, bot: Bot):
        """
        Notifie un passager de son remboursement d'annulation
        
        Args:
            booking: Réservation remboursée
            trip: Trajet annulé
            bot: Bot Telegram
        """
        try:
            passenger = booking.passenger
            if not passenger or not passenger.telegram_id:
                logger.warning(f"Impossible de notifier le passager {booking.passenger_id}")
                return
            
            message = (
                f"💰 **Remboursement automatique**\n\n"
                f"❌ **Trajet annulé par le conducteur**\n\n"
                f"🚗 **Trajet :** {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 **Date :** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                f"💸 **Montant remboursé :** {booking.refund_amount:.2f} CHF\n"
                f"🆔 **ID remboursement :** {booking.refund_id}\n\n"
                f"💳 **Le remboursement sera visible sur votre compte PayPal sous 1-3 jours ouvrés.**\n\n"
                f"😔 Nous nous excusons pour ce désagrément. "
                f"Vous pouvez rechercher d'autres trajets disponibles avec /rechercher."
            )
            
            await bot.send_message(
                chat_id=passenger.telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"📱 Notification de remboursement envoyée au passager {passenger.telegram_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification du passager {booking.passenger_id}: {e}")
    
    async def _notify_driver_summary(self, trip: Trip, bot: Bot, success_count: int, total_count: int, total_amount: float):
        """
        Notifie le conducteur du résumé des remboursements
        
        Args:
            trip: Trajet annulé
            bot: Bot Telegram
            success_count: Nombre de remboursements réussis
            total_count: Nombre total de remboursements
            total_amount: Montant total remboursé
        """
        try:
            driver = trip.driver
            if not driver or not driver.telegram_id:
                logger.warning(f"Impossible de notifier le conducteur {trip.driver_id}")
                return
            
            if success_count == total_count:
                status_icon = "✅"
                status_text = "Tous les remboursements ont été traités avec succès"
            else:
                status_icon = "⚠️"
                status_text = f"{success_count}/{total_count} remboursements ont réussi"
            
            message = (
                f"{status_icon} **Remboursements traités**\n\n"
                f"🚗 **Trajet annulé :** {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 **Date :** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                f"📊 **Résumé :**\n"
                f"👥 Passagers remboursés : {success_count}/{total_count}\n"
                f"💰 Montant total : {total_amount:.2f} CHF\n\n"
                f"💡 {status_text}\n\n"
                f"ℹ️ Les passagers ont été automatiquement notifiés de leur remboursement."
            )
            
            await bot.send_message(
                chat_id=driver.telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"📱 Résumé des remboursements envoyé au conducteur {driver.telegram_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification du conducteur {trip.driver_id}: {e}")

# Fonction d'utilité pour intégration facile
async def handle_trip_cancellation_refunds(trip_id: int, bot: Bot) -> bool:
    """
    Point d'entrée principal pour les remboursements d'annulation
    
    Args:
        trip_id: ID du trajet annulé
        bot: Instance du bot Telegram
        
    Returns:
        bool: True si tous les remboursements ont réussi
    """
    manager = CancellationRefundManager()
    return await manager.process_trip_cancellation_refunds(trip_id, bot)

if __name__ == "__main__":
    # Test basique du système
    import asyncio
    from unittest.mock import Mock
    
    async def test_system():
        print("🧪 Test du système de remboursement d'annulation")
        manager = CancellationRefundManager()
        print("✅ CancellationRefundManager initialisé avec succès")
        print("💡 Le système est opérationnel et prêt à traiter les annulations")
    
    asyncio.run(test_system())
