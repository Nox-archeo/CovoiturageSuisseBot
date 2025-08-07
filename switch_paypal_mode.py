#!/usr/bin/env python3
"""
Script pour changer le mode PayPal entre sandbox et live
Usage: python switch_paypal_mode.py [sandbox|live]
"""

import sys
import os
import re

def switch_paypal_mode(mode):
    """Change le mode PayPal dans le fichier .env"""
    
    if mode not in ['sandbox', 'live']:
        print("❌ Mode invalide. Utilisez 'sandbox' ou 'live'")
        return False
    
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"❌ Fichier {env_file} non trouvé")
        return False
    
    # Lire le fichier .env
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Remplacer le mode PayPal
    if 'PAYPAL_MODE=' in content:
        content = re.sub(r'PAYPAL_MODE=.*', f'PAYPAL_MODE={mode}', content)
    else:
        content += f'\nPAYPAL_MODE={mode}\n'
    
    # Écrire le fichier modifié
    with open(env_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Mode PayPal changé en: {mode}")
    
    if mode == 'sandbox':
        print("⚠️  IMPORTANT: En mode sandbox, vous devez utiliser:")
        print("   - Un compte PayPal de test pour les paiements")
        print("   - Des identifiants sandbox dans la configuration")
        print("   - URL: https://developer.paypal.com/docs/api/get-started/#test-your-api-calls")
    else:
        print("⚠️  IMPORTANT: En mode live:")
        print("   - Utilisez des comptes PayPal différents pour tester")
        print("   - Ne jamais tester avec le même compte que l'application")
    
    print("\n🔄 Redémarrez le bot pour appliquer les changements")
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python switch_paypal_mode.py [sandbox|live]")
        print("Exemple: python switch_paypal_mode.py sandbox")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if switch_paypal_mode(mode):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
