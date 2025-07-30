#!/usr/bin/env python3
"""
Comparaison des deux fichiers de communes pour voir s'il y a des différences
"""

import json
import os

def compare_commune_files():
    """Compare les deux fichiers de communes"""
    
    print("=== COMPARAISON DES FICHIERS DE COMMUNES ===")
    
    # Charger cities.json (utilisé par le bot)
    cities_path = 'src/bot/data/cities.json'
    with open(cities_path, 'r', encoding='utf-8') as f:
        cities_data = json.load(f)
    
    cities_names = set()
    cities_with_coords = set()
    cities_without_coords = set()
    
    for city in cities_data['cities']:
        name = city['name']
        cities_names.add(name)
        
        if 'lat' in city and 'lon' in city and city['lat'] is not None and city['lon'] is not None:
            cities_with_coords.add(name)
        else:
            cities_without_coords.add(name)
    
    print(f"cities.json (utilisé par le bot):")
    print(f"  Total: {len(cities_names)} communes")
    print(f"  Avec coordonnées: {len(cities_with_coords)}")
    print(f"  Sans coordonnées: {len(cities_without_coords)}")
    
    # Charger swiss_localities.json  
    localities_path = 'data/swiss_localities.json'
    with open(localities_path, 'r', encoding='utf-8') as f:
        localities_data = json.load(f)
    
    localities_names = set(localities_data.keys())
    
    print(f"\nswiss_localities.json:")
    print(f"  Total: {len(localities_names)} communes")
    
    # Comparaison
    print(f"\n=== COMPARAISON ===")
    
    # Communes dans cities.json mais pas dans swiss_localities.json
    only_in_cities = cities_names - localities_names
    print(f"Uniquement dans cities.json: {len(only_in_cities)}")
    if only_in_cities:
        print("  Exemples:", list(only_in_cities)[:10])
    
    # Communes dans swiss_localities.json mais pas dans cities.json
    only_in_localities = localities_names - cities_names
    print(f"Uniquement dans swiss_localities.json: {len(only_in_localities)}")
    if only_in_localities:
        print("  Exemples:", list(only_in_localities)[:10])
    
    # Communes communes
    common = cities_names & localities_names
    print(f"Communes communes: {len(common)}")
    
    # Test de quelques communes sans coordonnées
    if cities_without_coords:
        print(f"\n=== COMMUNES SANS COORDONNÉES (dans cities.json) ===")
        print("Exemples:", list(cities_without_coords)[:20])
        
        # Vérifier si on peut récupérer des coordonnées pour ces communes
        print(f"\nCes communes ont-elles des coordonnées dans swiss_localities.json ?")
        for commune in list(cities_without_coords)[:5]:
            if commune in localities_data:
                print(f"  {commune}: Présente dans swiss_localities.json")
            else:
                print(f"  {commune}: Absente de swiss_localities.json")
    
    # Vérifier quelques exemples de coordonnées
    print(f"\n=== EXEMPLES DE COORDONNÉES ===")
    test_cities = ["Lausanne", "Fribourg", "Genève"]
    
    for city in test_cities:
        # Dans cities.json
        city_data = None
        for c in cities_data['cities']:
            if c['name'] == city:
                city_data = c
                break
        
        if city_data:
            print(f"{city} (cities.json): lat={city_data.get('lat')}, lon={city_data.get('lon')}")
        else:
            print(f"{city} (cities.json): Non trouvé")
        
        # Dans swiss_localities.json - pas de coordonnées dans ce fichier
        if city in localities_data:
            print(f"{city} (swiss_localities.json): Présent (mais pas de coordonnées)")
        else:
            print(f"{city} (swiss_localities.json): Non trouvé")

if __name__ == "__main__":
    compare_commune_files()
