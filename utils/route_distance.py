"""
Module robuste pour calculer la distance routière entre deux points
Utilise un calcul d'estimation basé sur la distance haversine avec correction topographique
"""
import math
from typing import Tuple, Optional

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance haversine (vol d'oiseau) entre deux points GPS
    """
    R = 6371  # Rayon de la Terre en km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def estimate_road_distance(lat1, lon1, lat2, lon2):
    """
    Estime la distance par route en utilisant la distance haversine
    avec des facteurs de correction topographiques raffinés pour la Suisse
    """
    # Calcul de la distance haversine (vol d'oiseau)
    distance_direct = haversine_distance(lat1, lon1, lat2, lon2)
    
    # Si distance très courte, retourner directement
    if distance_direct < 0.5:
        return distance_direct
    
    # Calcul du point médian
    mid_lat = (lat1 + lat2) / 2
    mid_lon = (lon1 + lon2) / 2
    
    # Facteur de correction basé sur la géographie suisse détaillée
    correction_factor = 1.2  # Facteur par défaut
    
    # Détection spéciale pour éviter les distances trop courtes entre villes éloignées
    if distance_direct < 5.0:
        # Vérifier si ce sont des villes importantes mais éloignées (erreur probable de coordonnées)
        major_cities = ["chur", "davos", "lugano", "bellinzona", "interlaken", "berne"]
        city1_name = f"{lat1:.1f},{lon1:.1f}"  # Placeholder - devrait venir du nom réel
        city2_name = f"{lat2:.1f},{lon2:.1f}"  # Placeholder - devrait venir du nom réel
        
        # Si distance très courte mais coordonnées très différentes, corriger
        lat_diff = abs(lat1 - lat2)
        lon_diff = abs(lon1 - lon2)
        if lat_diff > 0.5 or lon_diff > 0.5:
            distance_direct = max(distance_direct, 
                                ((lat_diff * 111) ** 2 + (lon_diff * 111 * 0.7) ** 2) ** 0.5)
    
    # Alpes (routes de montagne très sinueuses)
    if mid_lat < 46.8 and mid_lon > 8.5:  # Alpes orientales (Grisons)
        correction_factor = 1.6
    elif mid_lat < 46.6 and 7.0 <= mid_lon <= 8.5:  # Alpes centrales (Valais)
        correction_factor = 1.5
    elif mid_lat < 46.8 and 6.5 <= mid_lon <= 7.5:  # Alpes occidentales
        correction_factor = 1.4
    
    # Jura (collines et vallées)
    elif mid_lat > 47.2 and mid_lon < 7.5:
        correction_factor = 1.3
    
    # Plateau suisse (réseau routier efficace)
    elif 46.4 <= mid_lat <= 47.6 and 7.0 <= mid_lon <= 8.8:
        correction_factor = 1.15
    
    # Région du Léman (terrain vallonné)
    elif mid_lat > 46.0 and mid_lon < 7.0:
        correction_factor = 1.25
    
    # Tessin (routes de montagne du sud)
    elif mid_lat < 46.5 and mid_lon > 8.5:
        correction_factor = 1.45
    
    # Ajustement pour les très courtes distances (moins de détours)
    if distance_direct < 10:
        correction_factor = min(correction_factor, 1.15)
    
    # Ajustement pour les très longues distances (autoroutes plus efficaces)
    elif distance_direct > 200:
        correction_factor = max(correction_factor - 0.1, 1.1)
    
    return distance_direct * correction_factor

def get_route_distance_km(start_coords: Tuple[float, float], 
                         end_coords: Tuple[float, float],
                         start_name: str = "", 
                         end_name: str = "") -> Optional[float]:
    """
    Calcule la distance routière entre deux points GPS.
    Utilise un calcul d'estimation robuste basé sur haversine avec correction topographique.
    """
    try:
        lat1, lon1 = start_coords
        lat2, lon2 = end_coords
        
        # Validation des coordonnées
        if not (-90 <= lat1 <= 90 and -180 <= lon1 <= 180 and 
                -90 <= lat2 <= 90 and -180 <= lon2 <= 180):
            return None
        
        # Vérification que les coordonnées sont en Suisse
        if not (45.8 <= lat1 <= 47.8 and 5.9 <= lon1 <= 10.5 and
                45.8 <= lat2 <= 47.8 and 5.9 <= lon2 <= 10.5):
            return None
        
        # Si les points sont très proches, retourner la distance haversine
        haversine_dist = haversine_distance(lat1, lon1, lat2, lon2)
        if haversine_dist < 0.5:  # Moins de 500m
            return max(0.1, haversine_dist)  # Minimum 100m
        
        # Calculer la distance estimée par route
        estimated_distance = estimate_road_distance(lat1, lon1, lat2, lon2)
        
        return round(estimated_distance, 1)
        
    except Exception as e:
        return None