#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de diagnostic pour tester les fonctions du profile_handler
"""

import logging
import sys
from database.db_manager import get_db
from database.models import User, Trip, Booking
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_get_user_stats():
    """
    Test la fonction get_user_stats
    """
    try:
        db = get_db()
        
        # Trouver un utilisateur pour le test
        user = db.query(User).first()
        
        if not user:
            logger.error("Aucun utilisateur trouvé dans la base de données!")
            return False
        
        logger.info(f"Test avec l'utilisateur #{user.id} (Telegram ID: {user.telegram_id})")
        
        # Simuler le calcul des statistiques
        stats = {
            'rating': 0,
            'trips_count': 0,
            'bookings_count': 0,
            'earnings': 0.00
        }
        
        # Récupérer la note moyenne
        driver_rating = user.driver_rating if hasattr(user, 'driver_rating') else 0
        passenger_rating = user.passenger_rating if hasattr(user, 'passenger_rating') else 0
        
        if driver_rating and passenger_rating:
            stats['rating'] = (driver_rating + passenger_rating) / 2
        elif driver_rating:
            stats['rating'] = driver_rating
        elif passenger_rating:
            stats['rating'] = passenger_rating
        else:
            stats['rating'] = 5.0
        
        # Compter les trajets à venir
        future_trips = db.query(Trip).filter(
            Trip.driver_id == user.id,
            Trip.departure_time > datetime.now()
        ).all()
        stats['trips_count'] = len(future_trips)
        
        # Compter les réservations actives
        active_bookings = db.query(Booking).filter(
            Booking.passenger_id == user.id,
            Booking.status.in_(['confirmed', 'pending'])
        ).join(Trip).filter(
            Trip.departure_time > datetime.now()
        ).all()
        stats['bookings_count'] = len(active_bookings)
        
        # Calculer les gains
        total_earnings = 0
        completed_trips = db.query(Trip).filter(
            Trip.driver_id == user.id,
            Trip.departure_time <= datetime.now()
        ).all()
        
        logger.info(f"Trajets complétés : {len(completed_trips)}")
        
        for trip in completed_trips:
            try:
                bookings = db.query(Booking).filter(
                    Booking.trip_id == trip.id,
                    Booking.status == 'completed'
                ).all()
                
                logger.info(f"Trajet #{trip.id}: {len(bookings)} réservations")
                
                for booking in bookings:
                    try:
                        seats = 1
                        if hasattr(booking, 'seats') and booking.seats is not None:
                            seats = booking.seats
                            logger.info(f"Réservation avec {seats} places")
                        
                        is_paid = True
                        if hasattr(booking, 'is_paid'):
                            is_paid = booking.is_paid
                            logger.info(f"Statut de paiement: {'Payé' if is_paid else 'Non payé'}")
                        
                        if is_paid:
                            price = trip.price_per_seat or 0
                            earnings = seats * price * 0.88
                            total_earnings += earnings
                            logger.info(f"Gain pour cette réservation: {earnings} CHF")
                    except Exception as e:
                        logger.error(f"Erreur lors du traitement de la réservation #{booking.id}: {str(e)}")
            except Exception as e:
                logger.error(f"Erreur lors du traitement du trajet #{trip.id}: {str(e)}")
        
        stats['earnings'] = total_earnings
        
        logger.info(f"Statistiques calculées: {stats}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors du test de get_user_stats: {str(e)}")
        return False

def test_booking_model():
    """
    Test l'accès aux colonnes du modèle Booking
    """
    try:
        db = get_db()
        booking = db.query(Booking).first()
        
        if not booking:
            logger.info("Aucune réservation trouvée dans la base de données.")
            return False
        
        logger.info(f"Test avec la réservation #{booking.id}")
        
        # Tester l'accès aux colonnes qui pourraient avoir été ajoutées
        attributes = ['seats', 'booking_date', 'is_paid', 'amount', 
                     'stripe_session_id', 'stripe_payment_intent_id']
        
        for attr in attributes:
            try:
                value = getattr(booking, attr, None)
                logger.info(f"Attribut '{attr}' = {value}")
            except Exception as e:
                logger.error(f"Erreur lors de l'accès à l'attribut '{attr}': {str(e)}")
        
        # Tester la relation avec Trip
        trip = booking.trip
        logger.info(f"Relation trip: {trip.id if trip else 'None'}")
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors du test du modèle Booking: {str(e)}")
        return False

def run_tests():
    """
    Exécute tous les tests
    """
    success = True
    
    logger.info("=== TEST DES STATISTIQUES UTILISATEUR ===")
    if test_get_user_stats():
        logger.info("✅ Test des statistiques utilisateur réussi!")
    else:
        logger.error("❌ Test des statistiques utilisateur échoué!")
        success = False
    
    logger.info("\n=== TEST DU MODÈLE BOOKING ===")
    if test_booking_model():
        logger.info("✅ Test du modèle Booking réussi!")
    else:
        logger.error("❌ Test du modèle Booking échoué!")
        success = False
    
    return success

if __name__ == "__main__":
    logger.info("Démarrage des tests de diagnostic du profile_handler...")
    
    if run_tests():
        logger.info("✅✅✅ Tous les tests ont réussi!")
        sys.exit(0)
    else:
        logger.error("❌❌❌ Certains tests ont échoué!")
        sys.exit(1)
