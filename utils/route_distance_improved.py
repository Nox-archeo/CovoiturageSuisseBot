"""
Module amélioré pour calculer la distance routière entre deux points via l'API OpenRouteService
CORRECTED VERSION - Gère mieux les coordonnées GPS précises qui ne sont pas "routables"
"""
import requests
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Clé API OpenRouteService
ORS_API_KEY = "5b3ce3597851110001cf62483e3812a7d9294d5e9d04f4656f862372"
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

def find_routable_coords(city_name: str, coords: Tuple[float, float]) -> Tuple[float, float]:
    """
    Trouve des coordonnées 'routables' pour une ville donnée.
    Utilise des coordonnées connues et testées pour les principales villes.
    """
    lat, lon = coords
    
    # Coordonnées connues et TESTÉES pour être routables
    routable_coords = {
        # Région lémanique - TESTÉES ✅
        'lausanne': (46.5197, 6.6323),
        'genève': (46.2044, 6.1432),
        'geneve': (46.2044, 6.1432),
        'montreux': (46.4311, 6.9130),
        'vevey': (46.4603, 6.8419),
        'morges': (46.5093, 6.4983),
        'nyon': (46.3821, 6.2403),
        
        # Région fribourgeoise - TESTÉES ✅
        'fribourg': (46.8016, 7.1530),  # TESTÉ et fonctionne
        'bulle': (46.6191, 7.0581),
        'romont': (46.6938, 6.9164),
        
        # Autres grandes villes - TESTÉES ✅
        'berne': (46.9481, 7.4474),
        'zurich': (47.3769, 8.5417),
        'winterthur': (47.5008, 8.7241),
        'bale': (47.5596, 7.5886),
        'bâle': (47.5596, 7.5886),
        'basel': (47.5596, 7.5886),
        'lucerne': (47.0502, 8.3093),
        'neuchatel': (46.9895, 6.9293),
        'neuchâtel': (46.9895, 6.9293),
        'sion': (46.2311, 7.3589),
        
        # Petites communes problématiques - coordonnées approximatives mais routables
        'corpataux-magnedens': (46.7800, 7.1200),
        'corpataux': (46.7800, 7.1200),
        'farvagny': (46.7650, 7.0800),
        'rossens': (46.7300, 7.0900),
        'vuisternens-en-ogoz': (46.7500, 7.1100),
        'posieux': (46.7600, 7.1300),
        
        # Ajouter d'autres communes selon les besoins
        'baden': (47.4767, 8.3067),  # Coordonnées centre-ville Baden
        'dudingen': (46.8497, 7.1904),
        'düdingen': (46.8497, 7.1904),
    }
    
    # Recherche par nom (insensible à la casse et variations)
    city_lower = city_name.lower().strip()
    
    # Variantes de noms possibles
    variants = [
        city_lower,
        city_lower.replace('-', ' '),
        city_lower.replace(' ', '-'),
        city_lower.replace('ü', 'u').replace('ä', 'a').replace('ö', 'o').replace('é', 'e').replace('è', 'e'),
        city_lower.split(' ')[0] if ' ' in city_lower else city_lower,  # Premier mot seulement
        city_lower.split('-')[0] if '-' in city_lower else city_lower,  # Avant le tiret
    ]
    
    for variant in variants:
        if variant in routable_coords:
            logger.info(f"Coordonnées routables trouvées pour {city_name}: {routable_coords[variant]}")
            return routable_coords[variant]
    
    # Si pas de correspondance exacte, utiliser une logique géographique intelligente
    # Arrondir les coordonnées à 4 décimales et ajuster vers des centres routables
    
    # Région fribourgeoise
    if 46.6 <= lat <= 46.9 and 7.0 <= lon <= 7.3:
        # Ajuster vers Fribourg centre (point routable connu)
        adjusted_lat = lat + (46.8016 - lat) * 0.15  # 15% vers Fribourg
        adjusted_lon = lon + (7.1530 - lon) * 0.15
        return (round(adjusted_lat, 4), round(adjusted_lon, 4))
    
    # Région lémanique
    elif 46.2 <= lat <= 46.8 and 6.1 <= lon <= 7.2:
        if lat < 46.3:  # Sud du lac = Genève
            return (46.2044, 6.1432)
        elif lat > 46.5:  # Nord du lac = Lausanne
            return (46.5197, 6.6323)
        else:  # Centre = Montreux/Vevey
            return (46.4311, 6.9130)
    
    # Région zurichoise
    elif 47.2 <= lat <= 47.8 and 8.0 <= lon <= 9.0:
        if lat > 47.5:  # Nord = Winterthur
            return (47.5008, 8.7241)
        else:  # Centre = Zurich
            return (47.3769, 8.5417)
    
    # Par défaut, arrondir et espérer que ça marche
    return (round(lat, 4), round(lon, 4))

def get_route_distance_km(start_coords: Tuple[float, float], end_coords: Tuple[float, float], start_city_name: str = None, end_city_name: str = None) -> Optional[float]:
    """
    Calcule la distance routière entre deux points en utilisant l'API OpenRouteService.
    VERSION AMÉLIORÉE avec gestion des coordonnées non-routables.
    """
    
    def try_api_request(start_lat, start_lon, end_lat, end_lon):
        """Essaie une requête API avec les coordonnées données"""
        try:
            headers = {
                'Authorization': ORS_API_KEY,
                'Content-Type': 'application/json'
            }
            
            body = {
                "coordinates": [
                    [start_lon, start_lat],  # Point de départ [lon, lat]
                    [end_lon, end_lat]       # Point d'arrivée [lon, lat]
                ]
            }
            
            response = requests.post(ORS_BASE_URL, json=body, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                distance_meters = data['routes'][0]['summary']['distance']
                distance_km = distance_meters / 1000.0
                return round(distance_km, 2)
            else:
                return None
                
        except Exception:
            return None
    
    try:
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        
        # 1. Essayer avec les coordonnées originales
        result = try_api_request(start_lat, start_lon, end_lat, end_lon)
        if result is not None:
            logger.info(f"Distance routière calculée (coordonnées originales): {result} km")
            return result
        
        # 2. Utiliser des coordonnées routables améliorées
        if start_city_name and end_city_name:
            start_routable = find_routable_coords(start_city_name, start_coords)
            end_routable = find_routable_coords(end_city_name, end_coords)
            
            result = try_api_request(start_routable[0], start_routable[1], end_routable[0], end_routable[1])
            if result is not None:
                logger.info(f"Distance routière calculée (coordonnées routables): {result} km pour {start_city_name} -> {end_city_name}")
                return result
        
        # 3. Essayer avec coordonnées arrondies (fallback)
        start_rounded = (round(start_lat, 4), round(start_lon, 4))
        end_rounded = (round(end_lat, 4), round(end_lon, 4))
        
        result = try_api_request(start_rounded[0], start_rounded[1], end_rounded[0], end_rounded[1])
        if result is not None:
            logger.info(f"Distance routière calculée (coordonnées arrondies): {result} km")
            return result
        
        # Toutes les tentatives ont échoué
        logger.error(f"Impossible de calculer la distance routière entre {start_coords} et {end_coords}")
        return None
            
    except Exception as e:
        logger.error(f"Erreur inattendue lors du calcul de distance routière: {e}")
        return None

def get_route_distance_with_fallback(start_coords: Tuple[float, float], end_coords: Tuple[float, float], start_city_name: str = None, end_city_name: str = None) -> Tuple[Optional[float], bool]:
    """
    Calcule la distance routière avec fallback vers la distance à vol d'oiseau en cas d'erreur.
    VERSION AMÉLIORÉE qui devrait réussir dans plus de cas.
    """
    # Essayer d'abord la distance routière améliorée
    route_distance = get_route_distance_km(start_coords, end_coords, start_city_name, end_city_name)
    
    if route_distance is not None:
        return route_distance, True
    
    # Fallback vers la distance à vol d'oiseau
    try:
        from geopy.distance import geodesic
        fallback_distance = geodesic(start_coords, end_coords).km
        logger.warning(f"Utilisation de la distance à vol d'oiseau en fallback: {fallback_distance:.2f} km")
        return round(fallback_distance, 2), False
    except Exception as e:
        logger.error(f"Erreur même avec le fallback géodésique: {e}")
        return None, False
