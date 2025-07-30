#!/usr/bin/env python3
"""
Gestionnaire de remboursements automatiques PayPal
Gère les remboursements partiels lorsqu'un nouveau passager s'ajoute
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from database.models import Trip, Booking, User
from database import get_db
from paypal_utils import PayPalManager
from utils.swiss_pricing import calculate_price_per_passenger, round_to_nearest_0_05_up
import asyncio

logger = logging.getLogger(__name__)

class AutoRefundManager:
    """Gestionnaire pour les remboursements automatiques PayPal"""
    
    def __init__(self):
        self.paypal_manager = PayPalManager()
    
    async def handle_new_passenger_refund(self, trip_id: int, bot=None) -> bool:
        """
        Gère les remboursements automatiques lorsqu'un nouveau passager s'ajoute
        
        Args:
            trip_id: ID du trajet
            bot: Instance du bot Telegram pour les notifications
            
        Returns:
            True si les remboursements ont été traités avec succès
        """
        try:
            db = get_db()
            trip = db.query(Trip).filter(Trip.id == trip_id).first()
            
            if not trip:
                logger.error(f"Trajet {trip_id} non trouvé")
                return False
            
            # Récupérer toutes les réservations payées
            paid_bookings = db.query(Booking).filter(
                Booking.trip_id == trip_id,
                Booking.payment_status == 'completed'
            ).order_by(Booking.booking_date).all()
            
            if len(paid_bookings) < 2:
                # Pas besoin de remboursement avec moins de 2 passagers
                return True
            
            # Récupérer le prix total du trajet (stocké lors de la création)
            total_trip_price = trip.price_per_seat * trip.seats_available if hasattr(trip, 'total_trip_price') else None
            
            # Si pas de prix total stocké, utiliser le prix actuel * places
            if not total_trip_price:
                # Calculer le prix total théorique depuis la distance
                if hasattr(trip, 'total_distance') and trip.total_distance:
                    from handlers.trip_handlers import compute_price_auto
                    total_trip_price, _ = compute_price_auto(trip.departure_city, trip.arrival_city)
                else:
                    # Fallback : estimer depuis le prix par place
                    total_trip_price = trip.price_per_seat * len(paid_bookings)
            
            # Calculer le nouveau prix par passager
            current_passenger_count = len(paid_bookings)
            new_price_per_passenger = calculate_price_per_passenger(total_trip_price, current_passenger_count)
            
            logger.info(f"Trajet {trip_id}: {current_passenger_count} passagers, nouveau prix par passager: {new_price_per_passenger} CHF")
            
            # Identifier les passagers à rembourser
            refunds_to_process = []
            
            for booking in paid_bookings:
                amount_paid = float(booking.total_price)
                refund_amount = amount_paid - new_price_per_passenger
                
                if refund_amount > 0.05:  # Seuil minimum de remboursement
                    refunds_to_process.append({
                        'booking': booking,
                        'amount_paid': amount_paid,
                        'new_price': new_price_per_passenger,
                        'refund_amount': refund_amount
                    })
            
            # Traiter les remboursements
            refund_results = []
            for refund_info in refunds_to_process:
                success = await self._process_single_refund(refund_info, trip, bot)
                refund_results.append(success)
            
            # Mettre à jour les prix dans la base de données
            await self._update_booking_prices(trip_id, new_price_per_passenger)
            
            return all(refund_results)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des remboursements pour le trajet {trip_id}: {e}")
            return False
    
    async def _process_single_refund(self, refund_info: Dict, trip: Trip, bot=None) -> bool:
        """
        Traite un remboursement individuel
        
        Args:
            refund_info: Informations sur le remboursement
            trip: Objet Trip
            bot: Instance du bot pour notifications
            
        Returns:
            True si le remboursement a réussi
        """
        try:
            booking = refund_info['booking']
            refund_amount = refund_info['refund_amount']
            
            # Effectuer le remboursement via PayPal
            success, refund_id = await self._execute_paypal_refund(
                booking.paypal_payment_id,
                refund_amount
            )
            
            if success:
                # Mettre à jour la réservation
                db = get_db()
                booking.total_price = refund_info['new_price']
                booking.refund_id = refund_id
                booking.refund_amount = refund_amount
                booking.refund_date = datetime.utcnow()
                db.commit()
                
                # Notifier le passager
                if bot and booking.passenger and booking.passenger.telegram_id:
                    await self._notify_passenger_refund(
                        bot, booking.passenger.telegram_id, 
                        trip, refund_amount, refund_info['new_price']
                    )
                
                logger.info(f"Remboursement réussi: {refund_amount} CHF pour booking {booking.id}")
                return True
            else:
                logger.error(f"Échec du remboursement PayPal pour booking {booking.id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du remboursement individuel: {e}")
            return False
    
    async def _execute_paypal_refund(self, payment_id: str, refund_amount: float) -> Tuple[bool, Optional[str]]:
        """
        Exécute un remboursement via l'API PayPal
        
        Args:
            payment_id: ID du paiement PayPal original
            refund_amount: Montant à rembourser
            
        Returns:
            Tuple[success, refund_id]
        """
        try:
            # Utiliser l'API PayPal Refunds
            success, refund_id = self.paypal_manager.refund_payment(payment_id, refund_amount)
            return success, refund_id
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du remboursement PayPal: {e}")
            return False, None
    
    async def _notify_passenger_refund(self, bot, telegram_id: int, trip: Trip, refund_amount: float, new_price: float):
        """
        Notifie un passager de son remboursement automatique
        
        Args:
            bot: Instance du bot Telegram
            telegram_id: ID Telegram du passager
            trip: Objet Trip
            refund_amount: Montant remboursé
            new_price: Nouveau prix par passager
        """
        try:
            message = (
                f"💰 **Remboursement automatique**\n\n"
                f"Un nouveau passager s'est ajouté à votre trajet :\n"
                f"🚗 {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                f"✅ **Remboursement effectué :**\n"
                f"💵 Montant remboursé : {refund_amount:.2f} CHF\n"
                f"💰 Nouveau prix par passager : {new_price:.2f} CHF\n\n"
                f"Le remboursement sera visible sur votre compte PayPal sous 1-3 jours ouvrables.\n\n"
                f"Merci de partager vos trajets ! 🚗"
            )
            
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification de remboursement: {e}")
    
    async def _update_booking_prices(self, trip_id: int, new_price_per_passenger: float):
        """
        Met à jour les prix des réservations dans la base de données
        
        Args:
            trip_id: ID du trajet
            new_price_per_passenger: Nouveau prix par passager
        """
        try:
            db = get_db()
            
            # Mettre à jour toutes les réservations payées
            bookings = db.query(Booking).filter(
                Booking.trip_id == trip_id,
                Booking.payment_status == 'completed'
            ).all()
            
            for booking in bookings:
                if booking.total_price != new_price_per_passenger:
                    booking.total_price = new_price_per_passenger
            
            db.commit()
            logger.info(f"Prix des réservations mis à jour pour le trajet {trip_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des prix: {e}")

# Instance globale
auto_refund_manager = AutoRefundManager()

# Fonction d'aide pour utilisation dans le bot
async def trigger_automatic_refunds(trip_id: int, bot=None) -> bool:
    """
    Déclenche les remboursements automatiques pour un trajet
    
    Args:
        trip_id: ID du trajet
        bot: Instance du bot Telegram
        
    Returns:
        True si les remboursements ont été traités avec succès
    """
    return await auto_refund_manager.handle_new_passenger_refund(trip_id, bot)
