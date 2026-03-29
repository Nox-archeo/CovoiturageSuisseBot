#!/usr/bin/env python3
"""
Test de vérification des comptes PayPal pour identifier le problème 403
"""
import asyncio
import os
from paypal_utils import PayPalManager
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_paypal_account_verification():
    """
    Teste différents aspects de la configuration PayPal
    """
    try:
        # 1. Initialiser PayPal
        paypal = PayPalManager()
        logger.info("✅ PayPal Manager initialisé")
        
        # 2. Vérifier les credentials
        logger.info("🔍 Test 1: Vérification des credentials...")
        
        # Tenter d'obtenir un token d'accès
        try:
            access_token = paypal.get_access_token()  # Pas async
            if access_token:
                logger.info("✅ Token d'accès obtenu avec succès")
            else:
                logger.error("❌ Impossible d'obtenir le token d'accès")
                return
        except Exception as e:
            logger.error(f"❌ Erreur obtention token: {e}")
            return
        
        # 3. Test des différentes adresses email
        test_emails = [
            "dekerdrelmargaux@gmail.com",  # Email cible du conducteur
            "seb.chappss@gmail.com",       # Email business account
            "sebastienchappuis@yahoo.fr"   # Email passager
        ]
        
        logger.info("🔍 Test 2: Tentative de paiement vers différentes adresses...")
        
        for email in test_emails:
            logger.info(f"\n📧 Test paiement vers: {email}")
            
            success, result = paypal.payout_to_driver(
                driver_email=email,
                amount=0.01,  # Montant minimum pour test
                trip_description="Test - Verification compte"
            )
            
            if success:
                logger.info(f"✅ {email}: Paiement réussi - {result}")
            else:
                logger.error(f"❌ {email}: Paiement échoué - {result}")
        
        # 4. Vérifier les permissions de l'app
        logger.info("\n🔍 Test 3: Vérification des permissions...")
        
        # Tester avec une adresse email sandbox connue
        sandbox_email = "sb-sender@personal.example.com"  # Email sandbox type
        
        success, result = paypal.payout_to_driver(
            driver_email=sandbox_email,
            amount=0.01,
            trip_description="Test - Permissions PayPal"
        )
        
        if success:
            logger.info(f"✅ Sandbox test: Permissions OK")
        else:
            logger.error(f"❌ Sandbox test: Problème permissions - {result}")
        
        # 5. Information sur l'environnement
        logger.info(f"\n📋 Informations environnement:")
        logger.info(f"   Mode: {'LIVE' if os.getenv('PAYPAL_MODE', 'sandbox') == 'live' else 'SANDBOX'}")
        logger.info(f"   Client ID: {os.getenv('PAYPAL_CLIENT_ID', 'NON_DEFINI')[:10]}...")
        logger.info(f"   Base URL: {paypal.base_url}")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_paypal_account_verification())