#!/usr/bin/env python3
"""
Test complet pour vérifier que toutes les communes importantes utilisent l'API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'handlers'))

from utils.route_distance import get_route_distance_with_fallback
from trip_handlers import get_coords
from geopy.distance import geodesic
import time

def test_all_major_cities():
    """Test toutes les principales villes suisses"""
    
    # Principales villes suisses (avec vrais noms)
    major_cities = [
        "Lausanne", "Genève", "Fribourg", "Luzern", "Neuchâtel", "Sion", 
        "Montreux", "Vevey", "Yverdon-les-Bains", "Bulle", "Morges", "Nyon", 
        "Delémont", "Martigny", "Aigle", "Sierre"
    ]
    
    print("=== VÉRIFICATION DES COORDONNÉES DES VILLES ===\n")
    
    # 1. Vérifier d'abord quelles villes ont des coordonnées
    available_cities = []
    for city in major_cities:
        coords = get_coords(city)
        if coords and coords != (None, None):
            available_cities.append(city)
            print(f"✅ {city}: {coords}")
        else:
            print(f"❌ {city}: Coordonnées non trouvées")
    
    print(f"\n=== {len(available_cities)} villes disponibles ===")
    print("Cities:", ", ".join(available_cities))
    
    # 2. Tester quelques trajets représentatifs
    test_routes = [
        ("Lausanne", "Genève"),
        ("Fribourg", "Lausanne"), 
        ("Lausanne", "Luzern"),  # Ajout de Lucerne
        ("Genève", "Luzern"),    # Test longue distance
        ("Fribourg", "Genève"),
        ("Lausanne", "Montreux"),
        ("Neuchâtel", "Lausanne"),
        ("Sion", "Lausanne"),
        ("Bulle", "Fribourg"),
        ("Morges", "Lausanne"),
        ("Yverdon-les-Bains", "Lausanne"),  # Nouveau
        ("Delémont", "Lausanne")  # Test distance moyenne
    ]
    
    print(f"\n=== TEST DE {len(test_routes)} TRAJETS REPRÉSENTATIFS ===\n")
    
    api_success_count = 0
    fallback_count = 0
    error_count = 0
    
    for start_city, end_city in test_routes:
        print(f"--- {start_city} -> {end_city} ---")
        
        # Vérifier que les deux villes sont disponibles
        if start_city not in available_cities or end_city not in available_cities:
            print(f"⚠️ Villes non disponibles")
            error_count += 1
            continue
        
        start_coords = get_coords(start_city)
        end_coords = get_coords(end_city)
        
        # Distance à vol d'oiseau
        geodesic_distance = geodesic(start_coords, end_coords).kilometers
        
        # Distance routière avec fallback
        route_distance, is_route = get_route_distance_with_fallback(start_coords, end_coords)
        
        if route_distance is None:
            print(f"❌ Erreur de calcul")
            error_count += 1
            continue
        
        # Calculer la différence
        diff_km = route_distance - geodesic_distance
        diff_pct = (diff_km / geodesic_distance) * 100 if geodesic_distance > 0 else 0
        
        if is_route:
            status = "✅ API OpenRouteService"
            api_success_count += 1
        else:
            status = "⚠️ Fallback vol d'oiseau"
            fallback_count += 1
            
        print(f"Distance: {geodesic_distance:.1f} km → {route_distance:.1f} km ({status})")
        print(f"Différence: +{diff_km:.1f} km (+{diff_pct:.1f}%)")
        
        # Calcul du prix pour voir l'impact
        base_price = 0.5 if route_distance <= 50 else max(0.3, 0.5 - (route_distance - 50) * 0.01)
        calculated_price = route_distance * base_price
        print(f"Prix: {calculated_price:.2f} CHF")
        print()
        
        # Petite pause pour ne pas surcharger l'API
        time.sleep(0.5)
    
    # Résumé
    total_tests = api_success_count + fallback_count + error_count
    print("=== RÉSUMÉ ===")
    print(f"Total des tests: {total_tests}")
    print(f"✅ API réussie: {api_success_count} ({api_success_count/total_tests*100:.1f}%)")
    print(f"⚠️ Fallback utilisé: {fallback_count} ({fallback_count/total_tests*100:.1f}%)")
    print(f"❌ Erreurs: {error_count} ({error_count/total_tests*100:.1f}%)")
    
    if api_success_count > fallback_count:
        print("\n🎉 EXCELLENT! La majorité des trajets utilisent l'API OpenRouteService")
    elif api_success_count > 0:
        print("\n✅ BON! Certains trajets utilisent l'API, d'autres le fallback")
    else:
        print("\n⚠️ ATTENTION! Aucun trajet n'utilise l'API OpenRouteService")

if __name__ == "__main__":
    test_all_major_cities()
