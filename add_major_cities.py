#!/usr/bin/env python3
"""
Script intelligent pour ajouter les principales villes manquantes avec géocodage automatique
"""

import json
import time
import requests
from typing import Dict, List, Optional, Tuple

def geocode_city(city_name: str, canton: str) -> Optional[Tuple[float, float]]:
    """
    Géocode une ville en utilisant l'API Nominatim (OpenStreetMap)
    """
    try:
        # Construire la requête de géocodage
        query = f"{city_name}, {canton}, Switzerland"
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'ch',  # Limiter à la Suisse
        }
        
        headers = {
            'User-Agent': 'CovoiturageSuisse-Bot/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                return lat, lon
        
        return None
        
    except Exception as e:
        print(f"Erreur géocodage pour {city_name}: {e}")
        return None

def add_major_missing_cities():
    """Ajoute les principales villes suisses manquantes"""
    
    print("=== AJOUT DES PRINCIPALES VILLES MANQUANTES ===")
    
    # Principales villes suisses manquantes avec leurs cantons
    missing_major_cities = [
        ("Zürich", "ZH", "8000"),
        ("Basel", "BS", "4000"),
        ("Bern", "BE", "3000"),
        ("Winterthur", "ZH", "8400"),
        ("Sankt Gallen", "SG", "9000"),
        ("Lugano", "TI", "6900"),
        ("Biel", "BE", "2500"),
        ("Thun", "BE", "3600"),
        ("Köniz", "BE", "3098"),
        ("Schaffhausen", "SH", "8200"),
        ("Chur", "GR", "7000"),
        ("Uster", "ZH", "8610"),
        ("Zug", "ZG", "6300"),
        ("Rapperswil-Jona", "SG", "8640"),
        ("Dübendorf", "ZH", "8600"),
        ("Dietikon", "ZH", "8953"),
        ("Frauenfeld", "TG", "8500"),
        ("Wetzikon", "ZH", "8620"),
        ("Aarau", "AG", "5000"),
        ("Bellinzona", "TI", "6500"),
        ("Olten", "SO", "4600"),
        ("Solothurn", "SO", "4500"),
        ("Kriens", "LU", "6010"),
        ("Emmen", "LU", "6020"),
        ("Vernier", "GE", "1214"),
        ("Meyrin", "GE", "1217"),
        ("Carouge", "GE", "1227")
    ]
    
    # Charger les données existantes
    with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    
    existing_names = {city['name'] for city in existing_data['cities']}
    
    print(f"Communes existantes: {len(existing_names)}")
    
    # Identifier les villes vraiment manquantes
    truly_missing = []
    for city_name, canton, npa in missing_major_cities:
        if city_name not in existing_names:
            truly_missing.append((city_name, canton, npa))
        else:
            print(f"✅ {city_name} déjà présent")
    
    print(f"Villes manquantes à ajouter: {len(truly_missing)}")
    
    if not truly_missing:
        print("🎉 Toutes les principales villes sont déjà présentes!")
        return
    
    # Géocoder et ajouter les villes manquantes
    new_cities = []
    success_count = 0
    
    for i, (city_name, canton, npa) in enumerate(truly_missing):
        print(f"\nGéocodage {i+1}/{len(truly_missing)}: {city_name} ({canton})")
        
        coords = geocode_city(city_name, canton)
        
        if coords:
            lat, lon = coords
            new_city = {
                "name": city_name,
                "canton": canton,
                "npa": npa,
                "lat": lat,
                "lon": lon
            }
            new_cities.append(new_city)
            success_count += 1
            print(f"✅ {city_name}: {lat:.6f}, {lon:.6f}")
        else:
            print(f"❌ Échec du géocodage pour {city_name}")
        
        # Pause pour respecter l'API
        time.sleep(1)
    
    print(f"\n=== RÉSUMÉ ===")
    print(f"Villes géocodées avec succès: {success_count}/{len(truly_missing)}")
    
    if new_cities:
        # Créer la sauvegarde
        backup_data = {
            "cities": existing_data['cities']
        }
        
        with open('src/bot/data/cities_backup.json', 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print("✅ Sauvegarde créée: cities_backup.json")
        
        # Ajouter les nouvelles villes
        all_cities = existing_data['cities'] + new_cities
        
        # Trier par canton puis par nom
        all_cities.sort(key=lambda x: (x.get('canton', ''), x['name']))
        
        new_data = {
            "cities": all_cities
        }
        
        # Sauvegarder
        with open('src/bot/data/cities.json', 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Ajouté {len(new_cities)} nouvelles villes au fichier cities.json")
        print(f"Total des communes: {len(all_cities)}")
        
        # Afficher les nouvelles villes ajoutées
        print(f"\n🏙️ NOUVELLES VILLES AJOUTÉES:")
        for city in new_cities:
            print(f"   {city['name']} ({city['canton']}) - {city['npa']}")
    
    else:
        print("❌ Aucune nouvelle ville n'a pu être géocodée")

def verify_new_cities():
    """Vérifie que les nouvelles villes ont bien été ajoutées"""
    
    print("\n=== VÉRIFICATION ===")
    
    with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Analyser par canton
    by_canton = {}
    for city in data['cities']:
        canton = city.get('canton', 'XX')
        if canton not in by_canton:
            by_canton[canton] = []
        by_canton[canton].append(city['name'])
    
    print(f"Total des communes: {len(data['cities'])}")
    print(f"Cantons représentés: {len(by_canton)}")
    
    for canton in sorted(by_canton.keys()):
        print(f"  {canton}: {len(by_canton[canton])} communes")

if __name__ == "__main__":
    try:
        add_major_missing_cities()
        verify_new_cities()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("💡 Conseil: Vérifiez votre connexion internet pour le géocodage")
