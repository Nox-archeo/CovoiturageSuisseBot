#!/usr/bin/env python3
"""
Ajouter les communes spécifiques manquantes identifiées lors des tests
"""

import json
import requests
from time import sleep

def geocode_with_nominatim(location_name):
    """Géocoder une commune avec Nominatim"""
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': f"{location_name}, Switzerland",
        'format': 'json',
        'limit': 1,
        'addressdetails': 1,
        'accept-language': 'fr,de,it,en'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data:
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            
            # Vérifier que c'est bien en Suisse
            if 45.8 <= lat <= 47.8 and 5.9 <= lon <= 10.5:
                return lat, lon
                
    except Exception as e:
        print(f"Erreur géocodage {location_name}: {e}")
    
    return None, None

def main():
    print("🏔️ AJOUT DES COMMUNES SPÉCIFIQUES MANQUANTES")
    print("=" * 60)
    
    # Communes manquantes avec leurs variantes
    missing_communes = [
        {"name": "Freiburg im Üechtland", "variant": "Freiburg", "zip": "1700", "canton": "FR"},
        {"name": "Sankt Gallen", "variant": "Sankt Gallen", "zip": "9000", "canton": "SG"},
        {"name": "Genf", "variant": "Genf", "zip": "1200", "canton": "GE"},
        {"name": "Albeuve", "variant": "Albeuve", "zip": "1669", "canton": "FR"},
        {"name": "Lessoc", "variant": "Lessoc", "zip": "1669", "canton": "FR"},
        {"name": "Montbovon", "variant": "Montbovon", "zip": "1669", "canton": "FR"},
        {"name": "Enney", "variant": "Enney", "zip": "1660", "canton": "FR"}
    ]
    
    # Charger les données existantes
    try:
        with open('data/swiss_localities.json', 'r', encoding='utf-8') as f:
            localities = json.load(f)
        print(f"📊 Communes existantes: {len(localities)}")
    except Exception as e:
        print(f"❌ Erreur lecture fichier: {e}")
        return
    
    # Ajouter les communes manquantes
    added_count = 0
    
    for commune_data in missing_communes:
        name = commune_data["name"]
        variant = commune_data["variant"]
        
        # Vérifier si la commune existe déjà (les données sont dans un dictionnaire)
        exists = (
            variant in localities or
            name in localities or
            any(
                commune.get('name', '').lower() == name.lower() or 
                commune.get('name', '').lower() == variant.lower()
                for commune in localities.values()
            )
        )
        
        if not exists:
            print(f"\n🔍 Géocodage de {name} ({variant})...")
            
            # Essayer avec le nom principal
            lat, lon = geocode_with_nominatim(name)
            
            # Si échec, essayer avec la variante
            if lat is None:
                lat, lon = geocode_with_nominatim(variant)
            
            # Si échec, essayer avec le code postal
            if lat is None:
                lat, lon = geocode_with_nominatim(f"{commune_data['zip']} Switzerland")
            
            if lat is not None and lon is not None:
                new_commune = {
                    "name": variant,  # Utiliser la variante comme nom principal
                    "zip": commune_data["zip"],
                    "canton": commune_data["canton"],
                    "lat": lat,
                    "lon": lon
                }
                
                localities[variant] = new_commune  # Ajouter avec la variante comme clé
                added_count += 1
                print(f"✅ Ajouté: {variant} ({commune_data['zip']}) [{commune_data['canton']}] GPS: ({lat:.4f}, {lon:.4f})")
            else:
                print(f"❌ Impossible de géocoder: {name}")
            
            # Délai pour respecter les limites de l'API
            sleep(1.1)
        else:
            print(f"⚠️  Commune déjà existante: {variant}")
    
    if added_count > 0:
        # Sauvegarder les données mises à jour
        try:
            with open('data/swiss_localities.json', 'w', encoding='utf-8') as f:
                json.dump(localities, f, ensure_ascii=False, indent=2)
            print(f"\n✅ Sauvegarde réussie!")
            print(f"📊 Total communes: {len(localities)} (+{added_count})")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    else:
        print("\n📊 Aucune commune à ajouter")

if __name__ == "__main__":
    main()
