import pandas as pd
import json
import os

def convert_excel_to_json():
    """Convertit le fichier Excel de l'OFS en JSON"""
    print("📥 Chargement des données...")
    
    # Charger le fichier Excel (à télécharger depuis le site de l'OFS)
    df = pd.read_excel('data/liste_communes.xlsx')
    
    # Convertir en format JSON
    cities = []
    seen = set()  # Pour éviter les doublons
    
    for _, row in df.iterrows():
        npa = str(row['NPA'])
        nom = row['Nom de la commune']
        canton = row['Canton']
        
        key = f"{npa}-{nom}"
        if key not in seen:
            seen.add(key)
            cities.append({
                "zip": npa,
                "name": nom,
                "canton": canton
            })
    
    # Trier par NPA puis nom
    cities.sort(key=lambda x: (x['zip'], x['name']))
    
    # Sauvegarder en JSON
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cities.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"cities": cities}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(cities)} villes sauvegardées dans cities.json")

if __name__ == "__main__":
    convert_excel_to_json()
