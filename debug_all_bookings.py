#!/usr/bin/env python3
"""
Debug: Voir TOUTES les réservations dans la base
"""

from database.models import Booking, Trip, User
from database.db_manager import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_all_bookings():
    """Voir toutes les réservations de la base"""
    
    db = get_db()
    
    try:
        # Voir TOUTES les réservations
        all_bookings = db.query(Booking).all()
        
        logger.info(f"📊 TOTAL réservations dans la base: {len(all_bookings)}")
        
        for i, booking in enumerate(all_bookings, 1):
            logger.info(f"\n📋 Réservation {i}:")
            logger.info(f"   - ID: {booking.id}")
            logger.info(f"   - Passager ID: {booking.passenger_id}")
            logger.info(f"   - Trip ID: {booking.trip_id}")
            logger.info(f"   - PayPal: {booking.paypal_payment_id}")
            logger.info(f"   - Payé: {booking.is_paid}")
            logger.info(f"   - Status: {booking.status}")
            logger.info(f"   - Montant: {booking.amount}")
            
            # Voir le trajet associé
            if booking.trip:
                trip = booking.trip
                logger.info(f"   - Trajet: {trip.departure_city} → {trip.arrival_city}")
                logger.info(f"   - Date: {trip.departure_time}")
        
        # Voir TOUS les utilisateurs aussi
        all_users = db.query(User).all()
        logger.info(f"\n👥 TOTAL utilisateurs: {len(all_users)}")
        
        for user in all_users:
            user_bookings = db.query(Booking).filter(Booking.passenger_id == user.id).all()
            logger.info(f"   - {user.full_name or user.username} (ID:{user.id}, TG:{user.telegram_id}): {len(user_bookings)} réservations")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    debug_all_bookings()
