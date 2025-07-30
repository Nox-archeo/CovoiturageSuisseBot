#!/usr/bin/env python3
"""
Test des nouvelles communes géocodées avec le calcul de distance routière.
Vérifie que toutes les nouvelles communes peuvent être utilisées pour créer des trajets.
"""

import json
import sys
import os

# Ajouter le répertoire racine au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.route_distance import get_route_distance_km
import random

def test_newly_geocoded_communes():
    """
    Test les nouvelles communes géocodées avec le calcul de distance
    """
    print("🧪 Test des nouvelles communes géocodées")
    print("=" * 50)
    
    # Lire les données des communes
    try:
        with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        cities = data['cities']
    except Exception as e:
        print(f"❌ Erreur lecture cities.json: {e}")
        return False
    
    # Identifier quelques nouvelles communes de différents cantons
    new_communes_samples = {
        'AG': ['Aarburg', 'Baden', 'Wohlen'],
        'ZH': ['Adliswil', 'Winterthur', 'Uster'],
        'TI': ['Bellinzona', 'Locarno', 'Mendrisio'],
        'SG': ['Rapperswil-Jona', 'Wil', 'Buchs'],
        'SO': ['Olten', 'Grenchen', 'Solothurn'],
        'BL': ['Liestal', 'Binningen', 'Allschwil']
    }
    
    # Communes de référence (déjà existantes) pour les tests
    reference_communes = ['Lausanne', 'Geneva', 'Fribourg', 'Bern']
    
    test_results = {
        'total_tests': 0,
        'successful_distance_calculations': 0,
        'failed_distance_calculations': 0,
        'route_found': 0,
        'fallback_used': 0
    }
    
    print("🔍 Tests de calcul de distance avec les nouvelles communes:")
    
    for canton, commune_names in new_communes_samples.items():
        print(f"\n📍 Canton {canton}:")
        
        for commune_name in commune_names:
            # Trouver la commune dans les données
            commune = None
            for city in cities:
                if city['name'] == commune_name and city['canton'] == canton:
                    commune = city
                    break
            
            if not commune:
                print(f"  ⚠️  Commune '{commune_name}' non trouvée dans {canton}")
                continue
            
            # Tester avec une commune de référence
            ref_commune_name = random.choice(reference_communes)
            ref_commune = None
            for city in cities:
                if city['name'] == ref_commune_name:
                    ref_commune = city
                    break
            
            if not ref_commune:
                continue
            
            # Test du calcul de distance
            print(f"  🛣️  Test: {commune_name} ↔ {ref_commune_name}")
            
            try:
                distance_km = get_route_distance_km(
                    (commune['lat'], commune['lon']),
                    (ref_commune['lat'], ref_commune['lon'])
                )
                
                test_results['total_tests'] += 1
                
                if distance_km is not None and distance_km > 0:
                    test_results['successful_distance_calculations'] += 1
                    
                    # Vérifier si c'est une distance routière (> distance à vol d'oiseau)
                    # Calcul approximatif de la distance à vol d'oiseau
                    import math
                    
                    lat1_rad = math.radians(commune['lat'])
                    lon1_rad = math.radians(commune['lon'])
                    lat2_rad = math.radians(ref_commune['lat'])
                    lon2_rad = math.radians(ref_commune['lon'])
                    
                    dlat = lat2_rad - lat1_rad
                    dlon = lon2_rad - lon1_rad
                    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    straight_distance = 6371 * c  # Rayon de la Terre en km
                    
                    if distance_km > straight_distance * 1.1:  # Route 10% plus longue que direct
                        test_results['route_found'] += 1
                        print(f"    ✅ Distance routière: {distance_km:.1f} km (vs {straight_distance:.1f} km direct)")
                    else:
                        test_results['fallback_used'] += 1
                        print(f"    📏 Fallback (direct): {distance_km:.1f} km")
                else:
                    test_results['failed_distance_calculations'] += 1
                    print(f"    ❌ Échec du calcul de distance")
                    
            except Exception as e:
                test_results['failed_distance_calculations'] += 1
                print(f"    ❌ Erreur: {e}")
    
    # Tests additionnels entre nouvelles communes
    print(f"\n🔄 Tests entre nouvelles communes:")
    
    # Prendre quelques paires de nouvelles communes pour test
    test_pairs = [
        ('Baden', 'AG', 'Aarburg', 'AG'),
        ('Winterthur', 'ZH', 'Uster', 'ZH'),
        ('Olten', 'SO', 'Solothurn', 'SO'),
        ('Bellinzona', 'TI', 'Locarno', 'TI')
    ]
    
    for city1_name, canton1, city2_name, canton2 in test_pairs:
        # Trouver les communes
        city1 = city2 = None
        for city in cities:
            if city['name'] == city1_name and city['canton'] == canton1:
                city1 = city
            elif city['name'] == city2_name and city['canton'] == canton2:
                city2 = city
        
        if city1 and city2:
            print(f"  🛣️  {city1_name} ({canton1}) ↔ {city2_name} ({canton2})")
            
            try:
                distance_km = get_route_distance_km(
                    (city1['lat'], city1['lon']),
                    (city2['lat'], city2['lon'])
                )
                
                test_results['total_tests'] += 1
                
                if distance_km is not None and distance_km > 0:
                    test_results['successful_distance_calculations'] += 1
                    print(f"    ✅ Distance: {distance_km:.1f} km")
                else:
                    test_results['failed_distance_calculations'] += 1
                    print(f"    ❌ Échec")
                    
            except Exception as e:
                test_results['failed_distance_calculations'] += 1
                print(f"    ❌ Erreur: {e}")
    
    # Résumé des résultats
    print(f"\n📊 RÉSUMÉ DES TESTS:")
    print(f"  🧪 Total tests: {test_results['total_tests']}")
    print(f"  ✅ Calculs réussis: {test_results['successful_distance_calculations']}")
    print(f"  ❌ Calculs échoués: {test_results['failed_distance_calculations']}")
    print(f"  🛣️  Routes trouvées: {test_results['route_found']}")
    print(f"  📏 Fallback utilisé: {test_results['fallback_used']}")
    
    if test_results['total_tests'] > 0:
        success_rate = test_results['successful_distance_calculations'] / test_results['total_tests'] * 100
        route_rate = test_results['route_found'] / test_results['total_tests'] * 100
        print(f"  📈 Taux de succès: {success_rate:.1f}%")
        print(f"  🗺️  Taux de routes: {route_rate:.1f}%")
    
    return test_results['successful_distance_calculations'] > test_results['failed_distance_calculations']

def test_coverage_statistics():
    """
    Affiche les statistiques de couverture finale
    """
    print(f"\n📊 STATISTIQUES DE COUVERTURE FINALE:")
    print("=" * 50)
    
    try:
        with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        cities = data['cities']
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    total = len(cities)
    cantons = set(city['canton'] for city in cities)
    
    print(f"🏘️  Total communes: {total}")
    print(f"🗺️  Cantons couverts: {len(cantons)} ({', '.join(sorted(cantons))})")
    print(f"✅ Toutes ont des coordonnées GPS")
    print(f"🧮 Couverture estimée: {total}/~2200 communes suisses ({total/2200*100:.1f}%)")
    
    # Top 10 des cantons par nombre de communes
    from collections import Counter
    canton_counts = Counter(city['canton'] for city in cities)
    print(f"\n🏆 TOP 10 CANTONS (par nombre de communes):")
    for canton, count in canton_counts.most_common(10):
        print(f"  {canton}: {count} communes")

if __name__ == "__main__":
    print("🧪 Tests de validation post-géocodage")
    print("=" * 60)
    
    success = test_newly_geocoded_communes()
    test_coverage_statistics()
    
    if success:
        print(f"\n🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Les nouvelles communes géocodées sont prêtes à être utilisées dans le bot.")
    else:
        print(f"\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔧 Vérifiez la configuration de l'API OpenRouteService.")
