#!/usr/bin/env python3
import json
from typing import Dict, Any, List

def load_swiss_localities() -> Dict[str, Any]:
    """Charge les données des localités suisses"""
    try:
        with open('/Users/margaux/CovoiturageSuisse/data/swiss_localities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement des localités suisses: {e}")
        return {}

def get_cities_by_canton(canton_code: str) -> List[str]:
    """Récupère les villes d'un canton donné"""
    localities = load_swiss_localities()
    cities = []
    
    for city_name, city_data in localities.items():
        if city_data.get('canton') == canton_code:
            cities.append(city_name)
    
    # Trier par ordre alphabétique
    cities.sort()
    
    print(f"Canton {canton_code}: {len(cities)} villes trouvées")
    if len(cities) > 0 and len(cities) <= 10:
        print(f"Villes du canton {canton_code}: {', '.join(cities)}")
    elif len(cities) > 10:
        print(f"Premières villes du canton {canton_code}: {', '.join(cities[:10])}...")
    
    return cities

if __name__ == "__main__":
    print("Test de la fonction get_cities_by_canton pour le canton FR")
    print("=" * 60)
    
    # Test canton FR
    cities_fr = get_cities_by_canton("FR")
    print(f"\nNombre total de villes en Fribourg: {len(cities_fr)}")
    
    # Vérifier si Giffers est dans la liste
    if "Giffers" in cities_fr:
        print("✅ Giffers est bien dans la liste des villes de Fribourg")
    else:
        print("❌ Giffers n'est PAS dans la liste des villes de Fribourg")
    
    # Vérifier quelques villes de Fribourg qu'on connaît
    test_cities = ["Fribourg", "Bulle", "Giffers", "Rechthalten"]
    print(f"\nVérification des villes de test: {test_cities}")
    for city in test_cities:
        if city in cities_fr:
            print(f"  ✅ {city}")
        else:
            print(f"  ❌ {city}")
    
    # Afficher les premières villes trouvées
    if cities_fr:
        print(f"\nPremières 20 villes de Fribourg:")
        for i, city in enumerate(cities_fr[:20]):
            print(f"  {i+1:2d}. {city}")
