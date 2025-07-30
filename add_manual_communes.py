#!/usr/bin/env python3
"""
Ajouter manuellement les communes manquantes avec coordonnées connues
"""

import json

def main():
    print("🏔️ AJOUT MANUEL DES COMMUNES MANQUANTES")
    print("=" * 50)
    
    # Communes manquantes avec coordonnées connues
    manual_communes = {
        "Freiburg": {
            "name": "Freiburg",
            "zip": "1700", 
            "canton": "FR",
            "lat": 46.8052,
            "lon": 7.1615  # Mêmes coordonnées que Fribourg
        },
        "Sankt Gallen": {
            "name": "Sankt Gallen",
            "zip": "9000",
            "canton": "SG", 
            "lat": 47.4245,
            "lon": 9.3767  # Mêmes coordonnées que Saint-Gall
        },
        "Genf": {
            "name": "Genf",
            "zip": "1200",
            "canton": "GE",
            "lat": 46.2044,
            "lon": 6.1432  # Mêmes coordonnées que Genève
        },
        "Albeuve": {
            "name": "Albeuve",
            "zip": "1669",
            "canton": "FR",
            "lat": 46.5147,
            "lon": 7.0636  # Coordonnées Albeuve
        },
        "Lessoc": {
            "name": "Lessoc", 
            "zip": "1669",
            "canton": "FR",
            "lat": 46.5033,
            "lon": 7.0550  # Coordonnées Lessoc
        },
        "Montbovon": {
            "name": "Montbovon",
            "zip": "1669", 
            "canton": "FR",
            "lat": 46.4944,
            "lon": 7.0683  # Coordonnées Montbovon
        },
        "Enney": {
            "name": "Enney",
            "zip": "1660",
            "canton": "FR", 
            "lat": 46.5275,
            "lon": 7.1083  # Coordonnées Enney
        }
    }
    
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
    
    for name, commune_data in manual_communes.items():
        if name not in localities:
            localities[name] = commune_data
            added_count += 1
            print(f"✅ Ajouté: {name} ({commune_data['zip']}) [{commune_data['canton']}] GPS: ({commune_data['lat']:.4f}, {commune_data['lon']:.4f})")
        else:
            print(f"⚠️  Commune déjà existante: {name}")
    
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
