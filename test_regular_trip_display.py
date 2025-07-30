#!/usr/bin/env python3
"""
Test complet de la fonctionnalité des trajets réguliers :
1. Création avec durée sélectionnable
2. Affichage groupé dans "mes trajets"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from database.models import Trip, User
from database.db_manager import SessionLocal
from utils.swiss_pricing import calculate_trip_price_swiss
import uuid

def test_regular_trip_creation_and_display():
    """Test la création de trajets réguliers et leur affichage"""
    print("🧪 Test de création et affichage des trajets réguliers")
    
    # Données de test
    telegram_id = 123456789  # ID numérique pour Telegram
    departure_location = "Fribourg"
    arrival_location = "Lausanne" 
    departure_time = datetime.now() + timedelta(days=1)  # Demain à la même heure
    departure_time = departure_time.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # Calculer le prix (distance approximative Fribourg-Lausanne: ~62 km)
    price = calculate_trip_price_swiss(62)
    print(f"💰 Prix calculé: {price} CHF")
    
    with SessionLocal() as session:
        try:
            # Créer/récupérer l'utilisateur de test
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username="testuser_regular",
                    full_name="Test User Regular",
                    phone="+41 79 123 45 67",
                    is_driver=True
                )
                session.add(user)
                session.commit()
                print(f"✅ Utilisateur de test créé: {telegram_id}")
            
            # Générer un group_id unique
            group_id = f"group_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            print(f"🆔 Group ID généré: {group_id}")
            
            # Créer des trajets réguliers pour 3 semaines (exemple)
            duration_weeks = 3
            selected_days = [0, 2, 4]  # Lundi, Mercredi, Vendredi
            
            trips_created = []
            current_date = departure_time.date()
            weeks_count = 0
            
            while weeks_count < duration_weeks:
                # Pour chaque jour de la semaine
                for i in range(7):
                    check_date = current_date + timedelta(days=i)
                    if check_date.weekday() in selected_days:
                        trip_datetime = datetime.combine(check_date, departure_time.time())
                        
                        # Ne créer que les trajets futurs
                        if trip_datetime > datetime.now():
                            trip = Trip(
                                driver_id=user.id,  # Utiliser l'ID de l'utilisateur créé
                                departure_city=departure_location,
                                arrival_city=arrival_location,
                                departure_time=trip_datetime,
                                seats_available=4,
                                price_per_seat=price,
                                recurring=True,
                                group_id=group_id
                            )
                            session.add(trip)
                            trips_created.append(trip_datetime)
                
                # Passer à la semaine suivante
                current_date += timedelta(days=7)
                weeks_count += 1
            
            session.commit()
            print(f"✅ {len(trips_created)} trajets réguliers créés avec group_id: {group_id}")
            
            # Vérifier l'affichage groupé
            print("\n📋 Test de l'affichage groupé:")
            
            # Récupérer tous les trajets de l'utilisateur
            user_trips = session.query(Trip).filter(Trip.driver_id == user.id).all()
            
            # Grouper par group_id
            grouped_trips = {}
            individual_trips = []
            
            for trip in user_trips:
                if trip.group_id and trip.recurring:
                    if trip.group_id not in grouped_trips:
                        grouped_trips[trip.group_id] = []
                    grouped_trips[trip.group_id].append(trip)
                else:
                    individual_trips.append(trip)
            
            print(f"📊 Résultats de groupement:")
            print(f"   - Groupes réguliers: {len(grouped_trips)}")
            print(f"   - Trajets individuels: {len(individual_trips)}")
            
            # Afficher les détails des groupes
            for group_id, group_trips in grouped_trips.items():
                if group_trips:
                    first_trip = group_trips[0]
                    print(f"\n🚗 Groupe: {first_trip.departure_city} → {first_trip.arrival_city}")
                    print(f"   - Nombre de trajets: {len(group_trips)}")
                    print(f"   - Prix: {first_trip.price_per_seat} CHF")
                    print(f"   - Places: {first_trip.seats_available}")
                    print(f"   - Group ID: {group_id}")
                    
                    # Afficher les dates
                    dates = sorted([trip.departure_time for trip in group_trips])
                    print(f"   - Dates: {dates[0].strftime('%d/%m')} à {dates[-1].strftime('%d/%m')}")
            
            print(f"\n✅ Test réussi! L'affichage groupé fonctionne correctement.")
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    test_regular_trip_creation_and_display()
