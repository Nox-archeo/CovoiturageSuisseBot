import json
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class CitiesManager:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.cities = []
        self.load_and_clean()
    
    def load_and_clean(self) -> None:
        """Charge et nettoie le fichier cities.json"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cities = data.get('cities', [])
            
            # Supprimer les doublons en gardant les entrées les plus complètes
            cleaned = {}
            for city in cities:
                name = city['name'].strip()
                if name not in cleaned or len(city) > len(cleaned[name]):
                    cleaned[name] = city
            
            self.cities = list(cleaned.values())
            self.save_cities()
            
            logger.info(f"Loaded {len(self.cities)} cities after cleaning")
            
        except Exception as e:
            logger.error(f"Error loading cities: {str(e)}")
            self.cities = []
    
    def save_cities(self) -> None:
        """Sauvegarde les villes dans le fichier JSON"""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump({'cities': self.cities}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cities: {str(e)}")
    
    def find_city(self, query: str) -> List[Dict]:
        """Recherche une ville"""
        query = query.lower().strip()
        return [
            city for city in self.cities
            if query in city['name'].lower() or 
               query in city.get('npa', '').lower() or
               query in city.get('canton', '').lower()
        ]

    def find_locality(self, query: str) -> List[Dict]:
        """Recherche une localité par nom ou NPA"""
        query = query.lower().strip()
        matches = [
            city for city in self.cities
            if query in city['name'].lower() or 
               query in str(city.get('npa', '')).lower()
        ]
        return matches[:5]  # Limite à 5 résultats

    def format_locality_result(self, city: Dict) -> str:
        """Formate l'affichage d'une ville"""
        return f"{city['name']} ({city['npa']}) - {city['canton']}"

    def get_popular_cities(self, limit: int = 6) -> List[Dict]:
        """Retourne les villes populaires"""
        popular = ["Genève", "Lausanne", "Berne", "Zürich", "Bâle", "Fribourg"]
        return [city for city in self.cities if city['name'] in popular][:limit]
