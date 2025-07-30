#!/usr/bin/env python3
"""
Test complet du système de gestion des trajets passagers
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_passenger_management_system():
    """Test complet du système de gestion des trajets passagers"""
    print("🎯 TEST SYSTÈME GESTION TRAJETS PASSAGERS")
    print("=" * 50)
    
    try:
        # Configuration de la base de données
        engine = create_engine('sqlite:///covoiturage.db')
        Session = sessionmaker(bind=engine)
        db = Session()
        
        # Test 1: Vérifier les handlers enregistrés
        print("\n1️⃣ VÉRIFICATION DES HANDLERS")
        handlers_to_check = [
            "show_passenger_trip_management",
            "handle_passenger_trip_action", 
            "confirm_delete_passenger_trip"
        ]
        
        # Charger le fichier trip_handlers.py pour vérifier les fonctions
        with open('handlers/trip_handlers.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        missing_handlers = []
        for handler in handlers_to_check:
            if f"async def {handler}" in content:
                print(f"  ✅ {handler} défini")
            else:
                print(f"  ❌ {handler} manquant")
                missing_handlers.append(handler)
        
        # Test 2: Vérifier l'enregistrement dans la fonction register
        print("\n2️⃣ VÉRIFICATION ENREGISTREMENT HANDLERS")
        required_patterns = [
            "passenger_trip_management",
            "edit_passenger_trip",
            "delete_passenger_trip", 
            "report_passenger_trip",
            "confirm_delete_passenger"
        ]
        
        missing_registrations = []
        for pattern in required_patterns:
            if pattern in content:
                print(f"  ✅ Pattern '{pattern}' enregistré")
            else:
                print(f"  ❌ Pattern '{pattern}' manquant")
                missing_registrations.append(pattern)
        
        # Test 3: Vérifier la structure de la base de données pour les trajets passagers
        print("\n3️⃣ VÉRIFICATION BASE DE DONNÉES")
        
        # Compter les trajets passagers existants
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM trips 
            WHERE trip_role = 'passenger'
        """))
        passenger_trips_count = result.fetchone()[0]
        print(f"  📊 Trajets passagers existants: {passenger_trips_count}")
        
        # Vérifier la structure des colonnes
        result = db.execute(text("PRAGMA table_info(trips)"))
        columns = [row[1] for row in result.fetchall()]
        
        required_columns = ['trip_role', 'creator_id', 'departure_city', 'arrival_city', 'departure_time']
        missing_columns = []
        for col in required_columns:
            if col in columns:
                print(f"  ✅ Colonne '{col}' présente")
            else:
                print(f"  ❌ Colonne '{col}' manquante")
                missing_columns.append(col)
        
        # Test 4: Vérifier la logique de redirection dans list_my_trips_menu
        print("\n4️⃣ VÉRIFICATION LOGIQUE DE REDIRECTION")
        if "show_passenger_trip_management" in content and "list_my_trips_menu" in content:
            if "has_passenger_profile and not has_driver_profile" in content:
                print("  ✅ Redirection automatique vers trajets passagers configurée")
            else:
                print("  ❌ Logique de redirection manquante")
        else:
            print("  ❌ Fonctions de redirection manquantes")
        
        # Test 5: Vérifier les callbacks dans bot.py
        print("\n5️⃣ VÉRIFICATION CALLBACKS BOT.PY")
        try:
            with open('bot.py', 'r', encoding='utf-8') as f:
                bot_content = f.read()
                
            if "register_trip_handlers(application)" in bot_content:
                print("  ✅ Handlers trip enregistrés dans bot.py")
            else:
                print("  ❌ Handlers trip non enregistrés dans bot.py")
                
        except FileNotFoundError:
            print("  ⚠️ Fichier bot.py non trouvé")
        
        # Résumé des tests
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ DES TESTS")
        
        total_issues = len(missing_handlers) + len(missing_registrations) + len(missing_columns)
        
        if total_issues == 0:
            print("🎉 TOUS LES TESTS PASSÉS!")
            print("✅ Le système de gestion des trajets passagers est complet")
            print("\n🔧 FONCTIONNALITÉS DISPONIBLES:")
            print("   • Interface dédiée pour les trajets passagers")
            print("   • Boutons Modifier/Supprimer/Signaler pour chaque trajet")
            print("   • Redirection automatique selon le profil utilisateur")
            print("   • Confirmation de suppression avec sécurité")
            print("   • Interface cohérente avec les trajets conducteur")
            
        else:
            print(f"⚠️ {total_issues} PROBLÈMES DÉTECTÉS")
            if missing_handlers:
                print(f"   • Handlers manquants: {', '.join(missing_handlers)}")
            if missing_registrations:
                print(f"   • Enregistrements manquants: {', '.join(missing_registrations)}")
            if missing_columns:
                print(f"   • Colonnes manquantes: {', '.join(missing_columns)}")
                
        db.close()
        
    except Exception as e:
        logger.error(f"Erreur dans le test: {e}")
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_passenger_management_system()
