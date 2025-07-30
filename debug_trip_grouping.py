#!/usr/bin/env python3
"""
Test debug pour comprendre pourquoi les trajets ne sont pas groupés
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import SessionLocal
from database.models import Trip, User, Booking
from datetime import datetime

def debug_trip_grouping():
    """Debug du groupement des trajets"""
    print("🔍 DEBUG - Analyse du groupement des trajets")
    
    with SessionLocal() as session:
        # Prendre tous les utilisateurs avec des trajets réguliers
        users_with_regular_trips = session.query(User).join(Trip).filter(
            Trip.recurring == True
        ).distinct().all()
        
        print(f"📊 {len(users_with_regular_trips)} utilisateurs avec des trajets réguliers")
        
        for user in users_with_regular_trips:
            print(f"\n👤 Utilisateur ID: {user.id}, Telegram ID: {user.telegram_id}")
            
            # Simuler la requête exacte de list_my_trips
            trips = session.query(Trip).filter(
                Trip.driver_id == user.id,
                Trip.is_published == True,
                Trip.departure_time > datetime.now(),
                Trip.is_cancelled == False
            ).order_by(Trip.departure_time).all()
            
            print(f"   📋 {len(trips)} trajets trouvés avec les filtres")
            
            # Groupement comme dans le code
            trip_groups = {}
            individual_trips = []
            
            for trip in trips:
                print(f"   🔍 Trip {trip.id}: recurring={trip.recurring}, group_id={trip.group_id}")
                
                if getattr(trip, 'is_cancelled', False):
                    print(f"      ❌ Ignoré car annulé")
                    continue
                    
                if trip.recurring and trip.group_id:
                    print(f"      ✅ Ajouté au groupe {trip.group_id}")
                    if trip.group_id not in trip_groups:
                        trip_groups[trip.group_id] = []
                    trip_groups[trip.group_id].append(trip)
                else:
                    print(f"      📍 Ajouté aux trajets individuels (recurring={trip.recurring}, group_id={trip.group_id})")
                    individual_trips.append(trip)
            
            print(f"   📊 RÉSULTAT: {len(trip_groups)} groupes, {len(individual_trips)} individuels")
            
            for group_id, group_trips in trip_groups.items():
                print(f"      🔄 Groupe {group_id}: {len(group_trips)} trajets")
            
            for trip in individual_trips:
                print(f"      📍 Individuel: {trip.departure_city} → {trip.arrival_city} le {trip.departure_time}")

if __name__ == "__main__":
    debug_trip_grouping()
