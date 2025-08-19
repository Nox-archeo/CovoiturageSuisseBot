#!/usr/bin/env python3
"""
Test direct du webhook avec la réservation #19
"""

import requests
import json
from datetime import datetime

def test_webhook_direct():
    """
    Teste directement le webhook avec les données réelles de la réservation #19
    """
    
    # Données exactes du webhook PayPal reçu
    real_webhook_data = {
        "id": "WH-46301466SD872372W-4WF51828323430829",
        "create_time": "2025-08-19T13:14:08.991Z",
        "resource_type": "capture", 
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "summary": "Payment completed for CHF 1.0 CHF",
        "resource": {
            "payee": {
                "email_address": "seb.chappss@gmail.com",
                "merchant_id": "RFFKMXVTU2K96"
            },
            "amount": {
                "currency_code": "CHF",
                "value": "1.00"
            },
            "seller_protection": {
                "status": "ELIGIBLE",
                "dispute_categories": ["UNAUTHORIZED_TRANSACTION"]
            },
            "supplementary_data": {
                "related_ids": {
                    "order_id": "26M12520H00877458"
                }
            },
            "update_time": "2025-08-19T13:14:05Z",
            "create_time": "2025-08-19T13:14:05Z",
            "final_capture": True,
            "seller_receivable_breakdown": {
                "gross_amount": {"currency_code": "CHF", "value": "1.00"},
                "paypal_fee": {"currency_code": "CHF", "value": "0.58"},
                "net_amount": {"currency_code": "CHF", "value": "0.42"}
            },
            "custom_id": "19",  # 🔥 ID de la réservation #19
            "links": [
                {
                    "href": "https://api.paypal.com/v2/payments/captures/1RL815500Y492972W",
                    "rel": "self",
                    "method": "GET"
                }
            ],
            "id": "1RL815500Y492972W",
            "status": "COMPLETED"
        },
        "status": "SUCCESS"
    }
    
    print("🔥 TEST WEBHOOK DIRECT - RÉSERVATION #19")
    print("=" * 50)
    print(f"📅 Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    print(f"💳 Payment ID: {real_webhook_data['resource']['id']}")
    print(f"🎫 Custom ID: {real_webhook_data['resource']['custom_id']}")
    print(f"💰 Montant: {real_webhook_data['resource']['amount']['value']} CHF")
    
    # Test 1: Webhook endpoint principal
    print(f"\n🎯 TEST 1: Webhook principal")
    try:
        response = requests.post(
            "https://covoituragesuissebot.onrender.com/paypal/webhook",
            json=real_webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Webhook accepté")
        else:
            print("   ❌ Webhook rejeté")
            
    except Exception as e:
        print(f"   ❌ Erreur webhook: {e}")
    
    # Test 2: Endpoint de debug (si existe)
    print(f"\n🎯 TEST 2: Debug endpoint")
    try:
        response = requests.post(
            "https://covoituragesuissebot.onrender.com/debug/webhook/test",
            json=real_webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
    except Exception as e:
        print(f"   ❌ Debug endpoint indisponible: {e}")
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"   🎯 Réservation testée: #19")
    print(f"   📡 Webhook URL: /paypal/webhook")
    print(f"   🔍 Si aucune notification → Problème base PostgreSQL production")

if __name__ == "__main__":
    test_webhook_direct()
