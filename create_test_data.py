#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour créer des données de test dans la base de données
"""

import logging
from database.db_manager import get_db
from database.models import User, Trip, Booking
from datetime import datetime, timedelta
from sqlalchemy import exists

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_test_data():
    """
    Crée des données de test dans la base de données
    """
    db = get_db()
    
    # Vérifier si l'utilisateur existe déjà
    user_exists = db.query(exists().where(User.telegram_id == 5932296330)).scalar()
    
    if not user_exists:
        # Créer un utilisateur de test
        logger.info("Création d'un utilisateur de test...")
        user = User(
            telegram_id=5932296330,
            username="test_user",
            full_name="Test User",
            is_driver=True,
            is_passenger=True,
            driver_rating=4.8,
            passenger_rating=4.9,
            phone="+41791234567"
        )
        db.add(user)
        db.commit()
    else:
        user = db.query(User).filter(User.telegram_id == 5932296330).first()
        logger.info(f"Utilisateur existant trouvé: {user.full_name}")
    
    # Créer un nouveau trajet
    logger.info("Création d'un trajet de test...")
    
    # Définir les dates pour les trajets
    future_date = datetime.now() + timedelta(days=7)
    past_date = datetime.now() - timedelta(days=3)
    
    # Trajet futur
    future_trip = Trip(
        driver_id=user.id,
        departure_city="Genève",
        arrival_city="Lausanne",
        departure_time=future_date,
        seats_available=3,
        available_seats=3,
        price_per_seat=15.0,
        additional_info="Trajet test pour le futur",
        is_published=True
    )
    db.add(future_trip)
    
    # Trajet passé
    past_trip = Trip(
        driver_id=user.id,
        departure_city="Lausanne",
        arrival_city="Berne",
        departure_time=past_date,
        seats_available=4,
        available_seats=0,
        price_per_seat=25.0,
        additional_info="Trajet test passé",
        is_published=True
    )
    db.add(past_trip)
    db.commit()
    
    # Créer une réservation pour le trajet passé
    logger.info("Création d'une réservation de test...")
    booking = Booking(
        trip_id=past_trip.id,
        passenger_id=user.id,  # L'utilisateur réserve son propre trajet pour le test
        status="completed",
        seats=2,
        booking_date=past_date - timedelta(days=2),
        is_paid=True,
        amount=past_trip.price_per_seat * 2,
        stripe_session_id="test_session_id",
        stripe_payment_intent_id="test_payment_intent_id"
    )
    db.add(booking)
    
    # Créer une réservation en attente pour le trajet futur
    pending_booking = Booking(
        trip_id=future_trip.id,
        passenger_id=user.id,
        status="pending",
        seats=1,
        booking_date=datetime.now(),
        is_paid=False
    )
    db.add(pending_booking)
    db.commit()
    
    logger.info("Données de test créées avec succès!")

if __name__ == "__main__":
    logger.info("Création de données de test pour le bot de covoiturage...")
    create_test_data()
