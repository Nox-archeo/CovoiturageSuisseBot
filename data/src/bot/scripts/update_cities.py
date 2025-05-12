import json
import os
import requests

def update_cities():
    """Met à jour le fichier cities.json avec les données de la Poste"""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    output_file = os.path.join(output_dir, 'cities.json')
    
    try:
        # Télécharge depuis l'API de la Poste
        response = requests.get(
            'https://swisspost.opendatasoft.com/api/explore/v2.1/catalog/datasets/plz-verzeichnis/records',
            params={'limit': -1}
        )
        
        if response.status_code == 200:
            data = response.json()
            cities = []
            seen = set()
            
            for item in data.get('results', []):
                npa = str(item.get('plz', '')).zfill(4)
                name = item.get('ortbez18', '')
                canton = item.get('kanton', '')
                
                if npa and name and canton:
                    key = f"{npa}-{name}"
                    if key not in seen:
                        seen.add(key)
                        cities.append({
                            "npa": npa,
                            "name": name,
                            "canton": canton
                        })
            
            # Sauvegarde
            os.makedirs(output_dir, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"cities": cities}, f, ensure_ascii=False, indent=2)
                
            print(f"✅ {len(cities)} villes enregistrées")
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    update_cities()
