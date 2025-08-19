#!/usr/bin/env python3
"""
Test complet du système de confirmation avec données réelles
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/margaux/CovoiturageSuisse')

from database import get_db
from database.models import User, Trip, Booking
from trip_confirmation_system import add_confirmation_buttons_to_trip

async def create_test_data():
    """
    Crée des données de test dans la base de données
    """
    print("🗃️ Création des données de test...")
    
    db = get_db()
    
    # Vérifier s'il y a déjà des utilisateurs de test
    test_driver = db.query(User).filter(User.telegram_id == 999001).first()
    test_passenger = db.query(User).filter(User.telegram_id == 999002).first()
    
    if not test_driver:
        test_driver = User(
            telegram_id=999001,
            username="test_driver",
            full_name="Conducteur Test",
            is_driver=True,
            paypal_email="driver@test.com"
        )
        db.add(test_driver)
    
    if not test_passenger:
        test_passenger = User(
            telegram_id=999002,
            username="test_passenger", 
            full_name="Passager Test",
            is_passenger=True
        )
        db.add(test_passenger)
    
    db.commit()
    
    # Créer un trajet terminé avec réservation payée
    test_trip = Trip(
        departure_city="Lausanne Test",
        arrival_city="Genève Test",
        departure_time=datetime.now() - timedelta(hours=2),  # Terminé il y a 2h
        price_per_seat=25.0,
        seats_available=3,
        creator_id=test_driver.id,
        driver_id=test_driver.id,
        is_published=True,
        is_cancelled=False,
        driver_confirmed_completion=False,
        payment_released=False
    )
    
    db.add(test_trip)
    db.commit()
    
    # Créer une réservation payée
    test_booking = Booking(
        trip_id=test_trip.id,
        passenger_id=test_passenger.id,
        amount=25.0,
        status='confirmed',
        is_paid=True,
        payment_status='completed',
        passenger_confirmed_completion=False
    )
    
    db.add(test_booking)
    db.commit()
    
    print(f"✅ Données créées : Trip ID {test_trip.id}, Booking ID {test_booking.id}")
    return test_trip.id, test_driver.id, test_passenger.id

async def test_real_confirmation():
    """
    Test avec des données réelles dans la base
    """
    print("🧪 Test de confirmation avec données réelles")
    print("=" * 50)
    
    trip_id, driver_id, passenger_id = await create_test_data()
    
    # Test boutons conducteur
    print("🚗 Test boutons conducteur :")
    driver_buttons = await add_confirmation_buttons_to_trip(trip_id, driver_id, 'driver')
    if driver_buttons:
        print(f"✅ {len(driver_buttons)} bouton(s) généré(s)")
        for btn in driver_buttons:
            print(f"   - {btn.text} (callback: {btn.callback_data})")
    else:
        print("❌ Aucun bouton généré")
    print()
    
    # Test boutons passager
    print("🎫 Test boutons passager :")
    passenger_buttons = await add_confirmation_buttons_to_trip(trip_id, passenger_id, 'passenger')
    if passenger_buttons:
        print(f"✅ {len(passenger_buttons)} bouton(s) généré(s)")
        for btn in passenger_buttons:
            print(f"   - {btn.text} (callback: {btn.callback_data})")
    else:
        print("❌ Aucun bouton généré")
    print()
    
    print("🧹 Nettoyage des données de test...")
    db = get_db()
    
    # Supprimer les données de test
    db.query(Booking).filter(Booking.trip_id == trip_id).delete()
    db.query(Trip).filter(Trip.id == trip_id).delete() 
    db.query(User).filter(User.telegram_id.in_([999001, 999002])).delete()
    db.commit()
    
    print("✅ Données de test nettoyées")
    print("🎯 Test terminé avec succès !")

if __name__ == "__main__":
    asyncio.run(test_real_confirmation())
