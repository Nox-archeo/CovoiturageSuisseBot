#!/usr/bin/env python3
"""
Debug spécifique pour Fribourg-Lausanne
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.route_distance import get_route_distance_with_fallback
from geopy.distance import geodesic
import sys
import os

# Importer la fonction get_coords depuis trip_handlers
sys.path.append(os.path.join(os.path.dirname(__file__), 'handlers'))
from trip_handlers import get_coords

def debug_fribourg_lausanne():
    print("=== DEBUG FRIBOURG-LAUSANNE ===")
    
    # Récupérer les coordonnées
    fribourg_coords = get_coords("Fribourg")
    lausanne_coords = get_coords("Lausanne")
    
    print(f"Fribourg coords: {fribourg_coords}")
    print(f"Lausanne coords: {lausanne_coords}")
    
    if not fribourg_coords or not lausanne_coords:
        print("❌ Coordonnées non trouvées")
        return
    
    # Calculer la distance à vol d'oiseau
    geodesic_distance = geodesic(fribourg_coords, lausanne_coords).kilometers
    print(f"Distance géodésique (vol d'oiseau): {geodesic_distance:.2f} km")
    
    # Calculer la distance routière
    print("\n--- Calcul distance routière ---")
    route_distance, is_route = get_route_distance_with_fallback(fribourg_coords, lausanne_coords)
    
    if route_distance is None:
        print("❌ Impossible de calculer la distance")
        return
        
    status = "vraie route" if is_route else "fallback vol d'oiseau"
    print(f"Distance routière (avec fallback): {route_distance:.2f} km ({status})")
    
    # Calculer la différence
    diff_km = route_distance - geodesic_distance
    diff_pct = (diff_km / geodesic_distance) * 100 if geodesic_distance > 0 else 0
    
    print(f"\nDifférence: +{diff_km:.2f} km (+{diff_pct:.1f}%)")
    
    # Test de prix
    print(f"\n--- Test calcul prix ---")
    # Prix au kilomètre (de 0.5 à 0.3 CHF selon distance)
    base_price = 0.5 if route_distance <= 50 else max(0.3, 0.5 - (route_distance - 50) * 0.01)
    calculated_price = route_distance * base_price
    print(f"Prix calculé: {calculated_price:.2f} CHF (base: {base_price:.2f} CHF/km)")

if __name__ == "__main__":
    debug_fribourg_lausanne()
