#!/usr/bin/env python3
"""
Trouver le VRAI trajet Corpataux → Posieux avec VRAI conducteur
"""

import os
from dotenv import load_dotenv
load_dotenv()

def find_real_corpataux_trip():
    """Trouve le vrai trajet et conducteur"""
    try:
        from database.db_manager import get_db
        from database.models import Trip, User, Booking
        
        db = get_db()
        
        # Votre ID
        your_telegram_id = 5932296330
        
        print("🔍 RECHERCHE TRAJET CORPATAUX → POSIEUX...")
        
        # Chercher TOUS les trajets avec Corpataux ou Posieux
        all_trips = db.query(Trip).all()
        
        corpataux_trips = []
        for trip in all_trips:
            if ('Corpataux' in trip.departure_city or 'corpataux' in trip.departure_city.lower()) and \
               ('Posieux' in trip.arrival_city or 'posieux' in trip.arrival_city.lower()):
                corpataux_trips.append(trip)
        
        print(f"✅ Trouvé {len(corpataux_trips)} trajets Corpataux → Posieux")
        
        for i, trip in enumerate(corpataux_trips):
            print(f"\n--- TRAJET #{trip.id} ---")
            print(f"📍 Route: {trip.departure_city} → {trip.arrival_city}")
            print(f"📅 Date: {trip.departure_time}")
            print(f"💰 Prix: {trip.price_per_seat} CHF")
            
            if trip.driver:
                print(f"🚗 Conducteur: {trip.driver.full_name or trip.driver.username}")
                print(f"📱 Telegram ID: {trip.driver.telegram_id}")
                print(f"🔍 ID base: {trip.driver.id}")
                
                # Vérifier si c'est un vrai utilisateur (pas de test)
                if trip.driver.telegram_id and trip.driver.telegram_id != 123456789:
                    print("✅ VRAI CONDUCTEUR !")
                else:
                    print("❌ Conducteur de test")
            else:
                print("❌ Pas de conducteur")
            
            # Vérifier vos réservations sur ce trajet
            your_bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.passenger_id == db.query(User).filter(User.telegram_id == your_telegram_id).first().id
            ).all()
            
            if your_bookings:
                for booking in your_bookings:
                    print(f"✅ VOTRE RÉSERVATION #{booking.id} - Statut: {booking.payment_status}")
        
        # Chercher aussi par date (21/08/2025 à 14:00)
        print(f"\n🗓 RECHERCHE PAR DATE 21/08/2025 14:00...")
        
        from datetime import datetime
        target_date = datetime(2025, 8, 21, 14, 0)
        
        date_trips = db.query(Trip).filter(
            Trip.departure_time == target_date
        ).all()
        
        print(f"✅ Trouvé {len(date_trips)} trajets le 21/08/2025 à 14:00")
        
        for trip in date_trips:
            print(f"\n--- TRAJET DATE #{trip.id} ---")
            print(f"📍 Route: {trip.departure_city} → {trip.arrival_city}")
            print(f"🚗 Conducteur: {trip.driver.full_name if trip.driver else 'Aucun'}")
            print(f"📱 Telegram ID: {trip.driver.telegram_id if trip.driver else 'Aucun'}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    find_real_corpataux_trip()
