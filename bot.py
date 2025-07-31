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
    
    # Exécuter webhook_server.py directement en important et lançant
    try:
        # Importer et exécuter directement le serveur webhook
        import webhook_server
        # Le serveur se lance automatiquement via le if __name__ == "__main__"
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)