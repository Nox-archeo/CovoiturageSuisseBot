#!/usr/bin/env python3
"""
Diagnostic des réservations PRODUCTION via API bot
"""

import requests
import json

def check_production_webhook():
    """Vérifier les endpoints de production"""
    
    print("🔍 DIAGNOSTIC PRODUCTION")
    print("=" * 40)
    
    base_url = "https://covoituragesuissebot.onrender.com"
    
    # 1. Vérifier le statut du service
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"📊 Status service: {response.json()}")
    except Exception as e:
        print(f"❌ Erreur health check: {e}")
        return
    
    # 2. Vérifier les logs récents (si endpoint existe)
    try:
        response = requests.get(f"{base_url}/debug/logs", timeout=10)
        if response.status_code == 200:
            print(f"📋 Logs récents disponibles")
        else:
            print(f"📋 Logs endpoint: {response.status_code}")
    except Exception as e:
        print(f"📋 Pas de logs endpoint")
    
    # 3. Test webhook PayPal (simulation)
    print(f"\n🎯 Test webhook PayPal...")
    
    # Simuler un webhook PayPal pour voir si ça fonctionne
    test_webhook_data = {
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "test_payment_123",
            "custom_id": "18",  # Votre réservation
            "amount": {
                "value": "1.00"
            }
        }
    }
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{base_url}/paypal/webhook",  # CORRECTION: Bonne route 
            json=test_webhook_data,
            headers=headers,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Webhook PayPal opérationnel")
        else:
            print(f"   ❌ Webhook PayPal problème: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Erreur webhook test: {e}")

if __name__ == "__main__":
    check_production_webhook()
