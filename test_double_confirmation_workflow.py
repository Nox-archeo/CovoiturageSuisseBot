#!/usr/bin/env python3
"""
Test complet du workflow de double confirmation
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/margaux/CovoiturageSuisse')

from database import get_db
from database.models import User, Trip, Booking
from trip_confirmation_system import add_confirmation_buttons_to_trip, get_trip_confirmation_state

async def test_double_confirmation_workflow():
    """
    Test complet du workflow de double confirmation
    """
    print("🧪 Test complet du workflow de double confirmation")
    print("=" * 60)
    
    db = get_db()
    
    # Nettoyer les données de test précédentes
    db.query(Booking).filter(Booking.trip_id.in_(
        db.query(Trip.id).filter(Trip.departure_city == "Lausanne Test")
    )).delete(synchronize_session=False)
    db.query(Trip).filter(Trip.departure_city == "Lausanne Test").delete()
    db.query(User).filter(User.telegram_id.in_([999001, 999002])).delete()
    db.commit()
    
    # Créer utilisateurs de test
    test_driver = User(
        telegram_id=999001,
        username="test_driver",
        full_name="Conducteur Test",
        is_driver=True,
        paypal_email="driver@test.com"
    )
    
    test_passenger = User(
        telegram_id=999002,
        username="test_passenger", 
        full_name="Passager Test",
        is_passenger=True
    )
    
    db.add(test_driver)
    db.add(test_passenger)
    db.commit()
    
    # Créer trajet terminé
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
        driver_confirmed_completion=False,  # PAS ENCORE CONFIRMÉ
        payment_released=False
    )
    
    db.add(test_trip)
    db.commit()
    
    # Créer réservation payée
    test_booking = Booking(
        trip_id=test_trip.id,
        passenger_id=test_passenger.id,
        amount=25.0,
        status='confirmed',
        is_paid=True,
        payment_status='completed',
        passenger_confirmed_completion=False  # PAS ENCORE CONFIRMÉ
    )
    
    db.add(test_booking)
    db.commit()
    
    print(f"✅ Données créées : Trip ID {test_trip.id}, Booking ID {test_booking.id}")
    print()
    
    # === ÉTAT INITIAL ===
    print("📋 ÉTAT INITIAL - Aucune confirmation")
    confirmation_state = get_trip_confirmation_state(test_trip.id, db)
    print(f"   Conducteur confirmé: {confirmation_state['driver_confirmed']}")
    print(f"   Passager confirmé: {confirmation_state.get('passenger_confirmations', {})}")
    print(f"   Tout confirmé: {confirmation_state['all_confirmed']}")
    print()
    
    # Test boutons conducteur
    print("🚗 Boutons conducteur (état initial) :")
    driver_buttons = await add_confirmation_buttons_to_trip(test_trip.id, test_driver.telegram_id, 'driver')
    for btn in driver_buttons:
        print(f"   - {btn.text}")
    print()
    
    # Test boutons passager
    print("🎫 Boutons passager (état initial) :")
    passenger_buttons = await add_confirmation_buttons_to_trip(test_trip.id, test_passenger.telegram_id, 'passenger')
    for btn in passenger_buttons:
        print(f"   - {btn.text}")
    print()
    
    # === SIMULATION CONFIRMATION CONDUCTEUR ===
    print("📋 SIMULATION - Conducteur confirme")
    test_trip.driver_confirmed_completion = True
    db.commit()
    
    confirmation_state = get_trip_confirmation_state(test_trip.id, db)
    print(f"   Conducteur confirmé: {confirmation_state['driver_confirmed']}")
    print(f"   Passager confirmé: {confirmation_state.get('passenger_confirmations', {})}")
    print(f"   Tout confirmé: {confirmation_state['all_confirmed']}")
    print()
    
    # Test boutons après confirmation conducteur
    print("🚗 Boutons conducteur (après sa confirmation) :")
    driver_buttons = await add_confirmation_buttons_to_trip(test_trip.id, test_driver.telegram_id, 'driver')
    for btn in driver_buttons:
        print(f"   - {btn.text}")
    print()
    
    print("🎫 Boutons passager (après confirmation conducteur) :")
    passenger_buttons = await add_confirmation_buttons_to_trip(test_trip.id, test_passenger.telegram_id, 'passenger')
    for btn in passenger_buttons:
        print(f"   - {btn.text}")
    print()
    
    # === SIMULATION CONFIRMATION PASSAGER ===
    print("📋 SIMULATION - Passager confirme")
    test_booking.passenger_confirmed_completion = True
    db.commit()
    
    confirmation_state = get_trip_confirmation_state(test_trip.id, db)
    print(f"   Conducteur confirmé: {confirmation_state['driver_confirmed']}")
    print(f"   Passager confirmé: {confirmation_state.get('passenger_confirmations', {})}")
    print(f"   Tout confirmé: {confirmation_state['all_confirmed']}")
    print()
    
    # Test boutons après double confirmation
    print("🚗 Boutons conducteur (après double confirmation) :")
    driver_buttons = await add_confirmation_buttons_to_trip(test_trip.id, test_driver.telegram_id, 'driver')
    for btn in driver_buttons:
        print(f"   - {btn.text}")
    print()
    
    print("🎫 Boutons passager (après double confirmation) :")
    passenger_buttons = await add_confirmation_buttons_to_trip(test_trip.id, test_passenger.telegram_id, 'passenger')
    for btn in passenger_buttons:
        print(f"   - {btn.text}")
    print()
    
    # Nettoyage
    print("🧹 Nettoyage des données de test...")
    db.query(Booking).filter(Booking.id == test_booking.id).delete()
    db.query(Trip).filter(Trip.id == test_trip.id).delete()
    db.query(User).filter(User.id.in_([test_driver.id, test_passenger.id])).delete()
    db.commit()
    
    print("✅ Test terminé avec succès !")

if __name__ == "__main__":
    asyncio.run(test_double_confirmation_workflow())
