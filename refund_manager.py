#!/usr/bin/env python3
"""
Gestionnaire de remboursements automatiques pour le système de covoiturage
Gère les remboursements PayPal pour les annulations et ajustements de prix
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from database import get_db
from database.models import Booking, Trip, User
from paypal_utils import PayPalManager
from utils.swiss_pricing import round_to_nearest_0_05, format_swiss_price

logger = logging.getLogger(__name__)

class RefundManager:
    """Gestionnaire des remboursements automatiques"""
    
    def __init__(self):
        self.paypal_manager = PayPalManager()
    
    async def process_trip_cancellation_refunds(self, trip_id: int, reason: str = "Annulation du trajet") -> Dict[str, List]:
        """
        Traite les remboursements pour l'annulation d'un trajet complet
        
        Args:
            trip_id: ID du trajet annulé
            reason: Motif de l'annulation
            
        Returns:
            Dict avec les résultats des remboursements
        """
        results = {
            "successful_refunds": [],
            "failed_refunds": [],
            "total_refunded": 0.0
        }
        
        try:
            db = get_db()
            
            # Récupérer toutes les réservations payées pour ce trajet
            bookings = db.query(Booking).filter(
                Booking.trip_id == trip_id,
                Booking.is_paid == True,
                Booking.paypal_payment_id.isnot(None)
            ).all()
            
            logger.info(f"Traitement des remboursements pour {len(bookings)} réservations du trajet {trip_id}")
            
            for booking in bookings:
                try:
                    # Effectuer le remboursement complet
                    success, refund_id = self.paypal_manager.refund_card_payment(
                        payment_id=booking.paypal_payment_id,
                        refund_amount=None,  # Remboursement total
                        reason=reason
                    )
                    
                    if success:
                        # Mettre à jour le statut de la réservation
                        booking.status = "refunded"
                        booking.refund_id = refund_id
                        booking.refund_date = datetime.now()
                        booking.refund_amount = booking.amount
                        
                        results["successful_refunds"].append({
                            "booking_id": booking.id,
                            "passenger_id": booking.passenger_id,
                            "amount": float(booking.amount),
                            "refund_id": refund_id
                        })
                        
                        results["total_refunded"] += float(booking.amount)
                        
                        logger.info(f"Remboursement réussi pour la réservation {booking.id}: {booking.amount} CHF")
                        
                    else:
                        results["failed_refunds"].append({
                            "booking_id": booking.id,
                            "passenger_id": booking.passenger_id,
                            "amount": float(booking.amount),
                            "error": "Échec du remboursement PayPal"
                        })
                        
                        logger.error(f"Échec du remboursement pour la réservation {booking.id}")
                
                except Exception as e:
                    logger.error(f"Erreur lors du remboursement de la réservation {booking.id}: {str(e)}")
                    results["failed_refunds"].append({
                        "booking_id": booking.id,
                        "passenger_id": booking.passenger_id,
                        "amount": float(booking.amount),
                        "error": str(e)
                    })
            
            # Sauvegarder les modifications
            db.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des remboursements pour le trajet {trip_id}: {str(e)}")
            db.rollback()
        
        return results
    
    async def process_price_adjustment_refunds(self, trip_id: int) -> Dict[str, List]:
        """
        Traite les remboursements d'ajustement de prix quand des passagers supplémentaires rejoignent
        
        Args:
            trip_id: ID du trajet avec ajustement de prix
            
        Returns:
            Dict avec les résultats des ajustements
        """
        results = {
            "successful_adjustments": [],
            "failed_adjustments": [],
            "total_refunded": 0.0
        }
        
        try:
            db = get_db()
            
            # Récupérer le trajet et calculer le nouveau prix par siège
            trip = db.query(Trip).get(trip_id)
            if not trip:
                logger.error(f"Trajet {trip_id} non trouvé")
                return results
            
            # Récupérer toutes les réservations payées
            bookings = db.query(Booking).filter(
                Booking.trip_id == trip_id,
                Booking.is_paid == True,
                Booking.paypal_payment_id.isnot(None)
            ).all()
            
            if not bookings:
                logger.info(f"Aucune réservation payée trouvée pour le trajet {trip_id}")
                return results
            
            # Calculer le nouveau prix par siège (divisé par le nombre total de passagers)
            total_passengers = sum(booking.seats for booking in bookings)
            if total_passengers == 0:
                return results
            
            new_price_per_seat = round_to_nearest_0_05(trip.price_per_seat / total_passengers)
            
            logger.info(f"Ajustement de prix pour le trajet {trip_id}: {trip.price_per_seat} CHF → {new_price_per_seat} CHF par siège")
            
            for booking in bookings:
                try:
                    # Calculer le nouveau montant total pour cette réservation
                    new_total_amount = round_to_nearest_0_05(new_price_per_seat * booking.seats)
                    old_amount = float(booking.amount)
                    
                    # Calculer le montant à rembourser
                    refund_amount = round_to_nearest_0_05(old_amount - new_total_amount)
                    
                    if refund_amount > 0:
                        # Effectuer le remboursement partiel
                        success, refund_id = self.paypal_manager.refund_card_payment(
                            payment_id=booking.paypal_payment_id,
                            refund_amount=refund_amount,
                            reason=f"Ajustement de prix - Nouveau passager rejoint le trajet"
                        )
                        
                        if success:
                            # Mettre à jour la réservation
                            booking.amount = new_total_amount
                            booking.price_adjusted = True
                            booking.refund_amount = refund_amount
                            booking.refund_id = refund_id
                            booking.refund_date = datetime.now()
                            
                            results["successful_adjustments"].append({
                                "booking_id": booking.id,
                                "passenger_id": booking.passenger_id,
                                "old_amount": old_amount,
                                "new_amount": new_total_amount,
                                "refund_amount": refund_amount,
                                "refund_id": refund_id
                            })
                            
                            results["total_refunded"] += refund_amount
                            
                            logger.info(f"Ajustement réussi pour la réservation {booking.id}: remboursement de {refund_amount} CHF")
                        
                        else:
                            results["failed_adjustments"].append({
                                "booking_id": booking.id,
                                "passenger_id": booking.passenger_id,
                                "refund_amount": refund_amount,
                                "error": "Échec du remboursement PayPal"
                            })
                    
                    else:
                        logger.info(f"Aucun ajustement nécessaire pour la réservation {booking.id}")
                
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajustement pour la réservation {booking.id}: {str(e)}")
                    results["failed_adjustments"].append({
                        "booking_id": booking.id,
                        "passenger_id": booking.passenger_id,
                        "error": str(e)
                    })
            
            # Sauvegarder les modifications
            db.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des ajustements pour le trajet {trip_id}: {str(e)}")
            db.rollback()
        
        return results
    
    async def cancel_booking_refund(self, booking_id: int, reason: str = "Annulation de la réservation") -> Tuple[bool, Optional[str]]:
        """
        Traite le remboursement pour l'annulation d'une réservation individuelle
        
        Args:
            booking_id: ID de la réservation à annuler
            reason: Motif de l'annulation
            
        Returns:
            Tuple[success, refund_id]
        """
        try:
            db = get_db()
            
            booking = db.query(Booking).get(booking_id)
            if not booking:
                logger.error(f"Réservation {booking_id} non trouvée")
                return False, None
            
            if not booking.is_paid or not booking.paypal_payment_id:
                logger.info(f"Réservation {booking_id} non payée, pas de remboursement nécessaire")
                booking.status = "cancelled"
                db.commit()
                return True, None
            
            # Effectuer le remboursement complet
            success, refund_id = self.paypal_manager.refund_card_payment(
                payment_id=booking.paypal_payment_id,
                refund_amount=None,  # Remboursement total
                reason=reason
            )
            
            if success:
                # Mettre à jour le statut de la réservation
                booking.status = "refunded"
                booking.refund_id = refund_id
                booking.refund_date = datetime.now()
                booking.refund_amount = booking.amount
                
                # Libérer les places dans le trajet
                trip = db.query(Trip).get(booking.trip_id)
                if trip:
                    if hasattr(trip, 'available_seats') and trip.available_seats is not None:
                        trip.available_seats += booking.seats
                    elif hasattr(trip, 'seats_available') and trip.seats_available is not None:
                        trip.seats_available += booking.seats
                
                db.commit()
                
                logger.info(f"Annulation et remboursement réussis pour la réservation {booking_id}: {booking.amount} CHF")
                return True, refund_id
            
            else:
                logger.error(f"Échec du remboursement pour la réservation {booking_id}")
                return False, None
        
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de la réservation {booking_id}: {str(e)}")
            db.rollback()
            return False, None


# Instance globale du gestionnaire de remboursements
refund_manager = RefundManager()
