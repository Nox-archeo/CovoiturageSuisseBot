#!/usr/bin/env python3
"""
Script pour forcer le redéploiement sur Render
"""

import os
import sys
import time
from datetime import datetime

def force_render_redeploy():
    """Force un redéploiement sur Render en modifiant un fichier de version"""
    
    print("🚀 FORCE REDÉPLOIEMENT RENDER")
    print("=" * 40)
    
    # Créer un fichier de version avec timestamp
    version_info = {
        "deployment_time": datetime.now().isoformat(),
        "version": "webhook_paypal_fix_v2",
        "changes": [
            "Correction webhook PayPal handler",
            "Fix champs base de données (is_paid)",
            "Correction imports PayPalManager",
            "Fix signature trigger_automatic_refunds",
            "Ajout logique custom_id"
        ]
    }
    
    version_content = f"""# DEPLOYMENT VERSION - AUTO-GENERATED
# Dernière mise à jour: {version_info['deployment_time']}
# Version: {version_info['version']}

DEPLOYMENT_VERSION = "{version_info['version']}"
DEPLOYMENT_TIME = "{version_info['deployment_time']}"

CHANGELOG = [
"""
    
    for change in version_info['changes']:
        version_content += f'    "{change}",\n'
    
    version_content += "]\n"
    
    # Écrire le fichier de version
    with open('/Users/margaux/CovoiturageSuisse/deployment_version.py', 'w') as f:
        f.write(version_content)
    
    print(f"📝 Fichier de version créé: {version_info['version']}")
    print("🔧 Changements inclus:")
    for change in version_info['changes']:
        print(f"   - {change}")
    
    return True

if __name__ == "__main__":
    force_render_redeploy()
