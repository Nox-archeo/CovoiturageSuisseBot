#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour créer des données de test pour les propositions de service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from database import get_db
from database.models import Trip, User

def create_test_passenger_trip():
    """Crée un trajet de test pour un passager"""
    db = get_db()
    
    # Créer un utilisateur test passager
    test_passenger = User(
        telegram_id=999999999,  # ID fictif pour test
        username="test_passenger",
        full_name="Test Passager",
        is_passenger=True,
        is_driver=False
    )
    
    # Vérifier s'il existe déjà
    existing_user = db.query(User).filter_by(telegram_id=999999999).first()
    if existing_user:
        test_passenger = existing_user
        print("👤 Utilisateur test trouvé")
    else:
        db.add(test_passenger)
        db.commit()
        db.refresh(test_passenger)
        print("👤 Nouvel utilisateur test créé")
    
    # Créer un trajet test
    test_trip = Trip(
        creator_id=test_passenger.id,
        departure_city="Lausanne",
        arrival_city="Genève",
        departure_time=datetime.now() + timedelta(days=1),
        trip_role="passenger",
        seats_available=2,
        price_per_seat=25.0,
        additional_info="Trajet de test pour les propositions de service",
        is_published=True,
        is_cancelled=False
    )
    
    db.add(test_trip)
    db.commit()
    db.refresh(test_trip)
    
    print(f"✅ Trajet de test créé:")
    print(f"   ID: {test_trip.id}")
    print(f"   De: {test_trip.departure_city}")
    print(f"   Vers: {test_trip.arrival_city}")
    print(f"   Date: {test_trip.departure_time}")
    print(f"   Prix: {test_trip.price_per_seat} CHF/place")
    print(f"   Places: {test_trip.seats_available}")
    
    print(f"\n🔥 Pour tester, utilise l'ID du trajet: {test_trip.id}")
    print("💡 Va dans Vue rapide et clique sur 'Proposer mes services' pour ce trajet")
    
    db.close()
    return test_trip

if __name__ == "__main__":
    print("🚗 Création d'un trajet de test pour les propositions de service...")
    create_test_passenger_trip()
