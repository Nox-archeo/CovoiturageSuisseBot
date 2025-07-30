#!/usr/bin/env python3
"""
Script pour vérifier et corriger les coordonnées GPS des communes suisses
"""

import json
import sys
import os
import requests
from typing import Dict, List, Tuple

def load_swiss_localities() -> Dict:
    """Charge les données des localités suisses"""
    try:
        with open('data/swiss_localities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement JSON: {e}")
        return {}

def verify_coordinates_batch(localities: Dict) -> Dict:
    """Vérifie les coordonnées par lot"""
    print("🔍 VÉRIFICATION DES COORDONNÉES GPS")
    print("=" * 50)
    
    # Vérifier les principales villes suisses
    major_cities = {
        'Zürich': (47.3769, 8.5417),
        'Genève': (46.2044, 6.1432),
        'Bâle': (47.5596, 7.5886),
        'Lausanne': (46.5197, 6.6323),
        'Berne': (46.9481, 7.4474),
        'Winterthour': (47.5000, 8.7333),
        'Lucerne': (47.0502, 8.3093),
        'Saint-Gall': (47.4245, 9.3767),
        'Lugano': (46.0101, 8.9600),
        'Bienne': (47.1368, 7.2474),
        'Thoune': (46.7578, 7.6280),
        'Köniz': (46.9243, 7.4144),
        'La Chaux-de-Fonds': (47.1013, 6.8266),
        'Fribourg': (46.8019, 7.1512),
        'Schaffhouse': (47.6954, 8.6345),
        'Chur': (46.8492, 9.5330),
        'Neuchâtel': (47.0019, 6.9309),
        'Uster': (47.3467, 8.7208),
        'Sion': (46.2337, 7.3588),
        'Emmen': (47.0810, 8.3060)
    }
    
    corrections = {}
    missing_coords = []
    
    print("📍 Vérification des principales villes:")
    for city_name, expected_coords in major_cities.items():
        found = False
        for name, data in localities.items():
            if city_name.lower() in name.lower() or name.lower() in city_name.lower():
                current_lat = data.get('lat', 0.0)
                current_lon = data.get('lon', 0.0)
                
                if current_lat == 0.0 or current_lon == 0.0:
                    print(f"❌ {name}: Coordonnées manquantes (0.0, 0.0)")
                    corrections[name] = expected_coords
                    missing_coords.append(name)
                else:
                    # Vérifier si les coordonnées sont proches (±0.1 degré)
                    lat_diff = abs(current_lat - expected_coords[0])
                    lon_diff = abs(current_lon - expected_coords[1])
                    
                    if lat_diff > 0.1 or lon_diff > 0.1:
                        print(f"⚠️  {name}: Coordonnées suspectes ({current_lat}, {current_lon}) vs attendues {expected_coords}")
                        corrections[name] = expected_coords
                    else:
                        print(f"✅ {name}: Coordonnées correctes ({current_lat}, {current_lon})")
                found = True
                break
        
        if not found:
            print(f"❌ {city_name}: Ville non trouvée dans la base")
    
    return corrections

def verify_npa_ranges() -> List[str]:
    """Vérifie les codes postaux suisses"""
    print("\n📮 VÉRIFICATION DES CODES POSTAUX")
    print("=" * 50)
    
    localities = load_swiss_localities()
    invalid_npa = []
    
    for name, data in localities.items():
        npa = data.get('zip', '')
        if npa:
            try:
                npa_int = int(npa)
                # Les NPA suisses vont de 1000 à 9999
                if not (1000 <= npa_int <= 9999):
                    print(f"❌ {name}: NPA invalide {npa}")
                    invalid_npa.append(f"{name}: {npa}")
            except ValueError:
                print(f"❌ {name}: NPA non numérique '{npa}'")
                invalid_npa.append(f"{name}: {npa}")
    
    print(f"✅ Vérification terminée. {len(invalid_npa)} NPA invalides trouvés.")
    return invalid_npa

def check_missing_communes() -> List[str]:
    """Vérifie s'il manque des communes importantes"""
    print("\n🏘️ VÉRIFICATION DES COMMUNES MANQUANTES")
    print("=" * 50)
    
    localities = load_swiss_localities()
    
    # Liste des communes souvent demandées
    important_communes = [
        'Corpataux-Magnedens', 'Posieux', 'Rossens', 'Farvagny', 'Vuisternens-en-Ogoz',
        'Marly', 'Villars-sur-Glâne', 'Givisiez', 'Granges-Paccot', 'Düdingen',
        'Bulle', 'Romont', 'Estavayer-le-Lac', 'Murten', 'Châtel-Saint-Denis',
        'Morges', 'Nyon', 'Vevey', 'Montreux', 'Aigle', 'Martigny', 'Sierre',
        'Monthey', 'Yverdon-les-Bains', 'Payerne', 'Delémont', 'Porrentruy',
        'Bellinzona', 'Locarno', 'Mendrisio', 'Davos', 'St. Moritz', 'Zermatt',
        'Interlaken', 'Grindelwald', 'Lauterbrunnen', 'Adelboden', 'Gstaad'
    ]
    
    missing = []
    found = []
    
    for commune in important_communes:
        found_match = False
        for name in localities.keys():
            if commune.lower() in name.lower() or name.lower() in commune.lower():
                found.append(f"✅ {commune} → {name}")
                found_match = True
                break
        
        if not found_match:
            missing.append(commune)
            print(f"❌ Manquant: {commune}")
    
    print(f"\n📊 Résultats:")
    print(f"✅ Trouvées: {len(found)}")
    print(f"❌ Manquantes: {len(missing)}")
    
    return missing

def apply_corrections(corrections: Dict[str, Tuple[float, float]]):
    """Applique les corrections de coordonnées"""
    if not corrections:
        print("\n✅ Aucune correction nécessaire!")
        return
    
    print(f"\n🔧 APPLICATION DE {len(corrections)} CORRECTIONS")
    print("=" * 50)
    
    localities = load_swiss_localities()
    
    for name, (lat, lon) in corrections.items():
        if name in localities:
            old_lat = localities[name].get('lat', 0.0)
            old_lon = localities[name].get('lon', 0.0)
            
            localities[name]['lat'] = lat
            localities[name]['lon'] = lon
            
            print(f"✅ {name}: ({old_lat}, {old_lon}) → ({lat}, {lon})")
        else:
            print(f"❌ {name}: Non trouvé pour correction")
    
    # Sauvegarder les corrections
    try:
        with open('data/swiss_localities.json', 'w', encoding='utf-8') as f:
            json.dump(localities, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Corrections sauvegardées dans swiss_localities.json")
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

def test_distance_calculation():
    """Test les calculs de distance avec les nouvelles coordonnées"""
    print("\n🧮 TEST DES CALCULS DE DISTANCE")
    print("=" * 50)
    
    try:
        from utils.route_distance import get_route_distance_km
        from utils.swiss_cities import find_locality
        
        # Tests de distances connues
        test_routes = [
            ('Fribourg', 'Lausanne', 67),  # Distance Google Maps
            ('Zürich', 'Berne', 95),
            ('Genève', 'Lausanne', 62),
            ('Bâle', 'Zürich', 87),
            ('Corpataux', 'Fribourg', 8)   # Distance courte locale
        ]
        
        print("🗺️ Tests de distances:")
        for start, end, expected_km in test_routes:
            start_results = find_locality(start)
            end_results = find_locality(end)
            
            if start_results and end_results:
                start_data = start_results[0]
                end_data = end_results[0]
                
                if 'lat' in start_data and 'lon' in start_data and 'lat' in end_data and 'lon' in end_data:
                    distance = get_route_distance_km(
                        (start_data['lat'], start_data['lon']),
                        (end_data['lat'], end_data['lon']),
                        start, end
                    )
                    
                    if distance:
                        diff = abs(distance - expected_km)
                        status = "✅" if diff < 10 else "⚠️" if diff < 20 else "❌"
                        print(f"{status} {start} → {end}: {distance:.1f}km (attendu: {expected_km}km, diff: {diff:.1f}km)")
                    else:
                        print(f"❌ {start} → {end}: Échec calcul distance")
                else:
                    print(f"❌ {start} → {end}: Coordonnées manquantes")
            else:
                print(f"❌ {start} → {end}: Villes non trouvées")
                
    except Exception as e:
        print(f"❌ Erreur test distance: {e}")

def main():
    """Fonction principale"""
    print("🔍 VÉRIFICATION COMPLÈTE DES DONNÉES GÉOGRAPHIQUES")
    print("=" * 60)
    
    localities = load_swiss_localities()
    if not localities:
        print("❌ Impossible de charger les données")
        return
    
    print(f"📊 {len(localities)} localités chargées")
    
    # 1. Vérifier les coordonnées
    corrections = verify_coordinates_batch(localities)
    
    # 2. Vérifier les codes postaux
    invalid_npa = verify_npa_ranges()
    
    # 3. Vérifier les communes manquantes
    missing_communes = check_missing_communes()
    
    # 4. Appliquer les corrections si nécessaire
    if corrections:
        apply_corrections(corrections)
    
    # 5. Tester les calculs de distance
    test_distance_calculation()
    
    # Résumé
    print("\n📋 RÉSUMÉ FINAL")
    print("=" * 50)
    print(f"🔧 Coordonnées corrigées: {len(corrections)}")
    print(f"❌ NPA invalides: {len(invalid_npa)}")
    print(f"❌ Communes manquantes: {len(missing_communes)}")
    
    if corrections or invalid_npa or missing_communes:
        print("\n⚠️ Actions recommandées:")
        if corrections:
            print("✅ Coordonnées corrigées automatiquement")
        if invalid_npa:
            print("🔍 Vérifier manuellement les NPA invalides")
        if missing_communes:
            print("➕ Ajouter les communes manquantes")
    else:
        print("\n🎉 Toutes les données sont correctes!")

if __name__ == "__main__":
    main()
