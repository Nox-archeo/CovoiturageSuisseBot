#!/usr/bin/env python3
"""
REDIRECTION VERS WEBHOOK SERVER
Ce fichier redirige vers webhook_server.py pour le déploiement Render
"""

import os
import sys
import subprocess

if __name__ == "__main__":
    print("🔄 Redirection vers webhook_server.py...")
    print("📍 Déploiement Render détecté")
    
    # Exécuter webhook_server.py avec subprocess en gardant les logs
    try:
        # Remplacer le processus actuel par webhook_server.py
        os.execv(sys.executable, [sys.executable, "webhook_server.py"])
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)