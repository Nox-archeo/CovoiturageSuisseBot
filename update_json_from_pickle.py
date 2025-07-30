#!/usr/bin/env python3
"""
Script pour mettre à jour le fichier JSON depuis les données pickle
"""

import pickle
import json
import sys
import os

def main():
    """Charge les données pickle et les sauvegarde en JSON"""
    
    # Charger les données pickle
    pickle_path = 'bot_data_complete_communes.pickle'
    json_path = 'data/swiss_localities.json'
    
    print(f"📂 Chargement des données depuis {pickle_path}...")
    
    try:
        with open(pickle_path, 'rb') as f:
            pickle_data = pickle.load(f)
        
        # Extraire les données des villes
        if isinstance(pickle_data, dict) and 'bot_data' in pickle_data:
            cities_data = pickle_data['bot_data'].get('cities_data', {})
        else:
            cities_data = pickle_data
        
        print(f"✅ {len(cities_data)} communes trouvées dans pickle")
        
        # Convertir en format JSON
        json_data = {}
        for name, data in cities_data.items():
            if isinstance(data, dict):
                json_data[name] = {
                    'name': data.get('name', name),
                    'zip': str(data.get('zip', data.get('npa', ''))),
                    'canton': data.get('canton', ''),
                    'lat': data.get('lat', 0.0),
                    'lon': data.get('lon', 0.0)
                }
        
        print(f"✅ {len(json_data)} communes converties pour JSON")
        
        # Sauvegarder en JSON
        print(f"💾 Sauvegarde vers {json_path}...")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"🎉 Fichier JSON mis à jour avec {len(json_data)} communes!")
        
        # Test de vérification
        print("\n🔍 VÉRIFICATION:")
        test_communes = ['Corpataux-Magnedens', 'Farvagny', 'Rossens (FR)', 'Vuisternens-en-Ogoz']
        
        for commune in test_communes:
            if commune in json_data:
                data = json_data[commune]
                print(f"✅ {commune}: NPA {data['zip']}, Canton {data['canton']}")
            else:
                print(f"❌ {commune}: Non trouvée")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Mise à jour terminée avec succès!")
    else:
        print("\n💥 Échec de la mise à jour")
        sys.exit(1)
