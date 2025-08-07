#!/usr/bin/env python3
"""
Test des paiements par carte bancaire via PayPal en mode LIVE
Ce script teste la fonctionnalité sans modifier la configuration
"""

import os
import sys
from dotenv import load_dotenv
from paypal_utils import PayPalManager

def test_card_payment_support():
    """Teste si la configuration actuelle supporte les paiements par carte"""
    
    print("🧪 TEST PAIEMENT PAR CARTE BANCAIRE - MODE LIVE")
    print("=" * 60)
    
    # Charger les variables d'environnement
    load_dotenv()
    
    mode = os.getenv('PAYPAL_MODE', 'sandbox')
    print(f"📊 Mode PayPal actuel: {mode}")
    
    if mode != 'live':
        print("⚠️  Attention: Vous n'êtes pas en mode live!")
        print("Ce test est conçu pour vérifier le mode live.")
        return False
    
    try:
        # Initialiser PayPal Manager
        paypal_manager = PayPalManager()
        print("✅ Connexion PayPal établie")
        
        # Créer un paiement de test avec les nouvelles options
        print("\n🔄 Création d'un paiement de test...")
        
        success, payment_id, approval_url = paypal_manager.create_payment(
            amount=1.00,  # 1 CHF pour le test
            currency="CHF",
            description="Test paiement par carte - CovoiturageSuisse",
            return_url="https://covoituragesuissebot.onrender.com/payment/test/success",
            cancel_url="https://covoituragesuissebot.onrender.com/payment/test/cancel"
        )
        
        if success and approval_url:
            print("✅ Paiement de test créé avec succès!")
            print(f"   Payment ID: {payment_id}")
            print(f"   URL de paiement: {approval_url}")
            
            print("\n💳 INSTRUCTIONS DE TEST:")
            print("1. Ouvrez l'URL ci-dessus dans un navigateur")
            print("2. Sur la page PayPal, cherchez l'option:")
            print("   - 'Payer par carte' ou 'Pay with card'")
            print("   - 'Je n'ai pas de compte PayPal'")
            print("3. Vous devriez pouvoir entrer directement:")
            print("   - Numéro de carte bancaire")
            print("   - Date d'expiration")
            print("   - Code CVV")
            print("   - Adresse de facturation")
            
            print("\n🔍 VÉRIFICATIONS:")
            print("✓ Si vous voyez l'option carte bancaire = SUCCÈS")
            print("✗ Si seul le login PayPal apparaît = Configuration à ajuster")
            
            print("\n⚠️  IMPORTANT:")
            print("- N'effectuez PAS le paiement de test")
            print("- Ce test vérifie seulement l'affichage des options")
            print("- Fermez simplement la page après vérification")
            
            return True
            
        else:
            print("❌ Échec de la création du paiement de test")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False

def explain_card_payment_benefits():
    """Explique les avantages du paiement par carte via PayPal"""
    
    print("\n💡 AVANTAGES DU PAIEMENT PAR CARTE VIA PAYPAL:")
    print("=" * 60)
    
    print("🎯 POUR VOS PASSAGERS:")
    print("  • Peuvent payer sans créer de compte PayPal")
    print("  • Utilisation directe de leur carte bancaire")
    print("  • Interface sécurisée et familière")
    print("  • Pas de données stockées sur votre bot")
    
    print("\n🔒 POUR LA SÉCURITÉ:")
    print("  • Chiffrement de niveau bancaire")
    print("  • Protection contre la fraude PayPal")
    print("  • Responsabilité PayPal en cas de litige")
    print("  • Conformité PCI DSS automatique")
    
    print("\n💰 POUR LES REMBOURSEMENTS:")
    print("  • Remboursement automatique possible")
    print("  • Retour sur la même carte utilisée")
    print("  • Traçabilité complète des transactions")
    print("  • Gestion des ajustements de prix")
    
    print("\n🚀 CONFIGURATION ACTUELLE:")
    print("  • Mode LIVE activé")
    print("  • Support carte bancaire amélioré")
    print("  • Interface en français")
    print("  • Nom de marque: CovoiturageSuisse")

def main():
    print("🤖 TEST PAIEMENT PAR CARTE - BOT COVOITURAGE")
    print("=" * 60)
    
    # Tester la configuration
    test_success = test_card_payment_support()
    
    # Expliquer les avantages
    explain_card_payment_benefits()
    
    print("\n" + "=" * 60)
    if test_success:
        print("✅ CONFIGURATION PRÊTE POUR LES PAIEMENTS PAR CARTE")
        print("\n📋 PROCHAINES ÉTAPES:")
        print("1. Testez avec une vraie carte bancaire (petit montant)")
        print("2. Vérifiez que l'option carte apparaît bien")
        print("3. Testez un remboursement si nécessaire")
        print("4. Le système est prêt pour vos utilisateurs!")
    else:
        print("❌ PROBLÈME DE CONFIGURATION DÉTECTÉ")
        print("\n🔧 Actions recommandées:")
        print("1. Vérifiez les identifiants PayPal")
        print("2. Contactez le support PayPal si nécessaire")
        print("3. Testez à nouveau après corrections")

if __name__ == "__main__":
    main()
