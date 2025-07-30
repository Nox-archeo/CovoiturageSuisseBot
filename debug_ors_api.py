#!/usr/bin/env python3
"""
Debug avancé pour comprendre pourquoi l'API OpenRouteService échoue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'handlers'))

import requests
import logging
from trip_handlers import get_coords

# Configurer le logging pour voir tous les détails
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Clé API OpenRouteService
ORS_API_KEY = "5b3ce3597851110001cf62483e3812a7d9294d5e9d04f4656f862372"
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

def test_ors_api_direct(start_coords, end_coords):
    """Test direct de l'API OpenRouteService avec logs détaillés"""
    
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    
    print(f"=== Test API OpenRouteService ===")
    print(f"Départ: {start_lat}, {start_lon}")
    print(f"Arrivée: {end_lat}, {end_lon}")
    
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
    
    print(f"URL: {ORS_BASE_URL}")
    print(f"Headers: {headers}")
    print(f"Body: {body}")
    
    try:
        response = requests.post(ORS_BASE_URL, json=body, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Succès! Réponse: {data}")
            distance_meters = data['routes'][0]['summary']['distance']
            distance_km = distance_meters / 1000.0
            print(f"Distance: {distance_km:.2f} km")
            return distance_km
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_coords_variations():
    """Test avec différentes variations de coordonnées"""
    
    # Coordonnées originales
    fribourg_coords = get_coords("Fribourg")
    lausanne_coords = get_coords("Lausanne")
    
    print("=== Test coordonnées originales ===")
    test_ors_api_direct(fribourg_coords, lausanne_coords)
    
    # Coordonnées arrondies
    print("\n=== Test coordonnées arrondies (3 décimales) ===")
    fribourg_rounded = (round(fribourg_coords[0], 3), round(fribourg_coords[1], 3))
    lausanne_rounded = (round(lausanne_coords[0], 3), round(lausanne_coords[1], 3))
    test_ors_api_direct(fribourg_rounded, lausanne_rounded)
    
    # Coordonnées de centre-ville approximatives
    print("\n=== Test coordonnées centre-ville approximatives ===")
    # Fribourg centre (approximatif)
    fribourg_center = (46.8016, 7.1500)
    # Lausanne centre (approximatif)  
    lausanne_center = (46.5197, 6.6323)
    test_ors_api_direct(fribourg_center, lausanne_center)

if __name__ == "__main__":
    test_coords_variations()
