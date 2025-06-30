#!/usr/bin/env python3
"""
Script de démarrage pour Render avec webhook automatisé
Ce script démarre le bot en mode webhook avec FastAPI pour les paiements PayPal
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def validate_environment():
    """Valide que toutes les variables d'environnement nécessaires sont définies"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'WEBHOOK_URL',
        'PAYPAL_CLIENT_ID',
        'PAYPAL_CLIENT_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        logger.info("📋 Variables requises:")
        logger.info("   - TELEGRAM_BOT_TOKEN: Token de votre bot Telegram")
        logger.info("   - WEBHOOK_URL: URL de votre service Render (ex: https://votre-app.onrender.com)")
        logger.info("   - PAYPAL_CLIENT_ID: ID client PayPal")
        logger.info("   - PAYPAL_CLIENT_SECRET: Secret client PayPal")
        logger.info("   - PAYPAL_WEBHOOK_ID: ID du webhook PayPal (optionnel)")
        return False
    
    return True

def main():
    """Fonction principale"""
    logger.info("🚀 Démarrage du bot CovoiturageSuisse en mode webhook")
    logger.info("=" * 60)
    
    # Validation de l'environnement
    if not validate_environment():
        sys.exit(1)
    
    # Affichage de la configuration
    webhook_url = os.getenv('WEBHOOK_URL')
    port = int(os.getenv('PORT', 8000))
    
    logger.info(f"🌐 Webhook URL: {webhook_url}")
    logger.info(f"🔌 Port: {port}")
    logger.info(f"💳 PayPal: {'✅ Configuré' if os.getenv('PAYPAL_CLIENT_ID') else '❌ Non configuré'}")
    
    # Import et démarrage du serveur webhook
    try:
        logger.info("📦 Import du serveur webhook...")
        from webhook_bot import app
        import uvicorn
        
        logger.info("✅ Serveur webhook prêt")
        logger.info("🎯 Points d'accès:")
        logger.info(f"   - Webhook Telegram: {webhook_url}/webhook")
        logger.info(f"   - Webhook PayPal: {webhook_url}/paypal/webhook")
        logger.info(f"   - Santé: {webhook_url}/health")
        
        logger.info("🚀 Démarrage du serveur...")
        
        # Démarrage du serveur
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"❌ Erreur d'import: {e}")
        logger.info("💡 Assurez-vous que toutes les dépendances sont installées:")
        logger.info("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
