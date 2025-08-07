#!/usr/bin/env python3
"""
Script de diagnostic PayPal pour le bot de covoiturage
Vérifie la configuration et teste la connexion PayPal
"""

import os
import sys
from dotenv import load_dotenv
import paypalrestsdk

def check_paypal_config():
    """Vérifie la configuration PayPal"""
    print("🔍 DIAGNOSTIC PAYPAL\n")
    
    # Charger les variables d'environnement
    load_dotenv()
    
    client_id = os.getenv('PAYPAL_CLIENT_ID')
    client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
    webhook_id = os.getenv('PAYPAL_WEBHOOK_ID')
    mode = os.getenv('PAYPAL_MODE', 'sandbox')
    
    print(f"📊 Configuration actuelle:")
    print(f"   Mode: {mode}")
    print(f"   Client ID: {'✅ Configuré' if client_id else '❌ Manquant'}")
    print(f"   Client Secret: {'✅ Configuré' if client_secret else '❌ Manquant'}")
    print(f"   Webhook ID: {'✅ Configuré' if webhook_id else '❌ Manquant'}")
    
    if not client_id or not client_secret:
        print("\n❌ Configuration incomplète!")
        return False
    
    # Tester la connexion PayPal
    print(f"\n🔗 Test de connexion PayPal ({mode})...")
    
    try:
        paypalrestsdk.configure({
            "mode": mode,
            "client_id": client_id,
            "client_secret": client_secret
        })
        
        # Créer un paiement de test
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Test Covoiturage",
                        "sku": "test",
                        "price": "10.00",
                        "currency": "CHF",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": "10.00",
                    "currency": "CHF"
                },
                "description": "Test de connexion PayPal"
            }]
        })
        
        if payment.create():
            print("✅ Connexion PayPal réussie!")
            print(f"   Payment ID de test: {payment.id}")
            
            # Obtenir l'URL d'approbation
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            
            if approval_url:
                print(f"   URL de test générée: ✅")
                print(f"   URL: {approval_url[:50]}...")
            else:
                print("   ❌ Impossible de générer l'URL d'approbation")
            
            return True
        else:
            print(f"❌ Erreur lors de la création du paiement test:")
            print(f"   {payment.error}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion PayPal: {str(e)}")
        return False

def check_account_conflict():
    """Vérifie les conflits de compte"""
    print(f"\n🔒 DIAGNOSTIC DES CONFLITS DE COMPTE:")
    
    mode = os.getenv('PAYPAL_MODE', 'sandbox')
    
    if mode == 'live':
        print("⚠️  VOUS ÊTES EN MODE LIVE (PRODUCTION)")
        print("\n❌ PROBLÈME IDENTIFIÉ:")
        print("   Vous ne pouvez pas utiliser le même compte PayPal que")
        print("   celui configuré pour l'application (le vendeur).")
        print("\n💡 SOLUTIONS:")
        print("   1. Utiliser un autre compte PayPal pour tester")
        print("   2. Passer en mode sandbox pour les tests:")
        print("      python switch_paypal_mode.py sandbox")
        print("   3. Demander à quelqu'un d'autre de tester le paiement")
        
    else:
        print("✅ Mode sandbox - Bon pour les tests")
        print("💡 En mode sandbox, vous devez utiliser:")
        print("   - Des comptes de test PayPal")
        print("   - https://developer.paypal.com/developer/accounts/")

def main():
    print("🤖 DIAGNOSTIC PAYPAL - BOT COVOITURAGE")
    print("=" * 50)
    
    config_ok = check_paypal_config()
    check_account_conflict()
    
    print("\n" + "=" * 50)
    if config_ok:
        print("✅ Configuration PayPal fonctionnelle")
    else:
        print("❌ Problèmes de configuration détectés")
    
    print("\n📋 ACTIONS RECOMMANDÉES:")
    mode = os.getenv('PAYPAL_MODE', 'sandbox')
    if mode == 'live':
        print("   1. Utiliser un compte PayPal différent pour tester")
        print("   2. OU passer en mode sandbox: python switch_paypal_mode.py sandbox")
    else:
        print("   1. Créer des comptes de test sur PayPal Developer")
        print("   2. Utiliser ces comptes pour tester les paiements")
    
    print("   3. Redémarrer le bot après tout changement")

if __name__ == "__main__":
    main()
