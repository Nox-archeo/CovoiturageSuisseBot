#!/usr/bin/env python3
"""
Script pour corriger TOUTES les coordonnées GPS manquantes des communes suisses
Utilise l'API Nominatim (OpenStreetMap) pour géocoder toutes les communes
"""

import json
import time
import requests
from typing import Dict, Tuple, Optional
import sys

def load_swiss_localities() -> Dict:
    """Charge les données des localités suisses"""
    try:
        with open('data/swiss_localities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement JSON: {e}")
        return {}

def geocode_location(location_name: str, zip_code: str = "", canton: str = "") -> Optional[Tuple[float, float]]:
    """
    Géocode une localité suisse avec Nominatim (OpenStreetMap)
    Gratuit et sans limite de rate (avec politesse)
    """
    base_url = "https://nominatim.openstreetmap.org/search"
    
    # Construire la requête de recherche
    query_parts = [location_name]
    if zip_code:
        query_parts.append(zip_code)
    if canton:
        query_parts.append(canton)
    query_parts.append("Switzerland")
    
    query = ", ".join(query_parts)
    
    params = {
        'q': query,
        'format': 'json',
        'countrycodes': 'ch',  # Limiter à la Suisse
        'limit': 1,
        'addressdetails': 1
    }
    
    headers = {
        'User-Agent': 'CovoiturageSuisse-Bot/1.0 (https://github.com/user/project)'
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            
            # Vérifier que c'est bien en Suisse (approximativement)
            if 45.8 <= lat <= 47.8 and 5.9 <= lon <= 10.5:
                return (lat, lon)
            else:
                print(f"⚠️  {location_name}: Coordonnées hors Suisse ({lat}, {lon})")
                return None
        else:
            print(f"❌ {location_name}: Aucun résultat trouvé")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {location_name}: Erreur réseau - {e}")
        return None
    except Exception as e:
        print(f"❌ {location_name}: Erreur - {e}")
        return None

def fix_all_missing_coordinates():
    """Corrige toutes les coordonnées manquantes"""
    print("🔧 CORRECTION DE TOUTES LES COORDONNÉES GPS MANQUANTES")
    print("=" * 60)
    
    localities = load_swiss_localities()
    if not localities:
        return
    
    # Identifier toutes les communes sans coordonnées
    missing_coords = []
    for name, data in localities.items():
        lat = data.get('lat', 0.0)
        lon = data.get('lon', 0.0)
        
        if lat == 0.0 or lon == 0.0:
            missing_coords.append((name, data))
    
    print(f"📊 Trouvé {len(missing_coords)} communes sans coordonnées sur {len(localities)} total")
    print(f"🎯 Objectif: Passer de {len(localities)-len(missing_coords)} à {len(localities)} communes avec coordonnées")
    
    if not missing_coords:
        print("✅ Toutes les communes ont déjà des coordonnées!")
        return
    
    print(f"\n🚀 Début du géocodage de {len(missing_coords)} communes...")
    print("⏱️  Estimation: ~{} minutes (1 requête par seconde)".format(len(missing_coords) // 60 + 1))
    
    corrections = {}
    success_count = 0
    failed_count = 0
    
    for i, (name, data) in enumerate(missing_coords, 1):
        zip_code = data.get('zip', '')
        canton = data.get('canton', '')
        
        print(f"\n[{i:4d}/{len(missing_coords)}] 🔍 Géocodage: {name}", end=" ")
        if zip_code:
            print(f"({zip_code})", end=" ")
        if canton:
            print(f"[{canton}]", end=" ")
        
        # Géocoder
        coords = geocode_location(name, zip_code, canton)
        
        if coords:
            corrections[name] = coords
            success_count += 1
            print(f"→ ✅ {coords[0]:.4f}, {coords[1]:.4f}")
        else:
            failed_count += 1
            print("→ ❌ Échec")
        
        # Pause pour respecter les limites de l'API (1 req/sec max)
        if i < len(missing_coords):
            time.sleep(1.1)
        
        # Sauvegarde intermédiaire tous les 100 éléments
        if i % 100 == 0:
            print(f"\n💾 Sauvegarde intermédiaire... ({success_count} succès, {failed_count} échecs)")
            apply_corrections_batch(localities, corrections)
            corrections = {}  # Reset pour éviter les doublons
    
    # Sauvegarde finale
    if corrections:
        print(f"\n💾 Sauvegarde finale...")
        apply_corrections_batch(localities, corrections)
    
    # Statistiques finales
    print(f"\n📊 RÉSULTATS FINAUX")
    print("=" * 50)
    print(f"✅ Succès: {success_count}")
    print(f"❌ Échecs: {failed_count}")
    print(f"📈 Taux de réussite: {success_count/(success_count+failed_count)*100:.1f}%")
    
    # Vérification finale
    final_localities = load_swiss_localities()
    total = len(final_localities)
    with_coords = sum(1 for data in final_localities.values() 
                     if data.get('lat', 0.0) != 0.0 and data.get('lon', 0.0) != 0.0)
    
    print(f"\n🎯 COUVERTURE FINALE")
    print(f"Total communes: {total}")
    print(f"Avec coordonnées: {with_coords} ({with_coords/total*100:.1f}%)")
    
    if with_coords == total:
        print("🎉 OBJECTIF ATTEINT: 100% des communes ont des coordonnées GPS!")
    else:
        print(f"⚠️  Il reste {total-with_coords} communes sans coordonnées")

def apply_corrections_batch(localities: Dict, corrections: Dict[str, Tuple[float, float]]):
    """Applique un lot de corrections"""
    if not corrections:
        return
    
    for name, (lat, lon) in corrections.items():
        if name in localities:
            localities[name]['lat'] = lat
            localities[name]['lon'] = lon
    
    # Sauvegarder
    try:
        with open('data/swiss_localities.json', 'w', encoding='utf-8') as f:
            json.dump(localities, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

def verify_failed_communes():
    """Affiche les communes qui n'ont toujours pas de coordonnées"""
    print("\n🔍 VÉRIFICATION DES COMMUNES RESTANTES SANS COORDONNÉES")
    print("=" * 60)
    
    localities = load_swiss_localities()
    still_missing = []
    
    for name, data in localities.items():
        lat = data.get('lat', 0.0)
        lon = data.get('lon', 0.0)
        
        if lat == 0.0 or lon == 0.0:
            still_missing.append((name, data.get('zip', ''), data.get('canton', '')))
    
    if still_missing:
        print(f"❌ {len(still_missing)} communes n'ont toujours pas de coordonnées:")
        for name, zip_code, canton in still_missing[:50]:  # Afficher les 50 premières
            print(f"  • {name} ({zip_code}) [{canton}]")
        
        if len(still_missing) > 50:
            print(f"  ... et {len(still_missing) - 50} autres")
    else:
        print("🎉 Toutes les communes ont maintenant des coordonnées GPS!")

def main():
    """Fonction principale"""
    print("🌍 CORRECTION COMPLÈTE DES COORDONNÉES GPS SUISSES")
    print("=" * 60)
    print("🎯 Objectif: Passer de 69.9% à 100% de couverture GPS")
    print("🔧 Méthode: Géocodage via OpenStreetMap Nominatim")
    print("⏱️  Temps estimé: 10-15 minutes")
    print("")
    
    # Demander confirmation
    response = input("Voulez-vous continuer? (y/N): ").strip().lower()
    if response not in ['y', 'yes', 'oui', 'o']:
        print("❌ Opération annulée")
        return
    
    # Lancer la correction
    fix_all_missing_coordinates()
    
    # Vérification finale
    verify_failed_communes()

if __name__ == "__main__":
    main()
