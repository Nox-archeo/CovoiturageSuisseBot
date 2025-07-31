#!/usr/bin/env python3
"""
Script de nettoyage d'urgence pour Render - à exécuter avant le bot
"""

import os
import re
import sys

def clean_env_variable(value):
    """Nettoie une variable d'environnement des caractères non-ASCII"""
    if not value:
        return value
    # Supprimer TOUS les caractères non-ASCII (0-127) et de contrôle  
    cleaned = re.sub(r'[^\x20-\x7E]', '', value)
    return cleaned.strip()

# Nettoyer immédiatement TOUTES les variables d'environnement
print("🧹 NETTOYAGE INTENSIF DES VARIABLES D'ENVIRONNEMENT")
print("=" * 60)

# Variables critiques à nettoyer
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
            print(f"🔧 Variable {var_name}: {original_len - new_len} caractères non-ASCII supprimés")
        
        os.environ[var_name] = cleaned_value
        print(f"✅ Variable {var_name} nettoyée ({new_len} caractères)")
    else:
        print(f"⚠️ Variable {var_name} non définie")

# Marquer l'environnement Render
os.environ['RENDER'] = 'true'
os.environ['ENVIRONMENT'] = 'production'

print("✅ Toutes les variables d'environnement ont été nettoyées")
print("🚀 Variables prêtes pour utilisation par le bot")

# Maintenant démarrer le bot nettoyé
if __name__ == '__main__':
    try:
        # Importer et démarrer le bot après nettoyage
        print("📦 Import du bot principal après nettoyage...")
        from bot import main as bot_main
        print("✅ Bot importé, démarrage...")
        bot_main()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
