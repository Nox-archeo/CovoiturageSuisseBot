#!/usr/bin/env python3
"""
Debug script pour analyser le problème de distance entre Fribourg et Düdingen
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.route_distance import get_route_distance_km, get_route_distance_with_fallback
from utils.swiss_pricing import calculate_trip_price_swiss, format_swiss_price
from geopy.distance import geodesic
import json

def load_cities():
    """Charge les données des villes"""
    with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['cities']

def find_city(cities, city_name):
    """Trouve une ville par nom"""
    for city in cities:
        if city['name'].lower() == city_name.lower():
            return city
    return None

def main():
    print("=== DEBUG FRIBOURG - DÜDINGEN ===")
    
    # Charger les villes
    cities = load_cities()
    
    # Trouver Fribourg et Düdingen
    fribourg = find_city(cities, "Fribourg")
    dudingen = find_city(cities, "Düdingen")
    
    if not fribourg:
        print("❌ Fribourg non trouvé")
        return
    
    if not dudingen:
        print("❌ Düdingen non trouvé")
        return
    
    print(f"✅ Fribourg trouvé: {fribourg}")
    print(f"✅ Düdingen trouvé: {dudingen}")
    print()
    
    # Coordonnées
    fribourg_coords = (fribourg['lat'], fribourg['lon'])
    dudingen_coords = (dudingen['lat'], dudingen['lon'])
    
    print(f"📍 Fribourg: {fribourg_coords}")
    print(f"📍 Düdingen: {dudingen_coords}")
    print()
    
    # Distance à vol d'oiseau (géodésique)
    geodesic_distance = geodesic(fribourg_coords, dudingen_coords).km
    print(f"🐦 Distance à vol d'oiseau: {geodesic_distance:.2f} km")
    
    # Distance routière avec OpenRouteService
    print("\n🛣️  Test distance routière OpenRouteService:")
    route_distance = get_route_distance_km(fribourg_coords, dudingen_coords, "Fribourg", "Düdingen")
    if route_distance:
        print(f"✅ Distance routière: {route_distance} km")
    else:
        print("❌ Échec calcul distance routière")
    
    # Distance avec fallback
    print("\n🔄 Test avec fallback:")
    fallback_distance, is_route = get_route_distance_with_fallback(fribourg_coords, dudingen_coords, "Fribourg", "Düdingen")
    if fallback_distance:
        distance_type = "routière" if is_route else "à vol d'oiseau (fallback)"
        print(f"📏 Distance utilisée: {fallback_distance} km ({distance_type})")
    else:
        print("❌ Échec total")
    
    # Calcul du prix avec le système actuel
    if fallback_distance:
        price = calculate_trip_price_swiss(fallback_distance)
        print(f"💰 Prix calculé: {format_swiss_price(price)} CHF")
        
        # Comparaison avec la vraie distance attendue
        expected_distance = 7.0  # Distance réelle attendue
        expected_price = calculate_trip_price_swiss(expected_distance)
        print(f"\n🎯 Comparaison:")
        print(f"   Distance attendue: {expected_distance} km")
        print(f"   Prix attendu: {format_swiss_price(expected_price)} CHF")
        print(f"   Différence distance: {abs(fallback_distance - expected_distance):.2f} km")
        print(f"   Différence prix: {abs(price - expected_price):.2f} CHF")
    
    print("\n" + "="*50)
    
    # Tests avec d'autres villes pour comparaison
    print("🧪 Tests de comparaison avec d'autres trajets:")
    
    test_routes = [
        ("Lausanne", "Genève"),
        ("Fribourg", "Bern"),
        ("Zurich", "Basel")
    ]
    
    for start_name, end_name in test_routes:
        start_city = find_city(cities, start_name)
        end_city = find_city(cities, end_name)
        
        if start_city and end_city:
            start_coords = (start_city['lat'], start_city['lon'])
            end_coords = (end_city['lat'], end_city['lon'])
            
            geodesic_dist = geodesic(start_coords, end_coords).km
            route_dist = get_route_distance_km(start_coords, end_coords)
            
            print(f"\n{start_name} → {end_name}:")
            print(f"  Vol d'oiseau: {geodesic_dist:.2f} km")
            if route_dist:
                print(f"  Routière: {route_dist} km")
                ratio = route_dist / geodesic_dist
                print(f"  Ratio route/vol d'oiseau: {ratio:.2f}")
            else:
                print(f"  Routière: ❌ ECHEC")

if __name__ == "__main__":
    main()
