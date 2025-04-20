from typing import List, Dict
from pathlib import Path
import json
import logging
from unidecode import unidecode

logger = logging.getLogger(__name__)

# Structure de données pour les localités
SWISS_LOCALITIES: Dict[str, Dict[str, str]] = {
    # Format: "Nom": {"zip": "code postal", "canton": "canton"}
    "Fribourg": {"zip": "1700", "canton": "FR"},
    "Givisiez": {"zip": "1762", "canton": "FR"},
    "Granges-Paccot": {"zip": "1763", "canton": "FR"},
    "Marly": {"zip": "1723", "canton": "FR"},
    "Villars-sur-Glâne": {"zip": "1752", "canton": "FR"},
    "Bulle": {"zip": "1630", "canton": "FR"},
    "Rechthalten": {"zip": "1718", "canton": "FR"},
    # ... Chargement du fichier complet des localités
}

def load_localities() -> Dict:
    """Charge la liste des localités depuis le fichier JSON"""
    try:
        file_path = Path(__file__).parent.parent / 'data' / 'swiss_localities.json'
        logger.info(f"Loading localities from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} localities")
            return data
    except FileNotFoundError:
        logger.error(f"Localities file not found at {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return {}

def find_locality(query: str) -> List[Dict]:
    """Recherche une localité par nom ou NPA avec gestion des accents"""
    if not query:
        return []
        
    localities = load_localities()
    if not localities:
        logger.error("No localities loaded!")
        return []

    results = []
    query = query.lower().strip()
    query_unaccented = unidecode(query)
    
    logger.info(f"Searching for: {query}")

    # Recherche par NPA
    if query.isdigit():
        for loc_data in localities.values():
            if loc_data['zip'].startswith(query):
                results.append(loc_data)
                logger.info(f"Found by ZIP: {loc_data['name']}")

    # Recherche par nom
    else:
        for loc_data in localities.values():
            name_lower = loc_data['name'].lower()
            name_unaccented = unidecode(name_lower)
            
            # Correspondance exacte
            if query == name_lower or query_unaccented == name_unaccented:
                results.insert(0, loc_data)
                logger.info(f"Exact match: {loc_data['name']}")
                continue
                
            # Correspondance partielle
            if query in name_lower or query_unaccented in name_unaccented:
                results.append(loc_data)
                logger.info(f"Partial match: {loc_data['name']}")

    logger.info(f"Found {len(results)} matches")
    return results[:5]

def is_valid_locality(locality: str) -> bool:
    """Vérifie si une localité existe dans la base"""
    if not locality:
        return False
    localities = load_localities()
    for loc_data in localities.values():
        if loc_data['name'].lower() == locality.lower():
            return True
    return False

def format_locality_result(locality: Dict) -> str:
    """Formate l'affichage d'une localité"""
    return f"{locality['name']} ({locality['zip']}, {locality['canton']})"

def get_locality_info(name: str) -> Dict[str, str]:
    """Récupère les informations d'une localité par son nom"""
    localities = load_localities()
    return localities.get(name, None)
