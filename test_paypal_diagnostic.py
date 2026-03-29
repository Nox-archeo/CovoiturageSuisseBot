#!/usr/bin/env python3
"""
Test diagnostic PayPal pour identifier la cause de l'erreur 403
"""

import os
import sys
sys.path.append('.')

from paypal_utils import PayPalManager
from dotenv import load_dotenv

def test_paypal_payout():
    """Teste un payout PayPal vers l'email de Margaux"""
    
    load_dotenv()
    
    print("🔍 DIAGNOSTIC PAYPAL PAYOUT")
    print("=" * 50)
    
    # Initialiser PayPal
    paypal = PayPalManager()
    
    print(f"Mode PayPal: {paypal.mode}")
    print(f"Base URL: {paypal.base_url}")
    
    # Tester le token
    token = paypal.get_access_token()
    if not token:
        print("❌ ERREUR: Impossible d'obtenir le token PayPal")
        return
    
    print("✅ Token PayPal obtenu")
    
    # Test payout vers Margaux
    driver_email = "dekerdrelmargaux@gmail.com"
    test_amount = 0.88
    description = "Test paiement conducteur - Diagnostic"
    
    print(f"\n🏦 TEST PAYOUT:")
    print(f"Email destinataire: {driver_email}")
    print(f"Montant: {test_amount} CHF")
    
    try:
        success, result = paypal.payout_to_driver(
            driver_email=driver_email,
            amount=test_amount,
            trip_description=description
        )
        
        if success:
            print("✅ PAYOUT RÉUSSI!")
            print(f"Batch ID: {result.get('batch_id')}")
            print("Le problème était temporaire ou résolu.")
        else:
            print("❌ PAYOUT ÉCHOUÉ")
            print("Cause probable:")
            print("1. Email dekerdrelmargaux@gmail.com n'a pas de compte PayPal")
            print("2. Ton app PayPal n'a pas la permission 'Payouts'")
            print("3. Restrictions sur ton compte business")
            
    except Exception as e:
        print(f"❌ ERREUR TECHNIQUE: {e}")

if __name__ == "__main__":
    test_paypal_payout()