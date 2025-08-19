#!/usr/bin/env python3
"""
Test d'intégration du système de confirmation dans les interfaces
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, '/Users/margaux/CovoiturageSuisse')

from database import get_db
from database.models import User, Trip, Booking
from trip_confirmation_system import add_confirmation_buttons_to_trip

async def test_confirmation_buttons():
    """
    Test des boutons de confirmation pour différents scénarios
    """
    db = get_db()
    
    print("🧪 Test d'intégration du système de confirmation")
    print("=" * 50)
    
    # Créer un trajet de test qui se termine récemment
    test_trip = Trip(
        departure_city="Lausanne",
        arrival_city="Genève", 
        departure_time=datetime.now() - timedelta(hours=2),  # Trajet terminé il y a 2h
        price_per_seat=25.0,
        seats_available=3,
        creator_id=1,  # Conducteur
        driver_id=1,
        is_published=True,
        is_cancelled=False,
        driver_confirmed_completion=False,
        payment_released=False
    )
    
    # Simulation d'une réservation payée
    test_booking = Booking(
        trip_id=1,  # Sera mis à jour après insertion
        passenger_id=2,
        amount=25.0,
        status='confirmed',
        is_paid=True,
        payment_status='completed',
        passenger_confirmed_completion=False
    )
    
    print("📝 Scénario de test :")
    print(f"- Trajet : {test_trip.departure_city} → {test_trip.arrival_city}")
    print(f"- Départ : {test_trip.departure_time}")
    print(f"- Status : terminé il y a 2h")
    print(f"- Réservation payée : {test_booking.is_paid}")
    print()
    
    # Test pour le conducteur
    print("🚗 Test boutons conducteur :")
    driver_buttons = await add_confirmation_buttons_to_trip(1, 1, 'driver')  # trip_id=1, user_id=1
    if driver_buttons:
        print(f"✅ {len(driver_buttons)} bouton(s) généré(s)")
        for btn in driver_buttons:
            print(f"   - {btn.text} (callback: {btn.callback_data})")
    else:
        print("❌ Aucun bouton généré")
    print()
    
    # Test pour le passager
    print("🎫 Test boutons passager :")
    passenger_buttons = await add_confirmation_buttons_to_trip(1, 2, 'passenger')  # trip_id=1, user_id=2
    if passenger_buttons:
        print(f"✅ {len(passenger_buttons)} bouton(s) généré(s)")
        for btn in passenger_buttons:
            print(f"   - {btn.text} (callback: {btn.callback_data})")
    else:
        print("❌ Aucun bouton généré")
    print()
    
    # Test protection temporelle (trajet trop récent)
    recent_trip = Trip(
        departure_city="Berne",
        arrival_city="Zurich",
        departure_time=datetime.now() - timedelta(minutes=10),  # Il y a 10 minutes
        price_per_seat=30.0,
        seats_available=2,
        creator_id=1,
        driver_id=1,
        is_published=True,
        is_cancelled=False,
        driver_confirmed_completion=False,
        payment_released=False
    )
    
    print("⏰ Test protection temporelle (trajet trop récent) :")
    recent_buttons = await add_confirmation_buttons_to_trip(2, 1, 'driver')  # trip_id=2, user_id=1
    if recent_buttons:
        print(f"⚠️ {len(recent_buttons)} bouton(s) généré(s) (ne devrait pas arriver)")
    else:
        print("✅ Aucun bouton généré (protection temporelle active)")
    print()
    
    print("🎯 Test terminé avec succès !")

if __name__ == "__main__":
    asyncio.run(test_confirmation_buttons())
