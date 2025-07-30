#!/usr/bin/env python3
"""
Test final de création de trajet Fribourg-Düdingen
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.create_trip_handler import compute_price_auto

def main():
    print("=== TEST CRÉATION TRAJET FRIBOURG → DÜDINGEN ===")
    
    # Test avec les vrais noms de villes
    result = compute_price_auto("Fribourg", "Düdingen")
    
    if result[0] is None or result[1] is None:
        print("❌ Échec du calcul")
        return
    
    distance, price = result
    print(f"✅ Distance calculée: {distance} km")
    print(f"✅ Prix calculé: {price:.2f} CHF")
    
    # Comparaison avec l'ancien système (fallback vol d'oiseau)
    print(f"\n📊 Comparaison:")
    print(f"   Ancien prix (20.14 km): 15.10 CHF")
    print(f"   Nouveau prix ({distance} km): {price:.2f} CHF")
    print(f"   Économie: {15.10 - price:.2f} CHF ({((15.10 - price) / 15.10 * 100):.1f}%)")
    
    # Vérification que le prix est dans la fourchette attendue
    expected_min = 5.0  # 7 km * 0.75 = 5.25, arrondi à 5.00
    expected_max = 7.0  # 9 km * 0.75 = 6.75, arrondi à 6.75
    
    if expected_min <= price <= expected_max:
        print(f"✅ Prix dans la fourchette attendue ({expected_min}-{expected_max} CHF)")
    else:
        print(f"⚠️ Prix hors fourchette attendue ({expected_min}-{expected_max} CHF)")

if __name__ == "__main__":
    main()
