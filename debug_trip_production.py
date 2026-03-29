#!/usr/bin/env python3
"""
Debug du trajet problématique sur la base PostgreSQL de production
"""

import os
import sys
sys.path.append('.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Trip, User
from dotenv import load_dotenv
from datetime import datetime, timedelta

def debug_production_trip():
    """Cherche le trajet Posieux → Corpataux-Magnedens sur la base de production"""
    
    load_dotenv()
    
    # URL de la base PostgreSQL de production (Render)
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL non trouvé dans .env")
        return
    
    print(f"🔗 Connexion à la base de production...")
    print(f"URL: {DATABASE_URL[:50]}...")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        # Chercher les trajets récents (dernières 48h)
        today = datetime.now()
        two_days_ago = today - timedelta(days=2)
        
        trips = db.query(Trip).filter(
            Trip.departure_time >= two_days_ago
        ).order_by(Trip.id.desc()).limit(20).all()
        
        print(f"\n🔍 TRAJETS RÉCENTS DE PRODUCTION ({len(trips)} trouvés):")
        
        posieux_trip = None
        
        for trip in trips:
            dep_city = trip.departure_city or ''
            arr_city = trip.arrival_city or ''
            
            print(f"\n📍 TRAJET {trip.id}:")
            print(f"  {dep_city} → {arr_city}")
            print(f"  Date: {trip.departure_time}")
            print(f"  Driver ID: {trip.driver_id}")
            print(f"  Status: {getattr(trip, 'status', 'NONE')}")
            
            # Chercher le trajet avec Posieux/Corpataux
            if ('posieux' in dep_city.lower() and 'corpataux' in arr_city.lower()) or \
               ('corpataux' in arr_city.lower() and 'magnedens' in arr_city.lower()):
                print(f"  🎯 MATCH! Trajet Posieux → Corpataux trouvé!")
                posieux_trip = trip
                
                # Analyser le conducteur
                if trip.driver_id:
                    driver = db.query(User).filter(User.id == trip.driver_id).first()
                    if driver:
                        print(f"    🚗 CONDUCTEUR: {driver.first_name} {driver.last_name}")
                        print(f"        Email PayPal: \"{driver.paypal_email}\"")
                        print(f"        Telegram ID: {driver.telegram_id}")
                    else:
                        print(f"    ❌ Driver ID {trip.driver_id} non trouvé")
                else:
                    print(f"    ❌ Driver ID est None")
                    
                    # Vérifier creator_id en cas de trajet passager
                    if hasattr(trip, 'creator_id') and trip.creator_id:
                        creator = db.query(User).filter(User.id == trip.creator_id).first()
                        if creator:
                            print(f"    👤 CRÉATEUR: {creator.first_name} {creator.last_name}")
                            print(f"        Email PayPal: \"{creator.paypal_email}\"")
        
        if not posieux_trip:
            print("\n❌ Aucun trajet Posieux → Corpataux trouvé dans les dernières 48h")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Erreur connexion base: {e}")

if __name__ == "__main__":
    debug_production_trip()
