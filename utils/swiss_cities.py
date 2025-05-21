from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import os
import logging
from unidecode import unidecode

logger = logging.getLogger(__name__)

# Chemin vers le fichier JSON des localités suisses
JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'swiss_localities.json')

# Cache pour les données chargées
_localities_data = None

def load_localities() -> Dict[str, Dict[str, str]]:
    """Charge les données des localités suisses depuis le fichier JSON"""
    global _localities_data
    
    if _localities_data is None:
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                _localities_data = json.load(f)
            logger.info(f"Données des localités suisses chargées: {len(_localities_data)} localités")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des localités suisses: {e}")
            _localities_data = {}
    
    return _localities_data

# Pour assurer la compatibilité avec le code existant
def load_all_localities() -> Dict[str, Dict[str, str]]:
    """Fonction alias pour load_localities pour compatibilité"""
    return load_localities()

def find_locality(query: str) -> List[Dict[str, str]]:
    """
    Recherche une localité dans les données suisses.
    Peut chercher par nom de ville ou code postal.
    
    Args:
        query: Partie du nom de la ville ou code postal
        
    Returns:
        Liste de localités correspondantes
    """
    localities = load_localities()
    results = []
    
    if not query or not localities:
        return results
    
    query = query.strip().lower()
    
    # Si la requête ressemble à un code postal (uniquement des chiffres)
    if query.isdigit():
        for name, data in localities.items():
            if data.get("zip", "").startswith(query):
                results.append({
                    "name": name,
                    "canton": data.get("canton", ""),
                    "zip": data.get("zip", "")
                })
    # Sinon, on cherche par nom
    else:
        for name, data in localities.items():
            if query in name.lower():
                results.append({
                    "name": name,
                    "canton": data.get("canton", ""),
                    "zip": data.get("zip", "")
                })
    
    # Trier les résultats par nom
    results.sort(key=lambda x: x["name"])
    return results

def is_valid_locality(locality: str) -> bool:
    """Vérifie si une localité existe dans la base"""
    if not locality:
        return False
    localities = load_localities()
    for loc_data in localities.values():
        if loc_data['name'].lower() == locality.lower():
            return True
    return False

def format_locality_result(locality: Dict[str, str]) -> str:
    """Formate le résultat d'une localité pour l'affichage"""
    return f"{locality['name']} ({locality['canton']}) - {locality['zip']}"

def get_locality_by_name(name: str) -> Optional[Dict[str, str]]:
    """Récupère les détails d'une localité par son nom"""
    localities = load_localities()
    if name in localities:
        return {
            "name": name,
            "canton": localities[name].get("canton", ""),
            "zip": localities[name].get("zip", "")
        }
    return None

# Fonction utilitaire pour récupérer directement les villes principales pour les boutons
def get_major_cities() -> List[str]:
    """Retourne une liste des principales villes suisses pour les boutons rapides"""
    return ["Fribourg", "Genève", "Lausanne", "Zürich", "Berne", "Bâle"]
