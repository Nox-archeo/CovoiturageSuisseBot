#!/usr/bin/env python3
"""
Diagnostic des vrais trajets et conducteurs
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

async def diagnostic_real_trips():
    """Diagnostic des vrais trajets et conducteurs"""
    try:
        from database.db_manager import get_db
        from database.models import Trip, User, Booking
        
        db = get_db()
        
        # Votre ID Telegram
        user_telegram_id = 5932296330
        user = db.query(User).filter(User.telegram_id == user_telegram_id).first()
        
        print(f"👤 VOS INFOS:")
        print(f"   Nom: {user.full_name or user.username}")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   ID base: {user.id}")
        
        # Lister VOS réservations payées
        print(f"\n📋 VOS RÉSERVATIONS PAYÉES:")
        bookings = db.query(Booking).filter(
            Booking.passenger_id == user.id,
            Booking.payment_status == 'completed'
        ).all()
        
        for booking in bookings:
            trip = booking.trip
            driver = trip.driver if trip else None
            
            print(f"\n   Réservation #{booking.id}:")
            print(f"   📍 Trajet: {trip.departure_city} → {trip.arrival_city}")
            print(f"   📅 Date: {trip.departure_time}")
            print(f"   💰 Montant: {booking.amount} CHF")
            print(f"   🚗 Conducteur: {driver.full_name if driver else 'Aucun'}")
            print(f"   📱 Conducteur Telegram ID: {driver.telegram_id if driver else 'Aucun'}")
        
        # Lister TOUS les trajets avec de vrais conducteurs
        print(f"\n🚗 TOUS LES TRAJETS AVEC VRAIS CONDUCTEURS:")
        trips = db.query(Trip).join(User, Trip.driver_id == User.id).filter(
            User.telegram_id != 123456789  # Exclure les utilisateurs de test
        ).all()
        
        for trip in trips[:10]:  # Limiter à 10
            driver = trip.driver
            print(f"\n   Trajet #{trip.id}:")
            print(f"   📍 Route: {trip.departure_city} → {trip.arrival_city}")
            print(f"   📅 Date: {trip.departure_time}")
            print(f"   🚗 Conducteur: {driver.full_name or driver.username}")
            print(f"   📱 Telegram ID: {driver.telegram_id}")
            
            # Vérifier si vous avez une réservation sur ce trajet
            your_booking = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.passenger_id == user.id
            ).first()
            
            if your_booking:
                print(f"   ✅ VOUS AVEZ UNE RÉSERVATION #{your_booking.id}")
        
        # Lister les trajets de Corpataux → Posieux spécifiquement
        print(f"\n🎯 TRAJETS CORPATAUX → POSIEUX:")
        corpataux_trips = db.query(Trip).filter(
            Trip.departure_city.ilike('%Corpataux%'),
            Trip.arrival_city.ilike('%Posieux%')
        ).all()
        
        for trip in corpataux_trips:
            driver = trip.driver
            print(f"\n   Trajet #{trip.id}:")
            print(f"   📍 Route: {trip.departure_city} → {trip.arrival_city}")
            print(f"   📅 Date: {trip.departure_time}")
            print(f"   🚗 Conducteur: {driver.full_name or driver.username if driver else 'Aucun'}")
            print(f"   📱 Telegram ID: {driver.telegram_id if driver else 'Aucun'}")
            
            # Vos réservations sur ce trajet
            your_bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.passenger_id == user.id
            ).all()
            
            if your_bookings:
                for booking in your_bookings:
                    print(f"   ✅ RÉSERVATION #{booking.id} - Statut: {booking.payment_status}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur diagnostic: {e}")
        return False

if __name__ == "__main__":
    print("🔍 DIAGNOSTIC DES VRAIS TRAJETS ET CONDUCTEURS")
    print("=" * 50)
    
    result = asyncio.run(diagnostic_real_trips())
    
    if result:
        print("\n✅ Diagnostic terminé")
    else:
        print("\n❌ Diagnostic échoué")
