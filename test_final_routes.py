#!/usr/bin/env python3
"""
Test final pour vérifier que tout fonctionne avec le système de fallback amélioré
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'handlers'))

from utils.route_distance import get_route_distance_with_fallback
from trip_handlers import get_coords
from geopy.distance import geodesic

def test_multiple_routes():
    """Test le calcul de distance pour plusieurs trajets"""
    
    routes_to_test = [
        ("Fribourg", "Lausanne"),
        ("Lausanne", "Genève"),
        ("Zürich", "Berne"),
        ("Bâle", "Lausanne")
    ]
    
    for start_city, end_city in routes_to_test:
        print(f"\n=== {start_city} -> {end_city} ===")
        
        # Récupérer les coordonnées
        start_coords = get_coords(start_city)
        end_coords = get_coords(end_city)
        
        if not start_coords or not end_coords:
            print(f"❌ Coordonnées non trouvées pour {start_city} ou {end_city}")
            continue
            
        print(f"{start_city}: {start_coords}")
        print(f"{end_city}: {end_coords}")
        
        # Distance à vol d'oiseau
        geodesic_distance = geodesic(start_coords, end_coords).kilometers
        print(f"Distance géodésique: {geodesic_distance:.2f} km")
        
        # Distance routière avec fallback
        route_distance, is_route = get_route_distance_with_fallback(start_coords, end_coords)
        
        if route_distance is None:
            print("❌ Impossible de calculer la distance")
            continue
            
        status = "✅ vraie route" if is_route else "⚠️ fallback vol d'oiseau"
        print(f"Distance routière: {route_distance:.2f} km ({status})")
        
        # Calculer la différence
        diff_km = route_distance - geodesic_distance
        diff_pct = (diff_km / geodesic_distance) * 100 if geodesic_distance > 0 else 0
        
        print(f"Différence: +{diff_km:.2f} km (+{diff_pct:.1f}%)")
        
        # Test de prix (juste pour vérifier)
        base_price = 0.5 if route_distance <= 50 else max(0.3, 0.5 - (route_distance - 50) * 0.01)
        calculated_price = route_distance * base_price
        print(f"Prix calculé: {calculated_price:.2f} CHF")

if __name__ == "__main__":
    test_multiple_routes()
