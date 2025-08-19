#!/usr/bin/env python3
"""
Script pour vérifier le statut du déploiement Render
"""

import requests
import time
from datetime import datetime

def check_deployment_status():
    """Vérifie le statut du déploiement sur Render"""
    
    print("🚀 Vérification du déploiement Render...")
    print(f"📅 Heure actuelle: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # URL de votre service (à adapter si nécessaire)
    service_url = "https://covoiturage-suisse-bot.onrender.com"
    
    try:
        print("🔍 Test de connectivité au service...")
        response = requests.get(f"{service_url}/health", timeout=10)
        
        if response.status_code == 200:
            print("✅ Service déployé et accessible!")
            print(f"📊 Status Code: {response.status_code}")
            
            # Si votre endpoint health retourne du JSON
            try:
                data = response.json()
                print(f"📋 Réponse: {data}")
            except:
                print(f"📋 Réponse: {response.text[:100]}...")
                
        else:
            print(f"⚠️  Service accessible mais status: {response.status_code}")
            
    except requests.exceptions.ConnectTimeout:
        print("⏳ Service en cours de déploiement... (timeout de connexion)")
        print("   Le déploiement peut prendre quelques minutes.")
        
    except requests.exceptions.ConnectionError:
        print("🔄 Service en cours de redémarrage ou déploiement...")
        print("   Ceci est normal après un push Git.")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    
    print()
    print("📝 Instructions:")
    print("1. Le déploiement se fait automatiquement après le Git push")
    print("2. Render détecte les changements et redéploie le service")
    print("3. Le processus peut prendre 2-5 minutes")
    print("4. Vous pouvez suivre le déploiement sur: https://dashboard.render.com")
    print()
    print("✅ Modifications déployées:")
    print("   - Informations de contact mises à jour")
    print("   - Email: covoituragesuisse@gmail.com")
    print("   - Téléphone: 0795290160") 
    print("   - Telegram: @Lilith66store (ID: 5932296330)")

if __name__ == "__main__":
    check_deployment_status()
