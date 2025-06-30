#!/usr/bin/env python
"""
Script de test pour vérifier l'intégration des modules de paiement PayPal
"""

import os
import sys
import logging
from pathlib import Path

# Ajouter le répertoire racine au chemin Python
sys.path.insert(0, str(Path(__file__).parent))

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test des imports des modules de paiement"""
    print("🔄 Test des imports...")
    
    try:
        from payment_handlers import get_payment_handlers
        print("✅ payment_handlers importé avec succès")
        
        from db_utils import init_payment_database, calculate_payment_split
        print("✅ db_utils importé avec succès")
        
        from paypal_utils import paypal_manager
        print("✅ paypal_utils importé avec succès")
        
        return True
    except Exception as e:
        print(f"❌ Erreur d'import : {e}")
        return False

def test_database_initialization():
    """Test de l'initialisation de la base de données"""
    print("\n🔄 Test de l'initialisation de la base de données...")
    
    try:
        from db_utils import init_payment_database
        
        if init_payment_database():
            print("✅ Base de données initialisée avec succès")
            return True
        else:
            print("❌ Erreur lors de l'initialisation de la base de données")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        return False

def test_payment_calculations():
    """Test des calculs de paiement"""
    print("\n🔄 Test des calculs de paiement...")
    
    try:
        from db_utils import calculate_payment_split
        
        # Test avec 100 CHF
        test_amount = 100.0
        split = calculate_payment_split(test_amount)
        
        expected_driver = 88.0
        expected_commission = 12.0
        
        if (split['driver_amount'] == expected_driver and 
            split['commission_amount'] == expected_commission):
            print(f"✅ Calcul correct pour {test_amount} CHF :")
            print(f"   - Conducteur : {split['driver_amount']} CHF ({split['driver_percentage']}%)")
            print(f"   - Commission : {split['commission_amount']} CHF ({split['commission_percentage']}%)")
            return True
        else:
            print(f"❌ Calcul incorrect :")
            print(f"   - Attendu : conducteur {expected_driver}, commission {expected_commission}")
            print(f"   - Obtenu : conducteur {split['driver_amount']}, commission {split['commission_amount']}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de calcul : {e}")
        return False

def test_handlers_registration():
    """Test de l'enregistrement des handlers"""
    print("\n🔄 Test de l'enregistrement des handlers...")
    
    try:
        from payment_handlers import get_payment_handlers
        
        handlers = get_payment_handlers()
        
        conv_handlers = handlers.get('conversation_handlers', [])
        cmd_handlers = handlers.get('command_handlers', [])
        callback_handlers = handlers.get('callback_handlers', [])
        
        print(f"✅ Handlers disponibles :")
        print(f"   - ConversationHandlers : {len(conv_handlers)}")
        print(f"   - CommandHandlers : {len(cmd_handlers)}")
        print(f"   - CallbackQueryHandlers : {len(callback_handlers)}")
        
        # Vérifier qu'il y a au moins quelques handlers
        if len(conv_handlers) > 0 and len(cmd_handlers) > 0:
            print("✅ Handlers correctement configurés")
            return True
        else:
            print("❌ Handlers manquants")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test des handlers : {e}")
        return False

def test_paypal_configuration():
    """Test de la configuration PayPal"""
    print("\n🔄 Test de la configuration PayPal...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        client_id = os.getenv('PAYPAL_CLIENT_ID')
        client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
        mode = os.getenv('PAYPAL_MODE', 'sandbox')
        
        if client_id and client_secret:
            print(f"✅ Configuration PayPal trouvée :")
            print(f"   - Mode : {mode}")
            print(f"   - Client ID : {client_id[:20]}... (tronqué)")
            print(f"   - Client Secret : {client_secret[:20]}... (tronqué)")
            return True
        else:
            print("❌ Configuration PayPal manquante dans .env")
            print("   Vérifiez PAYPAL_CLIENT_ID et PAYPAL_CLIENT_SECRET")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de configuration PayPal : {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test d'intégration des modules de paiement PayPal")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_paypal_configuration,
        test_database_initialization,
        test_payment_calculations,
        test_handlers_registration
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 Résultats des tests :")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Tous les tests réussis ({passed}/{total})")
        print("\n🎉 L'intégration PayPal est prête !")
        print("\nPour démarrer le bot avec PayPal :")
        print("   python bot.py")
        return True
    else:
        print(f"❌ {total - passed} test(s) échoué(s) sur {total}")
        print("\n⚠️ Veuillez corriger les erreurs avant de démarrer le bot")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
