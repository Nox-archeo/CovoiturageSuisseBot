"""
Module pour l'arrondi des prix selon les pratiques suisses
"""

import math

def round_to_nearest_0_05_up(amount: float) -> float:
    """
    Arrondit au 0.05 CHF supérieur selon les standards suisses
    
    Args:
        amount: Montant à arrondir
        
    Returns:
        Montant arrondi au 0.05 CHF supérieur
        
    Examples:
        13.38 -> 13.40
        13.35 -> 13.35 (pas de changement)
        13.31 -> 13.35
        13.42 -> 13.45
    """
    if amount == 0:
        return 0.0
    
    # Multiplier par 20 pour convertir en unités de 0.05
    multiplied = amount * 20
    
    # Arrondir vers le haut (ceil)
    rounded_up = math.ceil(multiplied)
    
    # Reconvertir en CHF
    result = rounded_up / 20
    
    return round(result, 2)

def calculate_price_per_passenger(total_trip_price: float, passenger_count: int) -> float:
    """
    Calcule le prix par passager avec arrondi suisse vers le haut
    
    Args:
        total_trip_price: Prix total du trajet
        passenger_count: Nombre de passagers payants
        
    Returns:
        Prix par passager arrondi au 0.05 CHF supérieur
    """
    if passenger_count <= 0:
        return total_trip_price
    
    # Diviser le prix total par le nombre de passagers
    price_per_passenger = total_trip_price / passenger_count
    
    # Arrondir au 0.05 CHF supérieur
    return round_to_nearest_0_05_up(price_per_passenger)

def round_to_nearest_0_05(price):
    """
    Arrondit un prix au multiple de 0.05 CHF le plus proche (pratique suisse).
    
    Args:
        price (float): Prix à arrondir
        
    Returns:
        float: Prix arrondi au 0.05 CHF le plus proche
        
    Examples:
        >>> round_to_nearest_0_05(73.57)
        73.55
        >>> round_to_nearest_0_05(73.58)
        73.6
        >>> round_to_nearest_0_05(24.99)
        25.0
        >>> round_to_nearest_0_05(10.11)
        10.1
        >>> round_to_nearest_0_05(10.12)
        10.1
        >>> round_to_nearest_0_05(10.13)
        10.15
    """
    if price is None:
        return 0.0
    
    # Conversion en float au cas où ce serait une string
    try:
        price = float(price)
    except (ValueError, TypeError):
        return 0.0
    
    # Arrondi au multiple de 0.05 le plus proche
    # Multiplier par 20, arrondir à l'entier, puis diviser par 20
    return round(price * 20) / 20

def format_swiss_price(price):
    """
    Formate un prix selon les conventions suisses (avec arrondi 0.05).
    
    Args:
        price (float): Prix à formater
        
    Returns:
        str: Prix formaté (ex: "73.55" ou "25.00")
    """
    rounded_price = round_to_nearest_0_05(price)
    
    # Formatage avec 2 décimales, mais suppression du .00 si entier
    if rounded_price == int(rounded_price):
        return f"{int(rounded_price)}.00"
    else:
        return f"{rounded_price:.2f}"

def calculate_trip_price_swiss(distance_km):
    """
    Calcule le prix d'un trajet selon le barème progressif avec arrondi suisse.
    
    Barème :
    - 0.75 CHF/km jusqu'à 24 km
    - 0.50 CHF/km entre 25 et 40 km  
    - 0.25 CHF/km au-delà de 40 km
    
    Args:
        distance_km (float): Distance en kilomètres
        
    Returns:
        float: Prix arrondi au 0.05 CHF le plus proche
    """
    if distance_km is None or distance_km <= 0:
        return 0.0
    
    # Calcul progressif du prix
    price = 0.0
    
    # Tranche 1 : 0 à 24 km à 0.75 CHF/km
    if distance_km <= 24:
        price = distance_km * 0.75
    else:
        # Les premiers 24 km à 0.75 CHF/km
        price += 24 * 0.75
        remaining_distance = distance_km - 24
        
        # Tranche 2 : 25 à 40 km à 0.50 CHF/km
        if remaining_distance <= 16:  # 40 - 24 = 16 km max dans cette tranche
            price += remaining_distance * 0.50
        else:
            # Les 16 km suivants (25-40) à 0.50 CHF/km
            price += 16 * 0.50
            # Tranche 3 : au-delà de 40 km à 0.25 CHF/km
            price += (remaining_distance - 16) * 0.25
    
    # Arrondi final au 0.05 CHF
    return round_to_nearest_0_05(price)

# Tests unitaires intégrés
if __name__ == "__main__":
    # Tests de la fonction d'arrondi
    test_cases = [
        (73.57, 73.55),
        (73.58, 73.60),
        (24.99, 25.00),
        (10.11, 10.10),
        (10.12, 10.10),
        (10.13, 10.15),
        (10.17, 10.15),
        (10.18, 10.20),
        (0, 0.00),
        (None, 0.00),
        ("25.13", 25.15)
    ]
    
    print("🧪 Tests d'arrondi suisse (0.05 CHF)")
    print("=" * 40)
    
    all_passed = True
    for input_price, expected in test_cases:
        result = round_to_nearest_0_05(input_price)
        passed = abs(result - expected) < 0.001  # Tolérance pour float
        
        status = "✅" if passed else "❌"
        print(f"{status} {input_price} → {result:.2f} (attendu: {expected:.2f})")
        
        if not passed:
            all_passed = False
    
    print(f"\n{'🎉 Tous les tests passés!' if all_passed else '⚠️ Certains tests ont échoué'}")
    
    # Tests de calcul de prix avec barème
    print(f"\n🧪 Tests calcul prix avec barème")
    print("=" * 40)
    
    distance_tests = [
        (10, 7.50),    # 10 * 0.75 = 7.50
        (24, 18.00),   # 24 * 0.75 = 18.00
        (30, 21.00),   # 24*0.75 + 6*0.50 = 18+3 = 21.00
        (50, 26.50),   # 24*0.75 + 16*0.50 + 10*0.25 = 18+8+2.5 = 28.50 → 28.50
    ]
    
    for distance, expected in distance_tests:
        result = calculate_trip_price_swiss(distance)
        print(f"🛣️ {distance} km → {result:.2f} CHF")
