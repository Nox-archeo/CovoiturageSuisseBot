"""
Module pour calculer la distance routière entre deux points via l'API OpenRouteService
"""
import requests
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Clé API OpenRouteService
ORS_API_KEY = "5b3ce3597851110001cf62483e3812a7d9294d5e9d04f4656f862372"
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

def get_route_distance_km(start_coords: Tuple[float, float], end_coords: Tuple[float, float], start_city_name: str = None, end_city_name: str = None) -> Optional[float]:
    """
    Calcule la distance routière entre deux points en utilisant l'API OpenRouteService.
    Essaie plusieurs variantes de coordonnées si les coordonnées exactes ne fonctionnent pas.
    
    Args:
        start_coords: Tuple (latitude, longitude) du point de départ
        end_coords: Tuple (latitude, longitude) du point d'arrivée
        start_city_name: Nom de la ville de départ (optionnel, aide à trouver de meilleures coordonnées)
        end_city_name: Nom de la ville d'arrivée (optionnel, aide à trouver de meilleures coordonnées)
        
    Returns:
        Distance en kilomètres, ou None en cas d'erreur
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
        
        # 1. Essayer avec les coordonnées exactes
        result = try_api_request(start_lat, start_lon, end_lat, end_lon)
        if result is not None:
            logger.info(f"Distance routière calculée (coordonnées exactes): {result} km")
            return result
        
        # 2. Essayer avec des coordonnées légèrement arrondies (peut-être plus proches de vraies routes)
        start_lat_rounded = round(start_lat, 4)
        start_lon_rounded = round(start_lon, 4)
        end_lat_rounded = round(end_lat, 4)
        end_lon_rounded = round(end_lon, 4)
        
        result = try_api_request(start_lat_rounded, start_lon_rounded, end_lat_rounded, end_lon_rounded)
        if result is not None:
            logger.info(f"Distance routière calculée (coordonnées arrondies): {result} km")
            return result
        
        # 3. Si c'est des villes importantes, utiliser des coordonnées connues qui marchent
        known_coords = {
            'fribourg': (46.8058, 7.1530),
            'dudingen': (46.8497, 7.1904),  # Düdingen - coordonnées fonctionnelles
            'bulle': (46.6191, 7.0581),
            'lausanne': (46.5197, 6.6323),
            'geneve': (46.2044, 6.1432),
            'berne': (46.9481, 7.4474),
            'zurich': (47.3769, 8.5417),
            'bale': (47.5596, 7.5886),
            'lucerne': (47.0502, 8.3093),
            'neuchatel': (46.9895, 6.9293),
            'sion': (46.2311, 7.3589),
            'montreux': (46.4311, 6.9130),
            'vevey': (46.4603, 6.8419),
            'morges': (46.5093, 6.4983),
            'nyon': (46.3821, 6.2403),
            'martigny': (46.1031, 7.0727),
            'aigle': (46.3179, 6.9689),
            'sierre': (46.2923, 7.5323),
            'yverdon': (46.7786, 6.6409),
            'saint-gall': (47.4245, 9.3767),
            'coire': (46.8481, 9.5284),
            'lugano': (46.0037, 8.9511),
            'bellinzone': (46.1944, 9.0175)
        }
        
        def find_known_city(lat, lon, city_name=None):
            # 1. Si on a le nom de la ville, chercher d'abord par nom exact
            if city_name:
                city_name_clean = city_name.lower().replace('ü', 'u').replace('ä', 'a').replace('ö', 'o')
                for known_city, (city_lat, city_lon) in known_coords.items():
                    if known_city.lower() == city_name_clean:
                        logger.info(f"Ville trouvée par nom: {city_name} -> {known_city} {(city_lat, city_lon)}")
                        return known_city, (city_lat, city_lon)
            
            # 2. Cherche si les coordonnées correspondent à une ville connue (tolérance de 0.2°)
            for city, (city_lat, city_lon) in known_coords.items():
                lat_diff = abs(lat - city_lat)
                lon_diff = abs(lon - city_lon)
                if lat_diff < 0.2 and lon_diff < 0.2:
                    logger.info(f"Coordonnées ({lat}, {lon}) correspondent à {city} (diff: lat={lat_diff:.3f}, lon={lon_diff:.3f})")
                    return city, (city_lat, city_lon)
            
            # 3. Si pas de correspondance directe, essayons de deviner par région
            # Région lémanique (autour du lac Léman)
            if 46.2 <= lat <= 46.8 and 6.1 <= lon <= 7.2:
                if lat < 46.3:  # Sud du lac = Genève
                    return 'geneve', known_coords['geneve']
                elif lat > 46.5:  # Nord du lac = Lausanne
                    return 'lausanne', known_coords['lausanne']
                elif lon > 6.8:  # Est = Montreux/Vevey
                    return 'montreux', known_coords['montreux']
            
            # Région fribourgeoise
            elif 46.6 <= lat <= 46.9 and 7.0 <= lon <= 7.2:
                return 'fribourg', known_coords['fribourg']
            
            # Région bernoise 
            elif 46.8 <= lat <= 47.1 and 7.3 <= lon <= 7.6:
                return 'berne', known_coords['berne']
                
            return None, None
        
        start_city, start_known = find_known_city(start_lat, start_lon, start_city_name)
        end_city, end_known = find_known_city(end_lat, end_lon, end_city_name)
        
        if start_known and end_known:
            result = try_api_request(start_known[0], start_known[1], end_known[0], end_known[1])
            if result is not None:
                logger.info(f"Distance routière calculée (coordonnées connues {start_city}->{end_city}): {result} km")
                return result
        
        # Toutes les tentatives ont échoué
        logger.error(f"Impossible de calculer la distance routière entre {start_coords} et {end_coords}")
        return None
            
    except requests.RequestException as e:
        logger.error(f"Erreur réseau lors du calcul de distance routière: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Erreur lors du parsing de la réponse OpenRouteService: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors du calcul de distance routière: {e}")
        return None

def get_route_distance_with_fallback(start_coords: Tuple[float, float], end_coords: Tuple[float, float], start_city_name: str = None, end_city_name: str = None) -> Tuple[Optional[float], bool]:
    """
    Calcule la distance routière avec fallback vers la distance à vol d'oiseau en cas d'erreur.
    
    Args:
        start_coords: Tuple (latitude, longitude) du point de départ
        end_coords: Tuple (latitude, longitude) du point d'arrivée
        start_city_name: Nom de la ville de départ (optionnel)
        end_city_name: Nom de la ville d'arrivée (optionnel)
        
    Returns:
        Tuple (distance_km, is_route_distance)
        - distance_km: Distance en kilomètres
        - is_route_distance: True si c'est la vraie distance routière, False si c'est à vol d'oiseau
    """
    # Essayer d'abord la distance routière
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
