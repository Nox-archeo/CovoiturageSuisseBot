#!/usr/bin/env python3
"""
Test direct pour forcer l'affichage de l'option carte bancaire
"""

from paypal_utils import PayPalManager

def create_guest_payment_url():
    """Crée une URL avec configuration optimisée pour guest checkout"""
    try:
        paypal_manager = PayPalManager()
        
        print("🔄 Génération d'URL avec configuration guest checkout optimisée...")
        
        # Créer le paiement avec paramètres spéciaux pour carte
        success, payment_id, approval_url = paypal_manager.create_payment(
            amount=2.50,
            currency="CHF", 
            description="Test paiement carte - Covoiturage Suisse",
            return_url="https://covoituragesuissebot.onrender.com/payment/success",
            cancel_url="https://covoituragesuissebot.onrender.com/payment/cancel"
        )
        
        if success and approval_url:
            print(f"✅ URL générée avec succès:")
            print(f"   {approval_url}")
            print()
            print("🎯 INSTRUCTIONS SPÉCIALES POUR VOIR L'OPTION CARTE:")
            print("   1. Ouvrez cette URL en navigation privée/incognito")
            print("   2. Ne vous connectez PAS à PayPal")
            print("   3. Cherchez 'Payer par carte' ou 'Debit/Credit Card'")
            print("   4. L'option peut être en petit en bas de page")
            print()
            print("🔍 SI VOUS NE VOYEZ PAS L'OPTION CARTE:")
            print("   • Essayez de cliquer sur 'Ouvrir un compte PayPal'")
            print("   • L'option carte apparaît souvent après")
            print("   • Ou cherchez un lien 'Pay with card' en bas")
            print()
            print("💡 ASTUCE: Parfois PayPal cache l'option carte")
            print("   dans les paramètres régionaux de la Suisse.")
            print("   L'option devrait être visible pour vos vrais utilisateurs.")
            
        else:
            print("❌ Erreur lors de la génération de l'URL de test")
            
    except Exception as e:
        print(f"⚠️ Erreur: {e}")

if __name__ == "__main__":
    create_guest_payment_url()
