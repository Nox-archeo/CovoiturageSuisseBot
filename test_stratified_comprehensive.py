#!/usr/bin/env python3
"""
Test stratifié intelligent : échantillon représentatif de 150 communes
pour couvrir tous les cantons et types de communes
"""

import sys
import os
import json
import random
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'handlers'))

from utils.route_distance import get_route_distance_with_fallback
from trip_handlers import get_coords
from geopy.distance import geodesic

def create_stratified_sample():
    """Crée un échantillon stratifié représentatif"""
    
    # Charger toutes les communes
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'swiss_localities.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"=== ÉCHANTILLONNAGE STRATIFIÉ ===")
    print(f"Total communes: {len(data)}")
    
    # Grouper par canton
    by_canton = {}
    for name, info in data.items():
        canton = info.get('canton', 'XX')
        if canton not in by_canton:
            by_canton[canton] = []
        by_canton[canton].append(name)
    
    print(f"Cantons trouvés: {len(by_canton)}")
    for canton, communes in sorted(by_canton.items()):
        print(f"  {canton}: {len(communes)} communes")
    
    # Échantillonnage stratifié
    sample = []
    random.seed(42)
    
    # 1. Principales villes connues (obligatoires)
    villes_importantes = [
        "Lausanne", "Genève", "Fribourg", "Luzern", "Neuchâtel", "Sion",
        "Montreux", "Vevey", "Bulle", "Morges", "Nyon", "Yverdon-les-Bains",
        "Delémont", "Martigny", "Aigle", "Sierre"
    ]
    
    for ville in villes_importantes:
        if ville in data:
            sample.append(ville)
    
    print(f"Villes importantes ajoutées: {len(sample)}")
    
    # 2. Échantillon aléatoire par canton (proportionnel)
    target_total = 150
    remaining_spots = target_total - len(sample)
    
    for canton, communes in by_canton.items():
        # Nombre d'échantillons pour ce canton (proportionnel)
        canton_ratio = len(communes) / len(data)
        canton_samples = max(1, int(remaining_spots * canton_ratio))
        
        # Communes déjà incluses
        canton_communes = [c for c in communes if c not in sample]
        
        # Ajouter échantillon aléatoire
        if canton_communes:
            to_add = min(canton_samples, len(canton_communes))
            selected = random.sample(canton_communes, to_add)
            sample.extend(selected)
    
    # Limiter à 150
    if len(sample) > target_total:
        sample = sample[:target_total]
    
    print(f"Échantillon final: {len(sample)} communes")
    
    return sample

def test_stratified_sample():
    """Test l'échantillon stratifié"""
    
    sample_communes = create_stratified_sample()
    
    print(f"\n=== VÉRIFICATION DES COORDONNÉES ===")
    
    communes_avec_coords = []
    for commune in sample_communes:
        coords = get_coords(commune)
        if coords and coords != (None, None):
            communes_avec_coords.append(commune)
    
    print(f"✅ Avec coordonnées: {len(communes_avec_coords)}/{len(sample_communes)} ({len(communes_avec_coords)/len(sample_communes)*100:.1f}%)")
    
    # Test d'un sous-échantillon de trajets (50 trajets max pour ne pas dépasser les limites)
    max_trajets = 50
    random.seed(42)
    
    trajets_to_test = []
    attempts = 0
    max_attempts = 200
    
    while len(trajets_to_test) < max_trajets and attempts < max_attempts:
        ville1, ville2 = random.sample(communes_avec_coords, 2)
        if (ville1, ville2) not in trajets_to_test and (ville2, ville1) not in trajets_to_test:
            trajets_to_test.append((ville1, ville2))
        attempts += 1
    
    print(f"\n=== TEST DE {len(trajets_to_test)} TRAJETS ALÉATOIRES ===")
    
    api_success = 0
    fallback_used = 0
    errors = 0
    differences = []
    
    for i, (ville1, ville2) in enumerate(trajets_to_test):
        print(f"Test {i+1}/{len(trajets_to_test)}: {ville1} -> {ville2}")
        
        coords1 = get_coords(ville1)
        coords2 = get_coords(ville2)
        
        # Distance à vol d'oiseau
        geodesic_distance = geodesic(coords1, coords2).kilometers
        
        # Distance routière
        route_distance, is_route = get_route_distance_with_fallback(coords1, coords2)
        
        if route_distance is None:
            print(f"❌ Erreur")
            errors += 1
            continue
        
        # Stats
        if is_route:
            api_success += 1
            status = "✅"
        else:
            fallback_used += 1
            status = "⚠️"
        
        diff_km = route_distance - geodesic_distance
        diff_pct = (diff_km / geodesic_distance) * 100 if geodesic_distance > 0 else 0
        differences.append(diff_pct)
        
        print(f"  {geodesic_distance:.1f} km → {route_distance:.1f} km ({status} +{diff_pct:.1f}%)")
        
        # Pause pour l'API
        time.sleep(0.4)
    
    # Résumé
    total_tests = api_success + fallback_used + errors
    
    print(f"\n=== RÉSUMÉ REPRÉSENTATIF ===")
    print(f"Échantillon: {len(sample_communes)} communes sur {741} total")
    print(f"Communes avec coordonnées: {len(communes_avec_coords)} ({len(communes_avec_coords)/len(sample_communes)*100:.1f}%)")
    print(f"Trajets testés: {total_tests}")
    print(f"✅ API réussie: {api_success} ({api_success/total_tests*100:.1f}%)")
    print(f"⚠️ Fallback utilisé: {fallback_used} ({fallback_used/total_tests*100:.1f}%)")
    print(f"❌ Erreurs: {errors} ({errors/total_tests*100:.1f}%)")
    
    if differences:
        avg_diff = sum(differences) / len(differences)
        print(f"Augmentation moyenne de distance: +{avg_diff:.1f}%")
    
    print(f"\n🎯 EXTRAPOLATION SUR LES 741 COMMUNES:")
    if api_success > 0:
        success_rate = api_success / total_tests
        print(f"   Estimation API réussie: {success_rate*100:.1f}% des trajets")
        print(f"   → Sur ~274,000 trajets possibles: ~{274000*success_rate:,.0f} utiliseraient l'API")
    
    print(f"\n✅ CONCLUSION: Échantillon représentatif testé avec succès!")

if __name__ == "__main__":
    test_stratified_sample()
