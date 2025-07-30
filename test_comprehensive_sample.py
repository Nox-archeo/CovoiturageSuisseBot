#!/usr/bin/env python3
"""
Test complet sur un échantillon représentatif de TOUTES les communes suisses
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

def load_all_communes():
    """Charge toutes les communes depuis le fichier JSON"""
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'swiss_localities.json')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return list(data.keys())

def test_sample_of_all_communes():
    """Test un échantillon représentatif de toutes les communes"""
    
    print("=== CHARGEMENT DE TOUTES LES COMMUNES ===")
    all_communes = load_all_communes()
    print(f"Total des communes dans la base: {len(all_communes)}")
    
    # Échantillon stratifié
    print("\n=== CRÉATION D'UN ÉCHANTILLON REPRÉSENTATIF ===")
    
    # 1. Grandes villes (population importante)
    grandes_villes = [
        "Lausanne", "Genève", "Fribourg", "Luzern", "Neuchâtel", "Sion"
    ]
    
    # 2. Villes moyennes 
    villes_moyennes = [
        "Montreux", "Vevey", "Bulle", "Morges", "Nyon", "Yverdon-les-Bains",
        "Delémont", "Martigny", "Aigle", "Sierre"
    ]
    
    # 3. Échantillon aléatoire de petites communes
    random.seed(42)  # Pour des résultats reproductibles
    autres_communes = [c for c in all_communes if c not in grandes_villes + villes_moyennes]
    petites_communes = random.sample(autres_communes, min(30, len(autres_communes)))
    
    echantillon = grandes_villes + villes_moyennes + petites_communes
    
    print(f"Échantillon sélectionné: {len(echantillon)} communes")
    print(f"- Grandes villes: {len(grandes_villes)}")
    print(f"- Villes moyennes: {len(villes_moyennes)}")
    print(f"- Petites communes (aléatoire): {len(petites_communes)}")
    
    # Vérifier quelles communes ont des coordonnées
    print(f"\n=== VÉRIFICATION DES COORDONNÉES ===")
    
    communes_avec_coords = []
    communes_sans_coords = []
    
    for commune in echantillon:
        coords = get_coords(commune)
        if coords and coords != (None, None):
            communes_avec_coords.append(commune)
        else:
            communes_sans_coords.append(commune)
    
    print(f"✅ Avec coordonnées: {len(communes_avec_coords)}/{len(echantillon)} ({len(communes_avec_coords)/len(echantillon)*100:.1f}%)")
    print(f"❌ Sans coordonnées: {len(communes_sans_coords)}")
    
    if communes_sans_coords:
        print("Communes sans coordonnées:", ", ".join(communes_sans_coords[:10]))
        if len(communes_sans_coords) > 10:
            print(f"... et {len(communes_sans_coords) - 10} autres")
    
    # Test de trajets avec les communes disponibles
    if len(communes_avec_coords) < 2:
        print("❌ Pas assez de communes avec coordonnées pour tester")
        return
    
    print(f"\n=== TEST DE TRAJETS ENTRE COMMUNES ===")
    
    # Générer des paires de test
    # - Quelques trajets entre grandes villes
    # - Quelques trajets grandes villes <-> petites communes  
    # - Quelques trajets entre petites communes
    
    trajets_test = []
    
    # Grandes villes entre elles
    for i, ville1 in enumerate(grandes_villes[:3]):
        if ville1 in communes_avec_coords:
            for ville2 in grandes_villes[i+1:i+3]:
                if ville2 in communes_avec_coords:
                    trajets_test.append((ville1, ville2, "Grande ville"))
    
    # Grandes villes vers petites communes
    for grande_ville in grandes_villes[:2]:
        if grande_ville in communes_avec_coords:
            for petite in petites_communes[:3]:
                if petite in communes_avec_coords:
                    trajets_test.append((grande_ville, petite, "Grande->Petite"))
    
    # Entre petites communes
    for i, petite1 in enumerate(petites_communes[:3]):
        if petite1 in communes_avec_coords:
            for petite2 in petites_communes[i+1:i+3]:
                if petite2 in communes_avec_coords:
                    trajets_test.append((petite1, petite2, "Petite->Petite"))
    
    print(f"Trajets à tester: {len(trajets_test)}")
    
    # Exécuter les tests
    api_success = 0
    fallback_used = 0
    errors = 0
    
    for i, (ville1, ville2, type_trajet) in enumerate(trajets_test):
        print(f"\n--- Test {i+1}/{len(trajets_test)}: {ville1} -> {ville2} ({type_trajet}) ---")
        
        coords1 = get_coords(ville1)
        coords2 = get_coords(ville2)
        
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
            status = "✅ API"
            api_success += 1
        else:
            status = "⚠️ Fallback"
            fallback_used += 1
        
        diff_km = route_distance - geodesic_distance
        diff_pct = (diff_km / geodesic_distance) * 100 if geodesic_distance > 0 else 0
        
        print(f"Distance: {geodesic_distance:.1f} km → {route_distance:.1f} km ({status})")
        print(f"Différence: +{diff_km:.1f} km (+{diff_pct:.1f}%)")
        
        # Pause pour ne pas surcharger l'API
        time.sleep(0.3)
    
    # Résumé final
    total_tests = api_success + fallback_used + errors
    
    print(f"\n=== RÉSUMÉ FINAL ===")
    print(f"Communes totales dans la base: {len(all_communes)}")
    print(f"Échantillon testé: {len(echantillon)} communes")
    print(f"Communes avec coordonnées: {len(communes_avec_coords)}/{len(echantillon)} ({len(communes_avec_coords)/len(echantillon)*100:.1f}%)")
    print(f"\nTrajets testés: {total_tests}")
    print(f"✅ API réussie: {api_success} ({api_success/total_tests*100:.1f}%)")
    print(f"⚠️ Fallback utilisé: {fallback_used} ({fallback_used/total_tests*100:.1f}%)")
    print(f"❌ Erreurs: {errors} ({errors/total_tests*100:.1f}%)")
    
    # Extrapolation
    if len(communes_avec_coords) > 0:
        taux_coords = len(communes_avec_coords) / len(echantillon)
        communes_avec_coords_estim = int(len(all_communes) * taux_coords)
        
        print(f"\n=== EXTRAPOLATION ===")
        print(f"Estimation communes avec coordonnées: ~{communes_avec_coords_estim}/{len(all_communes)} ({taux_coords*100:.1f}%)")
        
        if api_success > 0:
            taux_api = api_success / total_tests
            print(f"Si {taux_api*100:.1f}% des trajets utilisent l'API, c'est excellent!")
        else:
            print("⚠️ Aucun trajet n'utilise l'API - système à améliorer")

if __name__ == "__main__":
    test_sample_of_all_communes()
