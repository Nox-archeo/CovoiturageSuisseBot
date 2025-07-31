#!/usr/bin/env python3
"""
Script de démarrage pour Render avec nettoyage des variables d'environnement
"""

import os
import sys
import re
import logging
from dotenv import load_dotenv

# Charger immédiatement les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def clean_env_variable(value):
    """Nettoie une variable d'environnement des caractères non-ASCII"""
    if not value:
        return value
    
    # Supprimer TOUS les caractères non-ASCII (0-127) et de contrôle  
    cleaned = re.sub(r'[^\x20-\x7E]', '', value)
    return cleaned.strip()

def clean_all_environment():
    """Nettoie TOUTES les variables d'environnement critiques"""
    logger.info("🧹 Nettoyage intensif des variables d'environnement...")
    
    # Variables critiques à nettoyer absolument
    critical_vars = [
        'TELEGRAM_BOT_TOKEN',
        'PAYPAL_CLIENT_ID', 
        'PAYPAL_CLIENT_SECRET',
        'BOT_URL',
        'WEBHOOK_URL'
    ]
    
    for var_name in critical_vars:
        value = os.getenv(var_name)
        if value:
            original_len = len(value)
            cleaned_value = clean_env_variable(value)
            new_len = len(cleaned_value)
            
            if original_len != new_len:
                logger.warning(f"🔧 Variable {var_name}: {original_len - new_len} caractères non-ASCII supprimés")
            
            os.environ[var_name] = cleaned_value
            logger.info(f"✅ Variable {var_name} nettoyée et mise à jour")
        else:
            logger.warning(f"⚠️ Variable {var_name} non définie")
    
    # Marquer l'environnement Render
    os.environ['RENDER'] = 'true'
    os.environ['ENVIRONMENT'] = 'production'
    
    logger.info("✅ Toutes les variables d'environnement ont été nettoyées")

def verify_token():
    """Vérifie que le token est propre"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ Token Telegram manquant")
        return False
    
    # Vérifier qu'il ne contient que des caractères ASCII valides
    if not all(32 <= ord(c) <= 126 for c in token):
        logger.error("❌ Token contient encore des caractères non-ASCII!")
        return False
    
    logger.info(f"✅ Token validé: {len(token)} caractères ASCII valides")
    return True

def main():
    """Fonction principale"""
    logger.info("🚀 Démarrage du bot CovoiturageSuisse sur Render")
    logger.info("=" * 60)
    
    # ÉTAPE 1: Nettoyer absolument tout
    clean_all_environment()
    
    # ÉTAPE 2: Vérifier le token
    if not verify_token():
        logger.error("❌ Échec de validation du token")
        sys.exit(1)
    
    # ÉTAPE 3: Importer et démarrer le bot
    try:
        logger.info("📦 Import du serveur webhook...")
        
        # Forcer le mode webhook sur Render
        if not os.getenv('WEBHOOK_URL'):
            # Construire l'URL webhook depuis les variables Render
            render_url = os.getenv('RENDER_EXTERNAL_URL')
            if not render_url:
                # Fallback - construire l'URL à partir du nom du service
                service_name = os.getenv('RENDER_SERVICE_NAME', 'covoiturage-suisse-bot')
                render_url = f"https://{service_name}.onrender.com"
            
            webhook_url = render_url
            os.environ['WEBHOOK_URL'] = webhook_url
            logger.info(f"🔧 WEBHOOK_URL configurée automatiquement: {webhook_url}")
        
        from webhook_bot import app
        import uvicorn
        
        port = int(os.getenv('PORT', 8000))
        webhook_url = os.getenv('WEBHOOK_URL')
        
        logger.info(f"🌐 Webhook URL: {webhook_url}")
        logger.info(f"🚀 Démarrage serveur webhook sur port {port}")
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info",
            access_log=True
        )
            
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
