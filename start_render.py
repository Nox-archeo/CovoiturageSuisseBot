#!/usr/bin/env python3
"""
Script de démarrage pour Render avec nettoyage des variables d'environnement
"""

import os
import sys
import re
import logging
from dotenv import load_dotenv

load_dotenv()

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
    cleaned = re.sub(r'[^\x20-\x7E]', '', value)
    return cleaned.strip()

def main():
    """Fonction principale"""
    logger.info("🚀 Démarrage du bot sur Render")
    
    # Nettoyer les variables d'environnement
    vars_to_clean = ['TELEGRAM_BOT_TOKEN', 'PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET']
    
    for var_name in vars_to_clean:
        value = os.getenv(var_name)
        if value:
            cleaned_value = clean_env_variable(value)
            os.environ[var_name] = cleaned_value
            logger.info(f"✅ Variable {var_name} nettoyée")
    
    # Marquer l'environnement Render
    os.environ['RENDER'] = 'true'
    os.environ['ENVIRONMENT'] = 'production'
    
    # Vérifier le token
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.error("❌ Token Telegram manquant")
        sys.exit(1)
    
    try:
        # Importer et démarrer le bot
        from bot import main as bot_main
        logger.info("✅ Bot importé, démarrage...")
        bot_main()
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
