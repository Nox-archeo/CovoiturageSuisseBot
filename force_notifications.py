#!/usr/bin/env python3
"""
FORCE LES NOTIFICATIONS pour le paiement de Margaux
Simule le webhook PayPal avec les vraies données
"""

import requests
import json

def force_notifications():
    """Force les notifications pour le paiement réel"""
    
    print("🚨 FORCE NOTIFICATIONS PAIEMENT MARGAUX")
    print("=" * 50)
    
    base_url = "https://covoituragesuissebot.onrender.com"
    
    # Données du vrai paiement de Margaux
    # Réservation #18, trajet Corpataux → Posieux, 1 CHF
    real_webhook_data = {
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "REAL_PAYMENT_MARGAUX_001",  # ID unique pour identifier
            "custom_id": "18",  # Votre réservation #18
            "amount": {
                "value": "1.00",
                "currency_code": "CHF"
            },
            "status": "COMPLETED",
            "create_time": "2025-08-19T11:55:00Z"
        },
        "create_time": "2025-08-19T11:55:00Z",
        "event_version": "1.0",
        "resource_type": "capture"
    }
    
    print("📤 Envoi webhook PayPal RÉEL...")
    print(f"   Réservation: #{real_webhook_data['resource']['custom_id']}")
    print(f"   Montant: {real_webhook_data['resource']['amount']['value']} CHF")
    
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "PayPal/1.0"
        }
        
        response = requests.post(
            f"{base_url}/paypal/webhook",
            json=real_webhook_data,
            headers=headers,
            timeout=15
        )
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ WEBHOOK PAYPAL ENVOYÉ AVEC SUCCÈS")
            print("📱 Les notifications devraient arriver maintenant!")
        else:
            print(f"❌ Erreur webhook: {response.status_code}")
            print(f"   Détails: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur requête: {e}")
    
    print(f"\n🎯 Vérifiez maintenant vos notifications Telegram!")

if __name__ == "__main__":
    force_notifications()
