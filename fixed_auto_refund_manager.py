#!/usr/bin/env python3
"""
Système de remboursement automatique CORRIGÉ
Gère les adresses PayPal des passagers et les vrais remboursements
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

class FixedAutoRefundManager:
    """Gestionnaire CORRIGÉ pour les remboursements automatiques"""
    
    def __init__(self):
        self.paypal_manager = PayPalManager()
    
    async def handle_new_passenger_refund(self, trip_id: int, bot=None) -> bool:
        """
        Gère les remboursements automatiques lorsqu'un nouveau passager s'ajoute
        AVEC vérification des adresses PayPal
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
                return True  # Pas besoin de remboursement avec moins de 2 passagers
            
            # Calculer le nouveau prix par passager
            total_trip_price = self._calculate_total_trip_price(trip)
            current_passenger_count = len(paid_bookings)
            new_price_per_passenger = calculate_price_per_passenger(total_trip_price, current_passenger_count)
            
            logger.info(f"Trajet {trip_id}: {current_passenger_count} passagers, nouveau prix: {new_price_per_passenger} CHF")
            
            # Identifier les passagers à rembourser et vérifier leurs adresses PayPal
            refunds_to_process = []
            passengers_without_paypal = []
            
            for booking in paid_bookings:
                passenger = db.query(User).filter(User.id == booking.passenger_id).first()
                amount_paid = float(booking.total_price)
                refund_amount = amount_paid - new_price_per_passenger
                
                if refund_amount > 0.05:  # Seuil minimum de remboursement
                    if passenger and passenger.paypal_email:
                        # Passager avec adresse PayPal -> remboursement possible
                        refunds_to_process.append({
                            'booking': booking,
                            'passenger': passenger,
                            'amount_paid': amount_paid,
                            'new_price': new_price_per_passenger,
                            'refund_amount': refund_amount
                        })
                    else:
                        # Passager SANS adresse PayPal -> demander l'adresse
                        passengers_without_paypal.append({
                            'booking': booking,
                            'passenger': passenger,
                            'refund_amount': refund_amount
                        })
            
            # Demander les adresses PayPal manquantes
            if passengers_without_paypal:
                await self._request_paypal_addresses(passengers_without_paypal, bot)
                # Note: Les remboursements seront traités une fois les adresses fournies
                return True
            
            # Traiter les remboursements pour ceux qui ont une adresse PayPal
            refund_results = []
            for refund_info in refunds_to_process:
                success = await self._process_single_refund_to_paypal(refund_info, trip, bot)
                refund_results.append(success)
            
            # Mettre à jour les prix dans la base de données
            await self._update_booking_prices(trip_id, new_price_per_passenger)
            
            return all(refund_results)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des remboursements pour le trajet {trip_id}: {e}")
            return False
    
    async def _request_paypal_addresses(self, passengers_without_paypal: List[Dict], bot=None):
        """
        Demande aux passagers leur adresse PayPal pour remboursement
        """
        for passenger_info in passengers_without_paypal:
            passenger = passenger_info['passenger']
            refund_amount = passenger_info['refund_amount']
            
            if bot and passenger and passenger.telegram_id:
                try:
                    message = (
                        f"💰 **Remboursement en attente !**\n\n"
                        f"Suite à l'ajout d'un nouveau passager sur votre trajet, "
                        f"vous avez droit à un remboursement de **{refund_amount:.2f} CHF**.\n\n"
                        f"🚨 **Action requise :**\n"
                        f"Pour recevoir votre remboursement, vous devez nous fournir "
                        f"votre adresse email PayPal.\n\n"
                        f"📧 Cliquez sur le bouton ci-dessous pour configurer votre PayPal :"
                    )
                    
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    keyboard = [
                        [InlineKeyboardButton("📧 Entrer mon email PayPal", callback_data="paypal_input_start")],
                        [InlineKeyboardButton("ℹ️ Pourquoi PayPal ?", callback_data="paypal_info")]
                    ]
                    
                    await bot.send_message(
                        chat_id=passenger.telegram_id,
                        text=message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                    
                    logger.info(f"Demande d'adresse PayPal envoyée au passager {passenger.id}")
                    
                except Exception as e:
                    logger.error(f"Erreur envoi demande PayPal au passager {passenger.id}: {e}")
    
    async def _process_single_refund_to_paypal(self, refund_info: Dict, trip: Trip, bot=None) -> bool:
        """
        Traite un remboursement individuel via PayPal Payout
        """
        try:
            booking = refund_info['booking']
            passenger = refund_info['passenger']
            refund_amount = refund_info['refund_amount']
            
            # Effectuer le paiement PayPal vers l'adresse du passager
            success, payout_details = self.paypal_manager.send_payout(
                recipient_email=passenger.paypal_email,
                amount=refund_amount,
                currency="CHF",
                description=f"Remboursement covoiturage - Nouveau passager ajouté"
            )
            
            if success:
                # Mettre à jour la réservation
                db = get_db()
                booking.total_price = refund_info['new_price']
                booking.refund_id = payout_details.get('batch_id')
                booking.refund_amount = refund_amount
                booking.refund_date = datetime.utcnow()
                db.commit()
                
                # Notifier le passager
                if bot and passenger.telegram_id:
                    await self._notify_passenger_refund_success(
                        bot, passenger.telegram_id, trip, refund_amount, refund_info['new_price']
                    )
                
                logger.info(f"Remboursement PayPal réussi: {refund_amount} CHF vers {passenger.paypal_email}")
                return True
            else:
                logger.error(f"Échec du paiement PayPal pour booking {booking.id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du remboursement PayPal: {e}")
            return False
    
    async def _notify_passenger_refund_success(self, bot, telegram_id: int, trip: Trip, refund_amount: float, new_price: float):
        """
        Notifie le passager que son remboursement a été envoyé
        """
        try:
            message = (
                f"✅ **Remboursement envoyé !**\n\n"
                f"💰 **Montant :** {refund_amount:.2f} CHF\n"
                f"📧 **Destination :** Votre compte PayPal\n\n"
                f"🚗 **Trajet :** {trip.departure_city} → {trip.arrival_city}\n"
                f"💳 **Nouveau prix :** {new_price:.2f} CHF\n\n"
                f"Le remboursement arrivera dans votre compte PayPal dans les prochaines minutes.\n\n"
                f"Merci d'utiliser CovoiturageSuisse !"
            )
            
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur notification remboursement: {e}")
    
    def _calculate_total_trip_price(self, trip: Trip) -> float:
        """
        Calcule le prix total du trajet
        """
        if hasattr(trip, 'total_trip_price') and trip.total_trip_price:
            return trip.total_trip_price
        
        # Fallback: calculer depuis la distance
        if hasattr(trip, 'total_distance') and trip.total_distance:
            try:
                from handlers.trip_handlers import compute_price_auto
                total_price, _ = compute_price_auto(trip.departure_city, trip.arrival_city)
                return total_price
            except:
                pass
        
        # Dernier fallback: estimer depuis le prix par place
        return trip.price_per_seat * 2  # Estimation conservative
    
    async def _update_booking_prices(self, trip_id: int, new_price_per_passenger: float):
        """
        Met à jour les prix des réservations après remboursement
        """
        try:
            db = get_db()
            bookings = db.query(Booking).filter(Booking.trip_id == trip_id).all()
            
            for booking in bookings:
                booking.total_price = new_price_per_passenger
            
            db.commit()
            logger.info(f"Prix mis à jour pour le trajet {trip_id}: {new_price_per_passenger} CHF par passager")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour des prix: {e}")

# Fonction principale pour remplacer l'ancienne
async def trigger_automatic_refunds_fixed(trip_id: int, bot=None) -> Tuple[bool, Optional[str]]:
    """
    Point d'entrée CORRIGÉ pour les remboursements automatiques
    """
    try:
        refund_manager = FixedAutoRefundManager()
        success = await refund_manager.handle_new_passenger_refund(trip_id, bot)
        return success, None if success else "Erreur lors du traitement des remboursements"
        
    except Exception as e:
        logger.error(f"Erreur trigger_automatic_refunds_fixed: {e}")
        return False, str(e)
