import requests
import json
import os

def download_swiss_cities():
    """Télécharge toutes les villes suisses"""
    print("📥 Téléchargement des villes suisses...")
    
    try:
        # Utilisation de l'API de la Poste Suisse
        response = requests.get(
            'https://swisspost.opendatasoft.com/api/explore/v2.1/catalog/datasets/plz-verzeichnis/records',
            params={
                'limit': -1,  # Toutes les villes
                'lang': 'fr'
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Erreur API: {response.status_code}")
            return
            
        data = response.json()
        results = data.get('results', [])
        
        all_cities = []
        seen = set()  # Pour éviter les doublons
        
        for item in results:
            zip_code = str(item.get('plz', ''))
            city = item.get('ortbez', '')
            canton = item.get('kanton', '')
            
            if zip_code and city:
                key = f"{zip_code}-{city}"
                if key not in seen:
                    seen.add(key)
                    all_cities.append({
                        "zip": zip_code,
                        "name": city,
                        "canton": canton
                    })
        
        # Trier par NPA puis nom
        all_cities.sort(key=lambda x: (x['zip'], x['name']))
        
        # Créer le dossier data s'il n'existe pas
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(output_dir, exist_ok=True)
        
        # Sauvegarder dans le fichier JSON
        output_path = os.path.join(output_dir, 'swiss_cities.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"cities": all_cities}, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(all_cities)} villes sauvegardées dans swiss_cities.json")
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        # Charger une liste minimale de villes en cas d'erreur
        fallback_cities = [
            {"zip": "1700", "name": "Fribourg", "canton": "FR"},
            {"zip": "1701", "name": "Fribourg", "canton": "FR"},
            {"zip": "1630", "name": "Bulle", "canton": "FR"},
            {"zip": "1000", "name": "Lausanne", "canton": "VD"},
            {"zip": "1200", "name": "Genève", "canton": "GE"}
        ]
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'swiss_cities.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"cities": fallback_cities}, f, ensure_ascii=False, indent=2)
        
        print("⚠️ Liste minimale de villes sauvegardée")

if __name__ == "__main__":
    download_swiss_cities()
