#!/usr/bin/env python3
"""
Test avec les vrais noms des villes suisses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'handlers'))

from trip_handlers import get_coords

def test_city_names():
    """Test les vrais noms des villes"""
    
    # Vrais noms dans la base
    cities_to_test = [
        "Luzern",  # au lieu de Lucerne
        # Cherchons d'autres
    ]
    
    # Aussi tester les variantes connues
    city_variants = [
        ("Berne", "Bern"),
        ("Lucerne", "Luzern"),
        ("Zürich", "Zurich"),
        ("Bâle", "Basel"),
        ("Bâle", "Bale"),
        ("Saint-Gall", "Sankt Gallen"),
        ("Saint-Gall", "St. Gallen"),
    ]
    
    print("=== TEST DES VARIANTES DE NOMS ===")
    
    for fr_name, de_name in city_variants:
        coords_fr = get_coords(fr_name)
        coords_de = get_coords(de_name)
        
        print(f"{fr_name}: {coords_fr}")
        print(f"{de_name}: {coords_de}")
        print()

if __name__ == "__main__":
    test_city_names()
