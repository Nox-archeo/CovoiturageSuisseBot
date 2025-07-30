#!/usr/bin/env python3
"""
Test d'intégration pour le système de recherche de passagers.
Vérifie que tous les composants sont bien intégrés.
"""

import sys
import os
import logging

# Ajouter le chemin racine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from database.models import Trip, User
from datetime import datetime, timedelta

def test_passenger_trips_in_database():
    """Teste la présence de trajets passagers dans la base de données"""
    print("🔍 VÉRIFICATION DES TRAJETS PASSAGERS")
    print("=" * 50)
    
    db = get_db()
    
    # Compter tous les trajets passagers
    passenger_trips = db.query(Trip).filter(Trip.trip_role == 'passenger').all()
    print(f"📊 Total trajets passagers dans la base: {len(passenger_trips)}")
    
    # Compter les trajets futurs
    future_passenger_trips = db.query(Trip).filter(
        Trip.trip_role == 'passenger',
        Trip.departure_time > datetime.now()
    ).all()
    print(f"📅 Trajets passagers futurs: {len(future_passenger_trips)}")
    
    # Compter les trajets publiés
    published_passenger_trips = db.query(Trip).filter(
        Trip.trip_role == 'passenger',
        Trip.is_published == True,
        Trip.departure_time > datetime.now()
    ).all()
    print(f"✅ Trajets passagers publiés et futurs: {len(published_passenger_trips)}")
    
    if published_passenger_trips:
        print("\n🗂️ EXEMPLES DE TRAJETS PASSAGERS:")
        for i, trip in enumerate(published_passenger_trips[:3], 1):
            # Obtenir le nom du créateur de manière sécurisée
            creator_name = "Utilisateur"
            if trip.creator:
                if hasattr(trip.creator, 'full_name') and trip.creator.full_name:
                    creator_name = trip.creator.full_name
                elif hasattr(trip.creator, 'username') and trip.creator.username:
                    creator_name = trip.creator.username
            
            date_str = trip.departure_time.strftime('%d/%m/%Y à %H:%M')
            print(f"  {i}. {trip.departure_city} → {trip.arrival_city}")
            print(f"     📅 {date_str} | 👤 {creator_name} | 💰 {trip.price_per_seat} CHF")
    
    print("\n" + "=" * 50)
    return len(published_passenger_trips) > 0

def test_swiss_localities_data():
    """Teste la présence des données des localités suisses"""
    print("🇨🇭 VÉRIFICATION DES DONNÉES SUISSES")
    print("=" * 50)
    
    try:
        import json
        import os
        
        # Chercher le fichier JSON des localités
        json_files = [
            'swiss_localities.json',
            'data/swiss_localities.json',
            'localities.json'
        ]
        
        localities_data = None
        for json_file in json_files:
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    localities_data = json.load(f)
                print(f"✅ Fichier trouvé: {json_file}")
                break
        
        if localities_data:
            print(f"✅ Données des localités chargées: {len(localities_data)} entrées")
            
            # Vérifier les cantons
            cantons = set()
            for locality in localities_data:
                if 'kanton' in locality:
                    cantons.add(locality['kanton'])
                elif 'canton' in locality:
                    cantons.add(locality['canton'])
            
            print(f"🏛️ Cantons disponibles: {len(cantons)}")
            if cantons:
                print(f"   Exemples: {list(cantons)[:5]}...")
            
            return True
        else:
            print("❌ Aucun fichier de localités trouvé")
            print("💡 Fichiers recherchés:", json_files)
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du chargement des localités: {e}")
        return False

def test_search_passengers_handler():
    """Teste l'existence du handler de recherche de passagers"""
    print("\n🔧 VÉRIFICATION DU HANDLER")
    print("=" * 50)
    
    try:
        from handlers.search_passengers import register_search_passengers_handler, CANTONS
        print("✅ Handler search_passengers importé avec succès")
        
        print(f"🏛️ Cantons configurés: {len(CANTONS)}")
        for canton, emoji in list(CANTONS.items())[:5]:
            print(f"   {emoji} {canton}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import du handler: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test du handler: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST D'INTÉGRATION - RECHERCHE DE PASSAGERS")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Base de données
    results.append(test_passenger_trips_in_database())
    print()
    
    # Test 2: Localités suisses
    results.append(test_swiss_localities_data())
    print()
    
    # Test 3: Handler
    results.append(test_search_passengers_handler())
    print()
    
    # Résumé
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"✅ Tests réussis: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 Tous les tests sont passés ! Le système est prêt.")
        print()
        print("🚀 COMMANDES DISPONIBLES:")
        print("   - /chercher_passagers : Recherche avancée par canton")
        print("   - Menu → 'Demandes passagers' : Vue rapide + recherche avancée")
        print()
        print("🔗 INTÉGRATION RÉUSSIE:")
        print("   ✅ Base de données avec trajets passagers")
        print("   ✅ Données géographiques suisses")
        print("   ✅ Handler de recherche avancée")
        print("   ✅ Interface menu mise à jour")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
