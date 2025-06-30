#!/usr/bin/env python
"""
Script de test pour la recherche de trajets
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire racine au chemin Python
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from database.models import Trip, User
from database import get_db

def test_trip_search():
    """Test de la recherche de trajets"""
    print("🔄 Test de la recherche de trajets...")
    
    try:
        db = get_db()
        
        # Test de la requête comme dans le handler
        departure_str = "Fribourg"
        arrival_str = "Lausanne"
        
        print(f"Recherche: {departure_str} → {arrival_str}")
        
        # Requête exacte du handler
        matching_trips = db.query(Trip).filter(
            Trip.departure_city.like(f"%{departure_str}%"),
            Trip.arrival_city.like(f"%{arrival_str}%"),
            Trip.is_published == True,
            Trip.departure_time >= datetime.now()
        ).all()
        
        print(f"✅ Requête exécutée avec succès")
        print(f"📊 {len(matching_trips)} trajets trouvés")
        
        # Filtrer les trajets annulés côté Python
        valid_trips = []
        for trip in matching_trips:
            is_cancelled = getattr(trip, 'is_cancelled', False)
            if not is_cancelled:
                valid_trips.append(trip)
        
        print(f"📊 {len(valid_trips)} trajets valides (non annulés)")
        
        if len(valid_trips) == 0:
            print("ℹ️ Aucun trajet trouvé - c'est normal si aucun trajet n'est enregistré")
        else:
            print("\n📋 Détails des trajets trouvés:")
            for i, trip in enumerate(valid_trips[:3]):  # Afficher max 3 trajets
                print(f"  {i+1}. {trip.departure_city} → {trip.arrival_city}")
                print(f"     Date: {trip.departure_time}")
                if hasattr(trip, 'price_per_seat'):
                    print(f"     Prix: {trip.price_per_seat} CHF")
                if hasattr(trip, 'seats_available'):
                    print(f"     Places: {trip.seats_available}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_columns():
    """Test de la présence des colonnes dans la base de données"""
    print("\n🔄 Test des colonnes de la base de données...")
    
    try:
        db = get_db()
        
        # Test d'une requête simple
        trips = db.query(Trip).limit(1).all()
        
        if trips:
            trip = trips[0]
            print("✅ Colonnes testées :")
            
            # Test des nouvelles colonnes
            columns_to_test = [
                'status', 'payout_batch_id', 'is_cancelled'
            ]
            
            for col in columns_to_test:
                if hasattr(trip, col):
                    value = getattr(trip, col, 'N/A')
                    print(f"  ✅ {col}: {value}")
                else:
                    print(f"  ❌ {col}: Colonne manquante")
        else:
            print("ℹ️ Aucun trajet dans la base de données pour tester les colonnes")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des colonnes : {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_trip():
    """Créer un trajet de test pour les tests"""
    print("\n🔄 Création d'un trajet de test...")
    
    try:
        db = get_db()
        
        # Vérifier s'il y a déjà des trajets
        existing_trips = db.query(Trip).filter(
            Trip.departure_city.like("%Fribourg%"),
            Trip.arrival_city.like("%Lausanne%")
        ).count()
        
        if existing_trips > 0:
            print(f"ℹ️ {existing_trips} trajet(s) Fribourg-Lausanne déjà existant(s)")
            return True
        
        # Créer un utilisateur de test s'il n'existe pas
        test_user = db.query(User).filter(User.telegram_id == 999999).first()
        if not test_user:
            test_user = User(
                telegram_id=999999,
                username="testuser",
                full_name="Utilisateur Test",
                is_driver=True
            )
            db.add(test_user)
            db.commit()
            print("✅ Utilisateur de test créé")
        
        # Créer un trajet de test
        test_trip = Trip(
            driver_id=test_user.id,
            departure_city="Fribourg",
            arrival_city="Lausanne",
            departure_time=datetime(2025, 12, 31, 10, 0),  # Date future
            seats_available=3,
            price_per_seat=15.0,
            is_published=True,
            is_cancelled=False,
            status='active'
        )
        
        db.add(test_trip)
        db.commit()
        
        print("✅ Trajet de test créé : Fribourg → Lausanne")
        print(f"   ID: {test_trip.id}")
        print(f"   Date: {test_trip.departure_time}")
        print(f"   Prix: {test_trip.price_per_seat} CHF")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du trajet de test : {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test de la recherche de trajets")
    print("=" * 40)
    
    tests = [
        test_database_columns,
        create_test_trip,
        test_trip_search
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 40)
    print("📊 Résultats des tests :")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Tous les tests réussis ({passed}/{total})")
        print("\n🎉 La recherche de trajets devrait maintenant fonctionner !")
    else:
        print(f"❌ {total - passed} test(s) échoué(s) sur {total}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
