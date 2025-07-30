#!/usr/bin/env python3
"""
Script de débogage pour tester la création de trajets réguliers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from database.models import User, Trip
from handlers.create_trip_handler import create_regular_trips
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MockContext:
    def __init__(self):
        self.user_data = {
            'departure': {'name': 'Fribourg'},
            'arrival': {'name': 'Lausanne'},
            'selected_days': ['Lundi', 'Mercredi'],
            'regular_time': '08:30',
            'regular_hour': 8,
            'regular_minute': 30,
            'regular_weeks': 2,  # 2 semaines
            'seats': 3,
            'price': 15.50,
            'trip_options': {
                'smoking': 'no_smoking',
                'music': 'music_ok',
                'talk': 'depends',
                'pets': 'no_pets',
                'luggage': 'medium',
                'stops': '',
                'highway': True,
                'flexible_time': False,
                'women_only': False,
                'instant_booking': True
            },
            'meeting_point': 'Gare de Fribourg',
            'car_description': 'Volkswagen Golf blanche',
            'distance_km': 45.2,
            'estimated_duration': 35,
            'additional_info': 'Trajet régulier test'
        }

async def test_create_regular_trips():
    """Test de création de trajets réguliers"""
    
    # Trouver un utilisateur existant
    db = get_db()
    user = db.query(User).first()
    
    if not user:
        print("❌ Aucun utilisateur trouvé dans la base")
        return
    
    print(f"👤 Utilisateur trouvé: {user.telegram_id}")
    
    # Créer un contexte mock
    context = MockContext()
    
    print("📊 Données du contexte:")
    for key, value in context.user_data.items():
        print(f"  {key}: {value}")
    
    # Tester la création
    print("\n🚀 Test de création des trajets réguliers...")
    
    try:
        created_trips = await create_regular_trips(context, user.telegram_id)
        
        if created_trips:
            print(f"✅ {len(created_trips)} trajets créés avec succès!")
            
            for i, trip in enumerate(created_trips, 1):
                print(f"  {i}. {trip.departure_city} → {trip.arrival_city}")
                print(f"     Date: {trip.departure_time}")
                print(f"     Group ID: {trip.group_id}")
                print(f"     Recurring: {trip.recurring}")
                print(f"     Published: {trip.is_published}")
        else:
            print("❌ Aucun trajet créé - voir les logs d'erreur")
            
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        logger.error(f"Erreur: {e}", exc_info=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_create_regular_trips())
