#!/usr/bin/env python3
"""
Script pour créer des trajets réguliers avec ton vrai ID Telegram
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from database.models import Trip, User
from database.db_manager import SessionLocal
from utils.swiss_pricing import calculate_trip_price_swiss
import uuid

def create_real_regular_trips():
    """Crée des trajets réguliers pour ton ID Telegram réel"""
    
    # REMPLACE CETTE VALEUR PAR TON VRAI ID TELEGRAM
    # Tu peux l'obtenir en envoyant /start au bot et en regardant les logs
    YOUR_TELEGRAM_ID = input("Entre ton ID Telegram: ")
    try:
        YOUR_TELEGRAM_ID = int(YOUR_TELEGRAM_ID)
    except:
        print("❌ ID Telegram invalide")
        return
    
    print(f"🧪 Création de trajets réguliers pour l'ID Telegram: {YOUR_TELEGRAM_ID}")
    
    # Données de test
    departure_location = "Fribourg"
    arrival_location = "Lausanne" 
    departure_time = datetime.now() + timedelta(days=1)  # Demain à la même heure
    departure_time = departure_time.replace(hour=10, minute=30, second=0, microsecond=0)
    
    # Calculer le prix (distance approximative Fribourg-Lausanne: ~50 km)
    price = calculate_trip_price_swiss(50)
    print(f"💰 Prix calculé: {price} CHF")
    
    with SessionLocal() as session:
        try:
            # Créer/récupérer l'utilisateur
            user = session.query(User).filter(User.telegram_id == YOUR_TELEGRAM_ID).first()
            if not user:
                # Créer l'utilisateur s'il n'existe pas
                user = User(
                    telegram_id=YOUR_TELEGRAM_ID,
                    username="testuser_real",
                    full_name="User Real",
                    phone="+41 79 123 45 67",
                    is_driver=True
                )
                session.add(user)
                session.commit()
                print(f"✅ Utilisateur créé: {YOUR_TELEGRAM_ID}")
            else:
                print(f"✅ Utilisateur trouvé: {YOUR_TELEGRAM_ID}")
            
            # Supprimer les anciens trajets de test
            old_trips = session.query(Trip).filter(Trip.driver_id == user.id).all()
            for trip in old_trips:
                session.delete(trip)
            session.commit()
            print(f"🗑️ Supprimé {len(old_trips)} anciens trajets")
            
            # Générer un group_id unique
            group_id = f"group_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            print(f"🆔 Group ID généré: {group_id}")
            
            # Créer des trajets réguliers pour 3 semaines
            duration_weeks = 3
            selected_days = [0, 2]  # Lundi, Mercredi
            
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
                                driver_id=user.id,
                                departure_city=departure_location,
                                arrival_city=arrival_location,
                                departure_time=trip_datetime,
                                seats_available=4,
                                price_per_seat=price,
                                recurring=True,
                                group_id=group_id,
                                is_published=True,  # IMPORTANT !
                                is_cancelled=False   # IMPORTANT !
                            )
                            session.add(trip)
                            trips_created.append(trip_datetime)
                
                # Passer à la semaine suivante
                current_date += timedelta(days=7)
                weeks_count += 1
            
            session.commit()
            print(f"✅ {len(trips_created)} trajets réguliers créés avec group_id: {group_id}")
            print(f"\n🎯 Maintenant va dans le bot et fais: Menu → Profil → Mes trajets")
            print(f"Tu devrais voir:")
            print(f"🔄 TRAJET RÉGULIER ({len(trips_created)} trajets)")
            print(f"📍 {departure_location} → {arrival_location}")
            print(f"💰 {price} CHF/place")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    create_real_regular_trips()
