#!/usr/bin/env python3
"""
Script pour forcer le rechargement du module PayPal sur Render
"""
import importlib
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_reload_paypal():
    """Force le rechargement du module paypal_utils"""
    try:
        # Supprimer le module du cache Python si il existe
        if 'paypal_utils' in sys.modules:
            del sys.modules['paypal_utils']
            logger.info("🗑️ Module paypal_utils supprimé du cache")
        
        # Importer à nouveau
        import paypal_utils
        importlib.reload(paypal_utils)
        logger.info("🔄 Module paypal_utils rechargé")
        
        # Tester la classe
        manager = paypal_utils.PayPalManager()
        methods = [method for method in dir(manager) if not method.startswith('_')]
        logger.info(f"✅ Méthodes disponibles: {methods}")
        
        # Vérifier spécifiquement payout_to_driver
        if hasattr(manager, 'payout_to_driver'):
            logger.info("✅ payout_to_driver TROUVÉE !")
            return True
        else:
            logger.error("❌ payout_to_driver MANQUANTE !")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du rechargement: {e}")
        return False

if __name__ == "__main__":
    force_reload_paypal()
