#!/usr/bin/env python3
"""
NETTOYAGE AUTOMATIQUE DES RÉSERVATIONS NON PAYÉES
Ce script supprime automatiquement les réservations non payées après 1 heure
À intégrer dans le système pour éviter l'accumulation
"""

from datetime import datetime, timedelta
from database.models import Booking, Trip
from database.db_manager import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_unpaid_bookings():
    """
    Supprime automatiquement les réservations non payées de plus de 1 heure
    Restaure les places dans les trajets
    """
    
    db = get_db()
    
    try:
        # Calculer la limite de temps (1 heure avant maintenant)
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # Trouver toutes les réservations non payées de plus de 1 heure
        expired_bookings = db.query(Booking).filter(
            Booking.is_paid == False,
            Booking.booking_date < cutoff_time
        ).all()
        
        logger.info(f"🔍 Trouvé {len(expired_bookings)} réservations expirées à supprimer")
        
        seats_restored = 0
        
        for booking in expired_bookings:
            logger.info(f"🗑️ Suppression réservation expirée:")
            logger.info(f"   - ID: {booking.id}")
            logger.info(f"   - PayPal: {booking.paypal_payment_id}")
            logger.info(f"   - Date: {booking.booking_date}")
            logger.info(f"   - Âge: {datetime.now() - booking.booking_date}")
            
            # Restaurer les places dans le trajet
            if booking.trip and booking.seats_booked:
                booking.trip.seats_available += booking.seats_booked
                seats_restored += booking.seats_booked
                logger.info(f"   - Places restaurées: +{booking.seats_booked} (total: {booking.trip.seats_available})")
            
            # Supprimer la réservation
            db.delete(booking)
        
        # Sauvegarder les changements
        db.commit()
        
        logger.info(f"✅ Nettoyage terminé:")
        logger.info(f"   - {len(expired_bookings)} réservations supprimées")
        logger.info(f"   - {seats_restored} places restaurées")
        
        return len(expired_bookings)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage: {e}")
        db.rollback()
        return 0
        
    finally:
        db.close()

def cleanup_all_unpaid_bookings():
    """
    Supprime TOUTES les réservations non payées (pour nettoyage manuel)
    """
    
    db = get_db()
    
    try:
        # Trouver TOUTES les réservations non payées
        unpaid_bookings = db.query(Booking).filter(
            Booking.is_paid == False
        ).all()
        
        logger.info(f"🔍 Trouvé {len(unpaid_bookings)} réservations non payées à supprimer")
        
        seats_restored = 0
        
        for booking in unpaid_bookings:
            logger.info(f"🗑️ Suppression réservation non payée:")
            logger.info(f"   - ID: {booking.id}")
            logger.info(f"   - PayPal: {booking.paypal_payment_id}")
            
            # Restaurer les places dans le trajet
            if booking.trip and booking.seats_booked:
                booking.trip.seats_available += booking.seats_booked
                seats_restored += booking.seats_booked
                logger.info(f"   - Places restaurées: +{booking.seats_booked}")
            
            # Supprimer la réservation
            db.delete(booking)
        
        # Sauvegarder les changements
        db.commit()
        
        logger.info(f"✅ Nettoyage complet terminé:")
        logger.info(f"   - {len(unpaid_bookings)} réservations supprimées")
        logger.info(f"   - {seats_restored} places restaurées")
        
        return len(unpaid_bookings)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage: {e}")
        db.rollback()
        return 0
        
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("🧹 Nettoyage de TOUTES les réservations non payées...")
        deleted = cleanup_all_unpaid_bookings()
    else:
        print("🧹 Nettoyage des réservations expirées (>1h non payées)...")
        deleted = cleanup_unpaid_bookings()
    
    if deleted > 0:
        print(f"✅ {deleted} réservations nettoyées")
    else:
        print("ℹ️ Aucune réservation à nettoyer")
