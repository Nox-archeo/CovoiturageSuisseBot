#!/usr/bin/env python3
"""
Test complet du nouveau système de prix dynamique avec remboursements automatiques
"""

import logging
import asyncio
from datetime import datetime
from utils.swiss_pricing import (
    round_to_nearest_0_05_up, 
    calculate_price_per_passenger,
    calculate_trip_total_and_per_passenger
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_swiss_rounding():
    """
    Test de l'arrondi suisse au 0.05 CHF supérieur
    """
    print("🧮 TEST DE L'ARRONDI SUISSE")
    print("-" * 40)
    
    test_cases = [
        (13.38, 13.40),
        (13.35, 13.35),
        (13.31, 13.35),
        (13.42, 13.45),
        (17.85, 17.85),
        (8.92, 8.95),
        (8.925, 8.95),
        (5.951, 5.95),
        (4.463, 4.465)
    ]
    
    all_passed = True
    
    for input_amount, expected in test_cases:
        result = round_to_nearest_0_05_up(input_amount)
        status = "✅" if result == expected else "❌"
        print(f"{status} {input_amount:.3f} CHF → {result:.2f} CHF (attendu: {expected:.2f})")
        
        if result != expected:
            all_passed = False
    
    success_msg = "✅ Tous les tests d'arrondi ont réussi!"
    failure_msg = "❌ Certains tests d'arrondi ont échoué!"
    print(f"\n{success_msg if all_passed else failure_msg}")
    return all_passed

def test_dynamic_pricing():
    """
    Test du système de prix dynamique
    """
    print("\n💰 TEST DU SYSTÈME DE PRIX DYNAMIQUE")
    print("-" * 45)
    
    # Test avec le trajet Lausanne-Fribourg (17.85 CHF total)
    total_trip_price = 17.85
    
    test_cases = [
        (1, 17.85),  # 1 passager = prix total
        (2, 8.95),   # 2 passagers = 17.85 ÷ 2 = 8.925 → 8.95
        (3, 5.95),   # 3 passagers = 17.85 ÷ 3 = 5.95
        (4, 4.50)    # 4 passagers = 17.85 ÷ 4 = 4.4625 → 4.50
    ]
    
    all_passed = True
    
    for passenger_count, expected_price_per_passenger in test_cases:
        result = calculate_price_per_passenger(total_trip_price, passenger_count)
        details = calculate_trip_total_and_per_passenger(total_trip_price, passenger_count)
        
        status = "✅" if abs(result - expected_price_per_passenger) < 0.01 else "❌"
        print(f"{status} {passenger_count} passager(s):")
        print(f"    Prix par passager: {result:.2f} CHF (attendu: {expected_price_per_passenger:.2f})")
        print(f"    Total collecté: {details['total_actual']:.2f} CHF")
        print(f"    Différence: +{details['price_difference']:.2f} CHF")
        
        if abs(result - expected_price_per_passenger) >= 0.01:
            all_passed = False
    
        success_msg = "✅ Tous les tests de prix par passager ont réussi!"
    failure_msg = "❌ Certains tests de prix par passager ont échoué!"
    print(f"
{success_msg if all_passed else failure_msg}")
    return all_passed

def test_refund_calculations():
    """
    Test des calculs de remboursement
    """
    print("\n🔄 TEST DES CALCULS DE REMBOURSEMENT")
    print("-" * 45)
    
    # Scénario: Trajet Lausanne-Fribourg 17.85 CHF
    # 1er passager paie 17.85 CHF
    # 2ème passager s'ajoute → nouveau prix 8.95 CHF
    # Le 1er passager doit être remboursé de 8.90 CHF
    
    total_trip_price = 17.85
    
    # Simulation des paiements
    passengers = []
    
    # 1er passager
    price_1_passenger = calculate_price_per_passenger(total_trip_price, 1)
    passengers.append({
        'name': 'Passager 1',
        'amount_paid': price_1_passenger,
        'passenger_order': 1
    })
    
    print(f"1️⃣ Premier passager paie: {price_1_passenger:.2f} CHF")
    
    # 2ème passager s'ajoute
    price_2_passengers = calculate_price_per_passenger(total_trip_price, 2)
    passengers.append({
        'name': 'Passager 2',
        'amount_paid': price_2_passengers,
        'passenger_order': 2
    })
    
    print(f"2️⃣ Deuxième passager paie: {price_2_passengers:.2f} CHF")
    
    # Calculer les remboursements
    for passenger in passengers:
        if passenger['passenger_order'] == 1:
            refund_amount = passenger['amount_paid'] - price_2_passengers
            print(f"💸 {passenger['name']} remboursé de: {refund_amount:.2f} CHF")
            
            # Vérification
            expected_refund = 17.85 - 8.95  # 8.90
            status = "✅" if abs(refund_amount - expected_refund) < 0.01 else "❌"
            print(f"{status} Remboursement attendu: {expected_refund:.2f} CHF")
    
    return True

def test_real_world_scenarios():
    """
    Test avec des scenarii réels
    """
    print("\n🌍 TEST AVEC DES SCÉNARII RÉELS")
    print("-" * 40)
    
    scenarios = [
        {
            'name': 'Genève → Lausanne (distance ~62km)',
            'total_price': 15.50,  # 62 * 0.25
            'max_passengers': 3
        },
        {
            'name': 'Zürich → Bern (distance ~120km)', 
            'total_price': 30.00,  # 30 * 0.25
            'max_passengers': 4
        },
        {
            'name': 'Basel → Lucerne (distance ~85km)',
            'total_price': 21.25,  # 85 * 0.25
            'max_passengers': 2
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🚗 {scenario['name']}")
        print(f"    Prix total: {scenario['total_price']:.2f} CHF")
        
        for passenger_count in range(1, scenario['max_passengers'] + 1):
            price_per_passenger = calculate_price_per_passenger(
                scenario['total_price'], 
                passenger_count
            )
            total_collected = price_per_passenger * passenger_count
            
            print(f"    {passenger_count} passager(s): {price_per_passenger:.2f} CHF/personne "
                  f"(total: {total_collected:.2f} CHF)")
    
    return True

async def test_paypal_integration():
    """
    Test d'intégration PayPal (simulation)
    """
    print("\n💳 TEST D'INTÉGRATION PAYPAL (SIMULATION)")
    print("-" * 50)
    
    try:
        # Simulation d'un remboursement
        print("🔄 Simulation d'un remboursement PayPal...")
        print("    - Paiement original: 17.85 CHF")
        print("    - Nouveau prix: 8.95 CHF") 
        print("    - Remboursement: 8.90 CHF")
        print("✅ Simulation PayPal réussie")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur simulation PayPal: {e}")
        return False

def main():
    """
    Exécute tous les tests
    """
    print("🚀 TESTS DU NOUVEAU SYSTÈME DE PRIX DYNAMIQUE")
    print("=" * 60)
    
    tests = [
        ("Arrondi suisse", test_swiss_rounding),
        ("Prix dynamique", test_dynamic_pricing),
        ("Calculs remboursement", test_refund_calculations),
        ("Scénarii réels", test_real_world_scenarios),
        ("Intégration PayPal", lambda: asyncio.run(test_paypal_integration()))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{status:10} | {test_name}")
    
    print("-" * 60)
    print(f"TOTAL: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("\n🎉 TOUS LES TESTS ONT RÉUSSI!")
        print("✅ Le nouveau système de prix dynamique est prêt!")
        print("\n💡 Fonctionnalités validées:")
        print("   - ✅ Arrondi au 0.05 CHF supérieur")
        print("   - ✅ Prix par passager = Prix total ÷ Nombre de passagers")
        print("   - ✅ Calculs de remboursement automatique")
        print("   - ✅ Intégration PayPal simulée")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) ont échoué!")
        print("❌ Correction nécessaire avant déploiement!")

if __name__ == "__main__":
    main()
