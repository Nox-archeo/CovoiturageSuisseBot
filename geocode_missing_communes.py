#!/usr/bin/env python3
"""
Script pour géocoder automatiquement les communes suisses sans coordonnées GPS.
Utilise l'API Nominatim d'OpenStreetMap (gratuite, sans clé d'API).
"""

import json
import time
import requests
from typing import Dict, Optional, Tuple
import sys

def geocode_city(city_name: str, canton: str, country: str = "Switzerland") -> Optional[Tuple[float, float]]:
    """
    Géocode une ville en utilisant l'API Nominatim.
    
    Args:
        city_name: Nom de la ville
        canton: Code du canton (ex: "VD", "GE")
        country: Pays (défaut: "Switzerland")
    
    Returns:
        Tuple (latitude, longitude) ou None si non trouvé
    """
    # Mapping des codes cantons vers les noms complets
    canton_names = {
        'AG': 'Aargau', 'AI': 'Appenzell Innerrhoden', 'AR': 'Appenzell Ausserrhoden',
        'BE': 'Bern', 'BL': 'Basel-Landschaft', 'BS': 'Basel-Stadt',
        'FR': 'Fribourg', 'GE': 'Geneva', 'GL': 'Glarus', 'GR': 'Graubünden',
        'JU': 'Jura', 'LU': 'Lucerne', 'NE': 'Neuchâtel', 'NW': 'Nidwalden',
        'OW': 'Obwalden', 'SG': 'St. Gallen', 'SH': 'Schaffhausen', 'SO': 'Solothurn',
        'SZ': 'Schwyz', 'TG': 'Thurgau', 'TI': 'Ticino', 'UR': 'Uri',
        'VD': 'Vaud', 'VS': 'Valais', 'ZG': 'Zug', 'ZH': 'Zürich'
    }
    
    canton_name = canton_names.get(canton, canton)
    
    # Essayer plusieurs variantes de requête
    queries = [
        f"{city_name}, {canton_name}, {country}",
        f"{city_name}, {canton}, {country}",
        f"{city_name}, Switzerland",
        f"{city_name}"
    ]
    
    for query in queries:
        try:
            # Paramètres pour l'API Nominatim
            params = {
                'q': query,
                'format': 'json',
                'countrycodes': 'ch',  # Limiter à la Suisse
                'limit': 5,
                'addressdetails': 1
            }
            
            # Headers pour être poli avec l'API
            headers = {
                'User-Agent': 'CovoiturageSuisse/1.0 (covoiturage bot geocoding)'
            }
            
            response = requests.get(
                'https://nominatim.openstreetmap.org/search',
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                
                if results:
                    # Prendre le premier résultat (normalement le plus pertinent)
                    result = results[0]
                    lat = float(result['lat'])
                    lon = float(result['lon'])
                    
                    print(f"  ✓ Trouvé: {query} -> ({lat:.6f}, {lon:.6f})")
                    return (lat, lon)
            
            # Pause pour éviter de surcharger l'API (max 1 req/sec recommandé)
            time.sleep(1.1)
            
        except Exception as e:
            print(f"  ⚠ Erreur pour '{query}': {e}")
            continue
    
    print(f"  ✗ Impossible de géocoder: {city_name}, {canton}")
    return None

def geocode_missing_communes():
    """
    Géocode toutes les communes sans coordonnées dans cities.json
    """
    print("🗺️  Géocodage des communes suisses manquantes...")
    
    # Lire le fichier actuel
    cities_file = "src/bot/data/cities.json"
    try:
        with open(cities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de {cities_file}: {e}")
        return False
    
    cities = data['cities']
    
    # Identifier les communes sans coordonnées
    missing_coords = []
    for i, city in enumerate(cities):
        if city.get('lat') is None or city.get('lon') is None:
            missing_coords.append((i, city))
    
    print(f"📊 {len(missing_coords)} communes à géocoder sur {len(cities)} total")
    
    if not missing_coords:
        print("✅ Toutes les communes ont déjà des coordonnées !")
        return True
    
    # Sauvegarder avant modification
    backup_file = f"{cities_file}.backup_before_geocoding"
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Sauvegarde créée: {backup_file}")
    except Exception as e:
        print(f"⚠️  Impossible de créer la sauvegarde: {e}")
    
    # Géocoder les communes manquantes
    success_count = 0
    fail_count = 0
    
    for i, (index, city) in enumerate(missing_coords, 1):
        city_name = city.get('name', 'Unknown')
        canton = city.get('canton', 'Unknown')
        
        print(f"\n[{i}/{len(missing_coords)}] Géocodage: {city_name} ({canton})")
        
        coords = geocode_city(city_name, canton)
        if coords:
            lat, lon = coords
            cities[index]['lat'] = lat
            cities[index]['lon'] = lon
            success_count += 1
        else:
            fail_count += 1
        
        # Sauvegarder périodiquement (tous les 50)
        if i % 50 == 0:
            try:
                with open(cities_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"💾 Sauvegarde intermédiaire (après {i} communes)")
            except Exception as e:
                print(f"⚠️  Erreur sauvegarde intermédiaire: {e}")
    
    # Sauvegarder le résultat final
    try:
        with open(cities_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Sauvegarde finale terminée")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde finale: {e}")
        return False
    
    # Résumé
    print(f"\n📈 RÉSUMÉ DU GÉOCODAGE:")
    print(f"  ✅ Succès: {success_count}")
    print(f"  ❌ Échecs: {fail_count}")
    print(f"  📊 Taux de succès: {success_count/(success_count+fail_count)*100:.1f}%")
    
    if fail_count > 0:
        print(f"\n⚠️  {fail_count} communes n'ont pas pu être géocodées.")
        print("    Vous pouvez relancer le script ou géocoder manuellement.")
    
    return True

def show_statistics():
    """
    Affiche les statistiques après géocodage
    """
    print("\n📊 STATISTIQUES FINALES:")
    
    try:
        with open("src/bot/data/cities.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cities = data['cities']
        total = len(cities)
        with_coords = sum(1 for city in cities if city.get('lat') is not None and city.get('lon') is not None)
        without_coords = total - with_coords
        
        print(f"  🏘️  Total communes: {total}")
        print(f"  ✅ Avec coordonnées: {with_coords} ({with_coords/total*100:.1f}%)")
        print(f"  ❌ Sans coordonnées: {without_coords} ({without_coords/total*100:.1f}%)")
        
        # Statistiques par canton
        print(f"\n📍 Par canton:")
        from collections import defaultdict
        stats = defaultdict(lambda: {'total': 0, 'avec': 0})
        
        for city in cities:
            canton = city.get('canton', 'Unknown')
            stats[canton]['total'] += 1
            if city.get('lat') is not None and city.get('lon') is not None:
                stats[canton]['avec'] += 1
        
        for canton in sorted(stats.keys()):
            total_canton = stats[canton]['total']
            avec = stats[canton]['avec']
            pourcentage = (avec / total_canton * 100) if total_canton > 0 else 0
            print(f"    {canton}: {avec}/{total_canton} ({pourcentage:.1f}%)")
            
    except Exception as e:
        print(f"❌ Erreur lors du calcul des statistiques: {e}")

if __name__ == "__main__":
    print("🇨🇭 Géocodage automatique des communes suisses")
    print("=" * 50)
    
    if geocode_missing_communes():
        show_statistics()
        print("\n🎉 Géocodage terminé avec succès !")
    else:
        print("\n❌ Erreur pendant le géocodage.")
        sys.exit(1)
