#!/usr/bin/env python3
"""
Test de l'affichage groupé des trajets réguliers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import SessionLocal
from database.models import Trip, User, Booking
from datetime import datetime

def test_grouped_display():
    """Test l'affichage groupé des trajets réguliers"""
    print("🧪 Test de l'affichage groupé des trajets réguliers")
    
    with SessionLocal() as session:
        # Simuler un utilisateur (telegram_id = 123456789 du test précédent)
        user = session.query(User).filter(User.telegram_id == 123456789).first()
        if not user:
            print("❌ Utilisateur de test non trouvé")
            return
        
        print(f"✅ Utilisateur trouvé: {user.id}")
        
        # Récupérer tous les trajets à venir non annulés du conducteur
        trips = session.query(Trip).filter(
            Trip.driver_id == user.id,
            Trip.is_published == True,
            Trip.departure_time > datetime.now()
        ).order_by(Trip.departure_time).all()
        
        print(f"📊 {len(trips)} trajets trouvés")
        
        # Regrouper les trajets réguliers par group_id
        trip_groups = {}
        individual_trips = []
        
        for trip in trips:
            print(f"  Trip {trip.id}: recurring={trip.recurring}, group_id={trip.group_id}")
            
            if trip.recurring and trip.group_id:
                # Trajet régulier - le regrouper
                if trip.group_id not in trip_groups:
                    trip_groups[trip.group_id] = []
                trip_groups[trip.group_id].append(trip)
            else:
                # Trajet individuel
                individual_trips.append(trip)
        
        print(f"\n📋 RÉSULTATS DU GROUPEMENT:")
        print(f"   - Groupes réguliers: {len(trip_groups)}")
        print(f"   - Trajets individuels: {len(individual_trips)}")
        
        # Afficher les groupes de trajets réguliers
        for group_id, group_trips in trip_groups.items():
            if len(group_trips) > 0:
                first_trip = group_trips[0]
                
                # Compter le total des réservations dans le groupe
                total_bookings = 0
                total_seats = 0
                for trip in group_trips:
                    booking_count = session.query(Booking).filter(
                        Booking.trip_id == trip.id, 
                        Booking.status.in_(["pending", "confirmed"])
                    ).count()
                    total_bookings += booking_count
                    total_seats += trip.seats_available
                
                print(f"\n🔄 GROUPE RÉGULIER ({len(group_trips)} trajets)")
                print(f"   📍 {first_trip.departure_city} → {first_trip.arrival_city}")
                print(f"   💰 {first_trip.price_per_seat} CHF/place")
                print(f"   💺 {total_bookings}/{total_seats} réservations totales")
                print(f"   🆔 Group ID: {group_id}")
        
        # Afficher les trajets individuels
        for trip in individual_trips:
            departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
            
            # Compter les réservations actives
            booking_count = session.query(Booking).filter(
                Booking.trip_id == trip.id, 
                Booking.status.in_(["pending", "confirmed"])
            ).count()
            
            print(f"\n📍 TRAJET INDIVIDUEL")
            print(f"   📍 {trip.departure_city} → {trip.arrival_city}")
            print(f"   📅 {departure_date}")
            print(f"   💰 {trip.price_per_seat} CHF/place")
            print(f"   💺 {booking_count}/{trip.seats_available} réservations")

if __name__ == "__main__":
    test_grouped_display()
