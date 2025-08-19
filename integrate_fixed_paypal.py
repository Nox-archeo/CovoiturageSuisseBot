#!/usr/bin/env python3
"""
Intégration complète du système PayPal fixé
Remplace l'ancien système défaillant
"""

import os
import shutil
import logging

logger = logging.getLogger(__name__)

def integrate_fixed_paypal_system():
    """
    Intègre le système PayPal fixé en remplaçant l'ancien
    """
    try:
        base_dir = "/Users/margaux/CovoiturageSuisse"
        
        # 1. Sauvegarder l'ancien système
        print("🔄 Sauvegarde de l'ancien système...")
        if os.path.exists(f"{base_dir}/auto_refund_manager.py"):
            shutil.copy2(
                f"{base_dir}/auto_refund_manager.py",
                f"{base_dir}/auto_refund_manager.py.broken_backup"
            )
            print("✅ Ancien système sauvegardé")
        
        # 2. Remplacer par le système fixé
        print("🔄 Installation du système fixé...")
        if os.path.exists(f"{base_dir}/fixed_auto_refund_manager.py"):
            shutil.copy2(
                f"{base_dir}/fixed_auto_refund_manager.py",
                f"{base_dir}/auto_refund_manager.py"
            )
            print("✅ Système fixé installé")
        
        # 3. Vérifier l'intégration du webhook
        print("🔄 Vérification du webhook...")
        with open(f"{base_dir}/paypal_webhook_handler.py", 'r') as f:
            content = f.read()
            if "trigger_automatic_refunds_fixed" in content:
                print("✅ Webhook intégré au système fixé")
            else:
                print("❌ Webhook non intégré - intervention manuelle requise")
        
        # 4. Vérifier la présence des nouveaux modules
        required_files = [
            "paypal_user_manager.py",
            "paypal_input_handler.py"
        ]
        
        for file in required_files:
            if os.path.exists(f"{base_dir}/{file}"):
                print(f"✅ {file} présent")
            else:
                print(f"❌ {file} manquant")
        
        print("\n🎉 Intégration du système PayPal fixé terminée !")
        print("\n📋 Étapes suivantes :")
        print("1. Intégrer paypal_user_manager dans bot.py")
        print("2. Intégrer paypal_input_handler dans les handlers")
        print("3. Tester le workflow complet de remboursement")
        print("4. Vérifier la collecte d'adresses PayPal")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur intégration système PayPal: {e}")
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    integrate_fixed_paypal_system()
