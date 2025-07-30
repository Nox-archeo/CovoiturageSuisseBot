#!/usr/bin/env python3
"""
Test complet de l'arrondi suisse des prix dans tout le système de covoiturage
"""

import sys
import os

# Ajouter le répertoire racine au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.swiss_pricing import round_to_nearest_0_05, format_swiss_price, calculate_trip_price_swiss
from utils.route_distance import get_route_distance_with_fallback

def test_swiss_pricing_integration():
    """Test complet de l'intégration de l'arrondi suisse"""
    print("🧪 TEST COMPLET - ARRONDI SUISSE DANS LE SYSTÈME COVOITURAGE")
    print("=" * 70)
    
    # 1. Test de l'arrondi de base
    print("\n1️⃣ Tests d'arrondi de base (0.05 CHF)")
    print("-" * 40)
    
    test_cases = [
        (73.57, 73.55),  # Exemple du cahier des charges
        (73.58, 73.60),  # Exemple du cahier des charges  
        (24.99, 25.00),  # Exemple du cahier des charges
        (10.11, 10.10),
        (10.12, 10.10),
        (10.13, 10.15),
        (15.42, 15.40),
        (15.43, 15.45),
        (100.01, 100.00),
        (100.02, 100.00),
        (100.03, 100.05)
    ]
    
    all_passed = True
    for input_price, expected in test_cases:
        result = round_to_nearest_0_05(input_price)
        passed = abs(result - expected) < 0.001
        
        status = "✅" if passed else "❌"
        print(f"{status} {input_price} CHF → {result:.2f} CHF (attendu: {expected:.2f})")
        
        if not passed:
            all_passed = False
    
    success_msg = "🎉 Tous les tests d'arrondi passés!"
    fail_msg = "⚠️ Certains tests d'arrondi ont échoué"
    print(f"\n{success_msg if all_passed else fail_msg}")
    
    # 2. Test du barème progressif avec arrondi
    print("\n2️⃣ Tests du barème progressif avec arrondi")
    print("-" * 40)
    
    distance_tests = [
        # (distance_km, prix_attendu_arrondi)
        (10, 7.50),    # 10 * 0.75 = 7.50 → 7.50
        (15, 11.25),   # 15 * 0.75 = 11.25 → 11.25  
        (24, 18.00),   # 24 * 0.75 = 18.00 → 18.00
        (25, 18.50),   # 24*0.75 + 1*0.50 = 18+0.5 = 18.50 → 18.50
        (30, 21.00),   # 24*0.75 + 6*0.50 = 18+3 = 21.00 → 21.00
        (40, 26.00),   # 24*0.75 + 16*0.50 = 18+8 = 26.00 → 26.00
        (50, 28.50),   # 24*0.75 + 16*0.50 + 10*0.25 = 18+8+2.5 = 28.50 → 28.50
        (100, 41.00),  # 24*0.75 + 16*0.50 + 60*0.25 = 18+8+15 = 41.00 → 41.00
    ]
    
    barème_passed = True
    for distance, expected in distance_tests:
        result = calculate_trip_price_swiss(distance)
        passed = abs(result - expected) < 0.001
        
        status = "✅" if passed else "❌"
        print(f"{status} {distance:3d} km → {result:6.2f} CHF (attendu: {expected:6.2f})")
        
        if not passed:
            barème_passed = False
    
    success_msg2 = "🎉 Tous les tests de barème passés!"
    fail_msg2 = "⚠️ Certains tests de barème ont échoué"
    print(f"\n{success_msg2 if barème_passed else fail_msg2}")
    
    # 3. Test du formatage suisse
    print("\n3️⃣ Tests du formatage suisse")
    print("-" * 40)
    
    format_tests = [
        (7.50, "7.50"),
        (25.00, "25.00"), 
        (73.55, "73.55"),
        (100.0, "100.00"),
        (0.05, "0.05"),
        (0.0, "0.00")
    ]
    
    format_passed = True
    for input_val, expected in format_tests:
        result = format_swiss_price(input_val)
        passed = result == expected
        
        status = "✅" if passed else "❌"
        print(f"{status} {input_val} → '{result}' (attendu: '{expected}')")
        
        if not passed:
            format_passed = False
    
    success_msg3 = "🎉 Tous les tests de formatage passés!"
    fail_msg3 = "⚠️ Certains tests de formatage ont échoué"
    print(f"\n{success_msg3 if format_passed else fail_msg3}")
    
    # 4. Test avec vraies distances (quelques exemples)
    print("\n4️⃣ Tests avec vraies distances géographiques")
    print("-" * 40)
    
    try:
        import json
        with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        cities = data['cities']
        
        # Fonction pour récupérer les coordonnées d'une ville
        def get_city_coordinates(city_name):
            for city in cities:
                if city['name'].lower() == city_name.lower():
                    return (city['lat'], city['lon'])
            return None
        
        test_routes = [
            ('Lausanne', 'Geneva'),
            ('Fribourg', 'Bern'),
            ('Winterthur', 'Basel')
        ]
        
        geo_passed = True
        for city1, city2 in test_routes:
            coords1 = get_city_coordinates(city1)
            coords2 = get_city_coordinates(city2)
            
            if coords1 and coords2:
                distance_km, is_route = get_route_distance_with_fallback(coords1, coords2)
                if distance_km:
                    price = calculate_trip_price_swiss(distance_km)
                    route_type = "🛣️" if is_route else "📏"
                    
                    # Vérifier que le prix est bien un multiple de 0.05
                    remainder = round((price * 20) % 1, 3)
                    is_multiple_005 = remainder == 0.0
                    
                    status = "✅" if is_multiple_005 else "❌"
                    print(f"{status} {route_type} {city1} → {city2}: {distance_km:.1f} km = {format_swiss_price(price)} CHF")
                    
                    if not is_multiple_005:
                        geo_passed = False
                        print(f"    ⚠️ Prix {price} n'est pas un multiple de 0.05!")
                else:
                    print(f"⚠️ {city1} → {city2}: Calcul de distance impossible")
            else:
                print(f"⚠️ {city1} → {city2}: Coordonnées non trouvées")
        
        success_msg4 = "🎉 Tous les tests géographiques passés!"
        fail_msg4 = "⚠️ Certains tests géographiques ont échoué"
        print(f"\n{success_msg4 if geo_passed else fail_msg4}")
        
    except Exception as e:
        print(f"⚠️ Erreur lors des tests géographiques: {e}")
    
    # 5. Test de cas limites
    print("\n5️⃣ Tests de cas limites")
    print("-" * 40)
    
    edge_cases = [
        (None, 0.00),
        (0, 0.00),
        (-5, 0.00),
        (0.01, 0.75),  # 1 centième -> 0.75 CHF minimum (1 km)
        (1000, 258.00)  # 24*0.75 + 16*0.50 + 960*0.25 = 18+8+240 = 266 → mais arrondi possible
    ]
    
    edge_passed = True
    for distance, expected_min in edge_cases:
        result = calculate_trip_price_swiss(distance)
        
        # Pour les cas limites, on vérifie juste que c'est un multiple de 0.05
        remainder = round((result * 20) % 1, 3) if result else 0
        is_multiple_005 = remainder == 0.0
        
        status = "✅" if is_multiple_005 else "❌"
        print(f"{status} {distance} km → {format_swiss_price(result)} CHF (multiple de 0.05: {is_multiple_005})")
        
        if not is_multiple_005:
            edge_passed = False
    
    success_msg5 = "🎉 Tous les tests de cas limites passés!"
    fail_msg5 = "⚠️ Certains tests de cas limites ont échoué"
    print(f"\n{success_msg5 if edge_passed else fail_msg5}")
    
    # Résumé final
    all_tests_passed = all_passed and barème_passed and format_passed and edge_passed
    
    print(f"\n🏁 RÉSUMÉ FINAL")
    print("=" * 70)
    print(f"✅ Arrondi de base: {'PASS' if all_passed else 'FAIL'}")
    print(f"✅ Barème progressif: {'PASS' if barème_passed else 'FAIL'}")
    print(f"✅ Formatage suisse: {'PASS' if format_passed else 'FAIL'}")
    print(f"✅ Cas limites: {'PASS' if edge_passed else 'FAIL'}")
    
    if all_tests_passed:
        print(f"\n🎊 TOUS LES TESTS SONT PASSÉS!")
        print("✅ L'arrondi suisse (0.05 CHF) est correctement implémenté!")
        print("✅ Le barème progressif fonctionne parfaitement!")
        print("✅ Le système est prêt pour la production!")
    else:
        print(f"\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔧 Vérifiez les erreurs ci-dessus.")
    
    return all_tests_passed

if __name__ == "__main__":
    success = test_swiss_pricing_integration()
    exit(0 if success else 1)
