#!/usr/bin/env python3
"""
Test webhook réservation #21 avec logs détaillés
"""

import requests
import json
from datetime import datetime

def test_webhook_reservation_21():
    """
    Test avec les données exactes de la réservation #21
    """
    
    # Données basées sur les logs
    webhook_data_21 = {
        "id": "WH-TEST-21",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "2HX66173FR1950545",  # Capture ID du webhook
            "custom_id": "21",  # Réservation #21
            "amount": {"value": "1.00"},
            "status": "COMPLETED",
            "paypal_order_id": "0KL24916WA9329923"  # Order ID stocké en DB
        }
    }
    
    print("🔥 TEST WEBHOOK RÉSERVATION #21")
    print("=" * 50)
    print(f"📅 Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    print(f"💳 Capture ID: {webhook_data_21['resource']['id']}")
    print(f"🎫 Custom ID: {webhook_data_21['resource']['custom_id']}")
    print(f"💰 Montant: {webhook_data_21['resource']['amount']['value']} CHF")
    print(f"📦 Order ID: {webhook_data_21['resource'].get('paypal_order_id', 'N/A')}")
    
    # Test webhook
    try:
        response = requests.post(
            "https://covoituragesuissebot.onrender.com/paypal/webhook",
            json=webhook_data_21,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n🎯 RÉSULTAT WEBHOOK:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Webhook accepté")
        else:
            print("   ❌ Webhook rejeté")
            
    except Exception as e:
        print(f"   ❌ Erreur webhook: {e}")

if __name__ == "__main__":
    test_webhook_reservation_21()
