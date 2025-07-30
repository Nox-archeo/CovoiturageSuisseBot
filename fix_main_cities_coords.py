#!/usr/bin/env python3
"""
Script pour ajouter les coordonnées des villes principales suisses
"""

import json

def main():
    # Coordonnées des principales villes suisses
    principales_villes = {
        'Fribourg': {'lat': 46.8063, 'lon': 7.1617},
        'Lausanne': {'lat': 46.5197, 'lon': 6.6323},
        'Bern': {'lat': 46.9480, 'lon': 7.4474},
        'Zurich': {'lat': 47.3769, 'lon': 8.5417},
        'Geneva': {'lat': 46.2044, 'lon': 6.1432},
        'Basel': {'lat': 47.5596, 'lon': 7.5886},
        'Sion': {'lat': 46.2332, 'lon': 7.3578},
        'Neuchâtel': {'lat': 46.9926, 'lon': 6.9305},
        'Lucerne': {'lat': 47.0502, 'lon': 8.3093},
        'St. Gallen': {'lat': 47.4212, 'lon': 9.3751},
        'Lugano': {'lat': 46.0101, 'lon': 8.9627},
        'Biel/Bienne': {'lat': 47.1368, 'lon': 7.2463},
        'Thun': {'lat': 46.7581, 'lon': 7.6283},
        'Köniz': {'lat': 46.9245, 'lon': 7.4146},
        'La Chaux-de-Fonds': {'lat': 47.1057, 'lon': 6.8267},
        'Winterthur': {'lat': 47.5010, 'lon': 8.7234},
        'Schaffhausen': {'lat': 47.6970, 'lon': 8.6342},
        'Vernier': {'lat': 46.2064, 'lon': 6.0851},
        'Uster': {'lat': 47.3467, 'lon': 8.7208},
        'Lancy': {'lat': 46.1904, 'lon': 6.1125}
    }
    
    # Charger le JSON
    print("📂 Chargement du fichier JSON...")
    with open('data/swiss_localities.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ {len(data)} communes chargées")
    
    # Mettre à jour les coordonnées
    updated_count = 0
    for ville, coords in principales_villes.items():
        if ville in data:
            data[ville]['lat'] = coords['lat']
            data[ville]['lon'] = coords['lon']
            updated_count += 1
            print(f"✅ {ville}: ({coords['lat']}, {coords['lon']})")
        else:
            print(f"❌ {ville}: Non trouvé dans les données")
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde de {updated_count} coordonnées...")
    with open('data/swiss_localities.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"🎉 {updated_count} villes mises à jour avec leurs coordonnées!")

if __name__ == "__main__":
    main()
