#!/usr/bin/env python3
"""
Test de validation du custom_id dans PayPal
Vérifie que les paiements incluent maintenant l'ID de réservation
"""

import json
from paypal_utils import PayPalManager

def test_custom_id_inclusion():
    """Test que le custom_id est bien inclus dans le payload PayPal"""
    
    print("🔥 TEST CUSTOM_ID PAYPAL - VALIDATION CRITIQUE")
    print("=" * 60)
    
    try:
        # Initialiser PayPal Manager
        paypal_manager = PayPalManager()
        print("✅ PayPal Manager initialisé")
        
        # Test avec custom_id
        test_custom_id = "999"  # ID de test
        
        print(f"\n📝 Test avec custom_id: {test_custom_id}")
        
        # Créer un paiement de test (ne sera pas exécuté, juste validé)
        success, order_id, approval_url = paypal_manager.create_payment(
            amount=1.0,
            currency="CHF",
            description="Test custom_id validation",
            custom_id=test_custom_id
        )
        
        if success and order_id:
            print(f"✅ Paiement créé avec succès:")
            print(f"   Order ID: {order_id}")
            print(f"   Custom ID envoyé: {test_custom_id}")
            print(f"   Approval URL: {approval_url[:50]}...")
            
            # Vérifier que l'ordre contient le custom_id
            success_check, order_details = paypal_manager.find_payment(order_id)
            
            if success_check and order_details:
                purchase_units = order_details.get('purchase_units', [])
                if purchase_units:
                    custom_id_received = purchase_units[0].get('custom_id')
                    
                    if custom_id_received == test_custom_id:
                        print(f"✅ VALIDATION RÉUSSIE: custom_id présent dans l'ordre PayPal")
                        print(f"   Custom ID reçu: {custom_id_received}")
                        return True
                    else:
                        print(f"❌ ERREUR: custom_id manquant ou incorrect")
                        print(f"   Attendu: {test_custom_id}")
                        print(f"   Reçu: {custom_id_received}")
                        return False
                else:
                    print("❌ ERREUR: Aucun purchase_unit trouvé")
                    return False
            else:
                print("❌ ERREUR: Impossible de vérifier l'ordre créé")
                return False
        else:
            print("❌ ERREUR: Échec de création du paiement")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        return False

def test_old_payment_without_custom_id():
    """Test d'un paiement sans custom_id pour comparaison"""
    
    print("\n🔍 TEST COMPARAISON - Paiement SANS custom_id")
    print("-" * 50)
    
    try:
        paypal_manager = PayPalManager()
        
        # Créer un paiement SANS custom_id
        success, order_id, approval_url = paypal_manager.create_payment(
            amount=1.0,
            currency="CHF",
            description="Test sans custom_id"
            # Pas de custom_id passé
        )
        
        if success and order_id:
            print(f"✅ Paiement sans custom_id créé:")
            print(f"   Order ID: {order_id}")
            
            # Vérifier l'absence de custom_id
            success_check, order_details = paypal_manager.find_payment(order_id)
            
            if success_check and order_details:
                purchase_units = order_details.get('purchase_units', [])
                if purchase_units:
                    custom_id_received = purchase_units[0].get('custom_id')
                    
                    if custom_id_received is None:
                        print(f"✅ CONFIRMATION: Pas de custom_id (comme attendu)")
                        return True
                    else:
                        print(f"⚠️  INATTENDU: custom_id présent alors que non envoyé: {custom_id_received}")
                        return False
        else:
            print("❌ ERREUR: Échec de création du paiement test")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 VALIDATION CORRECTIFS PAYPAL CUSTOM_ID")
    print("=" * 60)
    
    # Test 1: Avec custom_id
    test1_passed = test_custom_id_inclusion()
    
    # Test 2: Sans custom_id (comparaison)
    test2_passed = test_old_payment_without_custom_id()
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS:")
    print(f"   ✅ Test avec custom_id: {'RÉUSSI' if test1_passed else 'ÉCHOUÉ'}")
    print(f"   ✅ Test sans custom_id: {'RÉUSSI' if test2_passed else 'ÉCHOUÉ'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("   ✅ Le custom_id est maintenant correctement inclus")
        print("   ✅ Le système peut identifier les réservations dans les webhooks")
        print("\n🔥 PRÊT POUR DÉPLOIEMENT!")
    else:
        print("\n❌ TESTS ÉCHOUÉS - CORRECTIFS NÉCESSAIRES")
        print("   Le système ne fonctionnera pas correctement")
