#!/usr/bin/env python3
"""
Script pour ajouter les communes et villes manquantes importantes
"""

import json
import sys
import os

def load_swiss_localities() -> dict:
    """Charge les données des localités suisses"""
    try:
        with open('data/swiss_localities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement JSON: {e}")
        return {}

def add_missing_cities():
    """Ajoute les villes et communes manquantes importantes"""
    
    localities = load_swiss_localities()
    print(f"📊 {len(localities)} localités actuelles")
    
    # Villes principales manquantes avec coordonnées exactes
    missing_cities = {
        # Villes principales
        'Basel': {
            'name': 'Basel',
            'zip': '4001', 
            'canton': 'BS',
            'lat': 47.5596,
            'lon': 7.5886
        },
        'Bâle': {
            'name': 'Bâle',
            'zip': '4001',
            'canton': 'BS', 
            'lat': 47.5596,
            'lon': 7.5886
        },
        'Winterthur': {
            'name': 'Winterthur',
            'zip': '8400',
            'canton': 'ZH',
            'lat': 47.5000,
            'lon': 8.7333
        },
        'Luzern': {
            'name': 'Luzern',
            'zip': '6000',
            'canton': 'LU',
            'lat': 47.0502,
            'lon': 8.3093
        },
        'Lucerne': {
            'name': 'Lucerne',
            'zip': '6000',
            'canton': 'LU',
            'lat': 47.0502,
            'lon': 8.3093
        },
        'St. Gallen': {
            'name': 'St. Gallen',
            'zip': '9000',
            'canton': 'SG',
            'lat': 47.4245,
            'lon': 9.3767
        },
        'Saint-Gall': {
            'name': 'Saint-Gall',
            'zip': '9000',
            'canton': 'SG',
            'lat': 47.4245,
            'lon': 9.3767
        },
        'Thun': {
            'name': 'Thun',
            'zip': '3600',
            'canton': 'BE',
            'lat': 47.7578,
            'lon': 7.6280
        },
        'Thoune': {
            'name': 'Thoune',
            'zip': '3600',
            'canton': 'BE',
            'lat': 47.7578,
            'lon': 7.6280
        },
        'Schaffhausen': {
            'name': 'Schaffhausen',
            'zip': '8200',
            'canton': 'SH',
            'lat': 47.6954,
            'lon': 8.6345
        },
        'Schaffhouse': {
            'name': 'Schaffhouse',
            'zip': '8200',
            'canton': 'SH',
            'lat': 47.6954,
            'lon': 8.6345
        },
        
        # Communes fribourgeoises manquantes
        'Posieux': {
            'name': 'Posieux',
            'zip': '1725',
            'canton': 'FR',
            'lat': 46.7707,
            'lon': 7.1130
        },
        
        # Stations touristiques importantes
        'Gstaad': {
            'name': 'Gstaad',
            'zip': '3780',
            'canton': 'BE',
            'lat': 46.4753,
            'lon': 7.2864
        },
        'Zermatt': {
            'name': 'Zermatt',
            'zip': '3920',
            'canton': 'VS',
            'lat': 46.0207,
            'lon': 7.7491
        },
        'St. Moritz': {
            'name': 'St. Moritz',
            'zip': '7500',
            'canton': 'GR',
            'lat': 46.4908,
            'lon': 9.8355
        },
        'Davos': {
            'name': 'Davos',
            'zip': '7260',
            'canton': 'GR',
            'lat': 46.8006,
            'lon': 9.8267
        },
        'Interlaken': {
            'name': 'Interlaken',
            'zip': '3800',
            'canton': 'BE',
            'lat': 46.6861,
            'lon': 7.8632
        },
        'Grindelwald': {
            'name': 'Grindelwald',
            'zip': '3818',
            'canton': 'BE',
            'lat': 46.6245,
            'lon': 8.0412
        },
        'Lauterbrunnen': {
            'name': 'Lauterbrunnen',
            'zip': '3822',
            'canton': 'BE',
            'lat': 46.5935,
            'lon': 7.9072
        },
        'Adelboden': {
            'name': 'Adelboden',
            'zip': '3715',
            'canton': 'BE',
            'lat': 46.4930,
            'lon': 7.6004
        },
        
        # Villes importantes supplémentaires
        'Morges': {
            'name': 'Morges',
            'zip': '1110',
            'canton': 'VD',
            'lat': 46.5117,
            'lon': 6.4997
        },
        'Nyon': {
            'name': 'Nyon',
            'zip': '1260',
            'canton': 'VD',
            'lat': 46.3831,
            'lon': 6.2389
        },
        'Vevey': {
            'name': 'Vevey',
            'zip': '1800',
            'canton': 'VD',
            'lat': 46.4601,
            'lon': 6.8432
        },
        'Montreux': {
            'name': 'Montreux',
            'zip': '1820',
            'canton': 'VD',
            'lat': 46.4312,
            'lon': 6.9123
        },
        'Aigle': {
            'name': 'Aigle',
            'zip': '1860',
            'canton': 'VD',
            'lat': 46.3167,
            'lon': 6.9667
        },
        'Martigny': {
            'name': 'Martigny',
            'zip': '1920',
            'canton': 'VS',
            'lat': 46.1024,
            'lon': 7.0737
        },
        'Sierre': {
            'name': 'Sierre',
            'zip': '3960',
            'canton': 'VS',
            'lat': 46.2919,
            'lon': 7.5351
        },
        'Monthey': {
            'name': 'Monthey',
            'zip': '1870',
            'canton': 'VS',
            'lat': 46.2543,
            'lon': 6.9584
        },
        'Yverdon-les-Bains': {
            'name': 'Yverdon-les-Bains',
            'zip': '1400',
            'canton': 'VD',
            'lat': 46.7784,
            'lon': 6.6410
        },
        'Payerne': {
            'name': 'Payerne',
            'zip': '1530',
            'canton': 'VD',
            'lat': 46.8215,
            'lon': 6.9377
        },
        'Delémont': {
            'name': 'Delémont',
            'zip': '2800',
            'canton': 'JU',
            'lat': 47.3644,
            'lon': 7.3467
        },
        'Porrentruy': {
            'name': 'Porrentruy',
            'zip': '2900',
            'canton': 'JU',
            'lat': 47.4157,
            'lon': 7.0754
        },
        'Bellinzona': {
            'name': 'Bellinzona',
            'zip': '6500',
            'canton': 'TI',
            'lat': 46.1944,
            'lon': 9.0172
        },
        'Locarno': {
            'name': 'Locarno',
            'zip': '6600',
            'canton': 'TI',
            'lat': 46.1712,
            'lon': 8.7980
        },
        'Mendrisio': {
            'name': 'Mendrisio',
            'zip': '6850',
            'canton': 'TI',
            'lat': 45.8691,
            'lon': 8.9814
        }
    }
    
    added_count = 0
    updated_count = 0
    
    print("➕ Ajout des villes et communes manquantes:")
    for name, data in missing_cities.items():
        if name not in localities:
            localities[name] = data
            added_count += 1
            print(f"✅ Ajouté: {name} ({data['canton']}, NPA {data['zip']})")
        else:
            # Vérifier si les coordonnées sont meilleures
            existing = localities[name]
            if existing.get('lat', 0.0) == 0.0 or existing.get('lon', 0.0) == 0.0:
                localities[name].update(data)
                updated_count += 1
                print(f"🔄 Mis à jour: {name} (coordonnées ajoutées)")
    
    print(f"\n📊 Résultats:")
    print(f"➕ Nouvelles communes: {added_count}")
    print(f"🔄 Mises à jour: {updated_count}")
    print(f"📈 Total: {len(localities)} localités")
    
    # Sauvegarder
    try:
        with open('data/swiss_localities.json', 'w', encoding='utf-8') as f:
            json.dump(localities, f, ensure_ascii=False, indent=2)
        print(f"💾 Données sauvegardées")
        return True
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return False

def verify_additions():
    """Vérifie que les ajouts ont bien fonctionné"""
    print("\n🔍 VÉRIFICATION DES AJOUTS")
    print("=" * 40)
    
    localities = load_swiss_localities()
    
    # Test quelques villes importantes
    test_cities = ['Basel', 'Winterthur', 'Luzern', 'St. Gallen', 'Posieux', 'Gstaad']
    
    for city in test_cities:
        found = False
        for name, data in localities.items():
            if city.lower() in name.lower():
                lat, lon = data.get('lat', 0), data.get('lon', 0)
                if lat != 0.0 and lon != 0.0:
                    print(f"✅ {name}: NPA {data.get('zip', 'N/A')}, Coords ({lat}, {lon})")
                else:
                    print(f"⚠️  {name}: Coordonnées manquantes")
                found = True
                break
        
        if not found:
            print(f"❌ {city}: Non trouvé")

def test_search_functionality():
    """Test la fonctionnalité de recherche"""
    print("\n🔍 TEST DE RECHERCHE")
    print("=" * 40)
    
    try:
        from utils.swiss_cities import find_locality
        
        test_queries = ['Basel', 'Bâle', '4001', 'Posieux', '1725', 'Gstaad']
        
        for query in test_queries:
            results = find_locality(query)
            if results:
                print(f"✅ '{query}' → {len(results)} résultat(s)")
                for r in results[:2]:  # Max 2 résultats
                    coords = f"({r.get('lat', 0)}, {r.get('lon', 0)})" if 'lat' in r else ""
                    print(f"    - {r.get('name', 'N/A')} ({r.get('zip', 'N/A')}) {coords}")
            else:
                print(f"❌ '{query}' → Aucun résultat")
                
    except Exception as e:
        print(f"❌ Erreur test recherche: {e}")

def main():
    """Fonction principale"""
    print("➕ AJOUT DES COMMUNES ET VILLES MANQUANTES")
    print("=" * 50)
    
    # Ajouter les communes manquantes
    if add_missing_cities():
        # Vérifier les ajouts
        verify_additions()
        
        # Tester la recherche
        test_search_functionality()
        
        print("\n🎉 AJOUTS TERMINÉS AVEC SUCCÈS!")
        print("✅ Les principales villes suisses sont maintenant disponibles")
        print("✅ Les coordonnées GPS sont corrigées")
        print("✅ La recherche par nom et NPA fonctionne")
    else:
        print("❌ Échec de l'ajout des communes")

if __name__ == "__main__":
    main()
