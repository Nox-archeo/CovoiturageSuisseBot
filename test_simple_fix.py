#!/usr/bin/env python3
"""
Test simple de la correction Fribourg-Düdingen
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.route_distance import get_route_distance_with_fallback
from utils.swiss_pricing import calculate_trip_price_swiss, format_swiss_price
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
    print("=== TEST SIMPLE CORRECTION FRIBOURG → DÜDINGEN ===")
    
    cities = load_cities()
    fribourg = find_city(cities, "Fribourg")
    dudingen = find_city(cities, "Düdingen")
    
    if not fribourg or not dudingen:
        print("❌ Villes non trouvées")
        return
    
    # Coordonnées
    fribourg_coords = (fribourg['lat'], fribourg['lon'])
    dudingen_coords = (dudingen['lat'], dudingen['lon'])
    
    print(f"📍 {fribourg['name']}: {fribourg_coords}")
    print(f"📍 {dudingen['name']}: {dudingen_coords}")
    
    # Calcul avec notre nouvelle API
    print(f"\n🔧 APRÈS CORRECTION:")
    distance, is_route = get_route_distance_with_fallback(
        fribourg_coords, dudingen_coords, 
        fribourg['name'], dudingen['name']
    )
    
    if distance:
        price = calculate_trip_price_swiss(distance)
        distance_type = "routière" if is_route else "à vol d'oiseau"
        print(f"  Distance ({distance_type}): {distance} km")
        print(f"  Prix: {format_swiss_price(price)} CHF")
    
    # Calcul avec l'ancienne API (sans noms de villes)
    print(f"\n⚠️ AVANT CORRECTION:")
    old_distance, old_is_route = get_route_distance_with_fallback(fribourg_coords, dudingen_coords)
    
    if old_distance:
        old_price = calculate_trip_price_swiss(old_distance)
        old_distance_type = "routière" if old_is_route else "à vol d'oiseau"
        print(f"  Distance ({old_distance_type}): {old_distance} km")
        print(f"  Prix: {format_swiss_price(old_price)} CHF")
    
    # Comparaison
    if distance and old_distance:
        print(f"\n📊 IMPACT DE LA CORRECTION:")
        print(f"  Réduction distance: {old_distance - distance:.2f} km ({((old_distance - distance) / old_distance * 100):.1f}%)")
        print(f"  Réduction prix: {old_price - price:.2f} CHF ({((old_price - price) / old_price * 100):.1f}%)")
        
        if is_route and not old_is_route:
            print(f"  ✅ Passage du fallback à la vraie distance routière")
        elif is_route and old_is_route:
            print(f"  ✅ Amélioration du calcul de distance routière")

if __name__ == "__main__":
    main()
