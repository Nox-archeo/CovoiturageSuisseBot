#!/usr/bin/env python3
"""
Test du webhook PayPal avec les nouvelles fonctions
"""

import asyncio
import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from paypal_webhook_handler import handle_paypal_webhook, handle_payment_completion

async def test_webhook_processing():
    """Test du traitement des webhooks PayPal"""
    print("🧪 Test du traitement des webhooks PayPal")
    
    # Test 1: Webhook avec custom_id
    webhook_data_1 = {
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "test_payment_123",
            "custom_id": "1",  # ID de la réservation existante
            "amount": {"value": "15.00", "currency_code": "CHF"}
        }
    }
    
    print(f"\n1️⃣ Test webhook avec custom_id=1 (réservation existante)")
    result1 = await handle_paypal_webhook(webhook_data_1, bot=None)
    print(f"   Résultat: {'✅ Succès' if result1 else '❌ Échec'}")
    
    # Test 2: Webhook sans custom_id mais avec payment_id
    webhook_data_2 = {
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "test_payment_456",
            "amount": {"value": "20.00", "currency_code": "CHF"}
        }
    }
    
    print(f"\n2️⃣ Test webhook sans custom_id")
    result2 = await handle_paypal_webhook(webhook_data_2, bot=None)
    print(f"   Résultat: {'✅ Succès' if result2 else '❌ Échec'}")
    
    # Test 3: Test direct de handle_payment_completion
    print(f"\n3️⃣ Test direct handle_payment_completion")
    result3 = await handle_payment_completion("test_payment_direct", bot=None)
    print(f"   Résultat: {'✅ Succès' if result3 else '❌ Échec'}")

if __name__ == "__main__":
    asyncio.run(test_webhook_processing())
