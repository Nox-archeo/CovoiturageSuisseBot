#!/usr/bin/env python3
"""
Teste la création d'un paiement PayPal pour vérifier que le système fonctionne
"""

import sys
import os
import logging

# Configuration du chemin
sys.path.append('/Users/margaux/CovoiturageSuisse')

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_payment_creation():
    """Test la création d'un paiement PayPal"""
    try:
        from paypal_utils import paypal_manager
        
        print("🔄 Test de création de paiement PayPal...")
        print(f"💰 Montant: 1.0 CHF")
        print(f"📝 Description: Test paiement covoiturage")
        
        # Créer un paiement de test
        success, order_id, approval_url = paypal_manager.create_payment(
            amount=1.0,
            currency="CHF",
            description="Test paiement covoiturage - Trajet Lausanne-Genève",
            custom_id="test_booking_1"
        )
        
        if success:
            print("✅ Paiement créé avec succès!")
            print(f"🆔 Order ID: {order_id}")
            print(f"🔗 URL d'approbation: {approval_url}")
            print(f"\n💡 Vous pouvez maintenant tester le paiement en visitant cette URL:")
            print(f"{approval_url}")
            return True
        else:
            print("❌ Échec de la création du paiement.")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_payment_creation()
    if result:
        print("\n🎉 Test réussi! Le système de paiement fonctionne.")
    else:
        print("\n💥 Test échoué. Vérifiez la configuration PayPal.")
