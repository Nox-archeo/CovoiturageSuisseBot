#!/usr/bin/env python3
"""
Test des nouvelles villes ajoutées avec l'API de distance
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'handlers'))

from utils.route_distance import get_route_distance_with_fallback
from trip_handlers import get_coords
from geopy.distance import geodesic

def test_new_cities():
    """Test les nouvelles villes ajoutées"""
    
    # Principales nouvelles villes à tester
    new_cities = [
        "Zürich", "Basel", "Bern", "Winterthur", "Sankt Gallen", 
        "Lugano", "Biel", "Thun", "Chur", "Aarau"
    ]
    
    print("=== TEST DES NOUVELLES VILLES ===")
    
    # 1. Vérifier que toutes ont des coordonnées
    print("Vérification des coordonnées:")
    for city in new_cities:
        coords = get_coords(city)
        if coords and coords != (None, None):
            print(f"✅ {city}: {coords}")
        else:
            print(f"❌ {city}: Coordonnées manquantes")
    
    # 2. Tester quelques trajets avec les nouvelles villes
    test_routes = [
        ("Lausanne", "Zürich"),
        ("Genève", "Basel"),
        ("Fribourg", "Bern"), 
        ("Zürich", "Sankt Gallen"),
        ("Basel", "Bern"),
        ("Lugano", "Zürich"),
        ("Chur", "Sankt Gallen"),
        ("Biel", "Lausanne")
    ]
    
    print(f"\n=== TEST DE {len(test_routes)} TRAJETS AVEC NOUVELLES VILLES ===")
    
    api_success = 0
    fallback_used = 0
    errors = 0
    
    for i, (ville1, ville2) in enumerate(test_routes):
        print(f"\n--- Test {i+1}/{len(test_routes)}: {ville1} -> {ville2} ---")
        
        coords1 = get_coords(ville1)
        coords2 = get_coords(ville2)
        
        if not coords1 or coords1 == (None, None) or not coords2 or coords2 == (None, None):
            print(f"❌ Coordonnées manquantes")
            errors += 1
            continue
        
        # Distance à vol d'oiseau
        geodesic_distance = geodesic(coords1, coords2).kilometers
        
        # Distance routière
        route_distance, is_route = get_route_distance_with_fallback(coords1, coords2)
        
        if route_distance is None:
            print(f"❌ Erreur de calcul")
            errors += 1
            continue
        
        # Stats
        if is_route:
            status = "✅ API OpenRouteService"
            api_success += 1
        else:
            status = "⚠️ Fallback vol d'oiseau"
            fallback_used += 1
        
        diff_km = route_distance - geodesic_distance
        diff_pct = (diff_km / geodesic_distance) * 100 if geodesic_distance > 0 else 0
        
        print(f"Distance: {geodesic_distance:.1f} km → {route_distance:.1f} km ({status})")
        print(f"Différence: +{diff_km:.1f} km (+{diff_pct:.1f}%)")
        
        # Calcul du prix pour vérifier
        base_price = 0.5 if route_distance <= 50 else max(0.3, 0.5 - (route_distance - 50) * 0.01)
        calculated_price = route_distance * base_price
        print(f"Prix calculé: {calculated_price:.2f} CHF")
        
        # Pause pour l'API
        time.sleep(0.5)
    
    # Résumé
    total_tests = api_success + fallback_used + errors
    
    print(f"\n=== RÉSUMÉ POUR LES NOUVELLES VILLES ===")
    print(f"Trajets testés: {total_tests}")
    print(f"✅ API réussie: {api_success} ({api_success/total_tests*100:.1f}%)")
    print(f"⚠️ Fallback utilisé: {fallback_used} ({fallback_used/total_tests*100:.1f}%)")
    print(f"❌ Erreurs: {errors} ({errors/total_tests*100:.1f}%)")
    
    if api_success > fallback_used:
        print(f"\n🎉 EXCELLENT! La majorité des trajets vers/depuis les nouvelles villes utilisent l'API")
    else:
        print(f"\n⚠️ Les nouvelles villes fonctionnent mais beaucoup utilisent le fallback")

if __name__ == "__main__":
    test_new_cities()
