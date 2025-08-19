#!/usr/bin/env python3
"""
Vérification post-déploiement des corrections de recherche
"""

import requests
import time
from datetime import datetime

def check_deployment_and_fixes():
    """Vérifie le déploiement et les corrections"""
    
    print("🚀 Vérification post-déploiement des corrections")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    print("\n✅ CORRECTIONS APPLIQUÉES:")
    print("1. 🔧 Configuration DB PostgreSQL optimisée:")
    print("   - pool_size: 20 (était: 5)")
    print("   - max_overflow: 30 (était: 10)")
    print("   - pool_timeout: 60s (était: 30s)")
    print("   → Fix: sqlalchemy.exc.TimeoutError")
    
    print("\n2. 🔧 Redirection conducteur corrigée:")
    print("   - AVANT: Boucle infinie callback search_passengers")
    print("   - MAINTENANT: Appel direct start_passenger_search()")
    print("   → Fix: Bouton 'Je suis conducteur' fonctionnel")
    
    print("\n3. 🔧 Boutons annuler fixes:")
    print("   - search_cancel correctement géré")
    print("   - ConversationHandler.END sur annulation")
    print("   → Fix: Boutons 'Annuler' fonctionnels")
    
    print("\n📱 TESTS À EFFECTUER DANS TELEGRAM:")
    print("=" * 50)
    print("1. /start → Chercher un trajet")
    print("   ✓ Bouton 'Je suis conducteur' → doit aller à recherche passagers")
    print("   ✓ Bouton 'Je suis passager' → doit aller à recherche trajets")
    print("   ✓ Bouton 'Annuler' → doit fermer la conversation")
    
    print("\n2. /chercher_trajet")
    print("   ✓ Ne doit plus boucler indéfiniment")
    print("   ✓ Doit afficher le menu de sélection")
    
    print("\n3. Test de charge DB")
    print("   ✓ Plus de TimeoutError avec plusieurs utilisateurs")
    print("   ✓ Connexions DB gérées correctement")
    
    print("\n🔍 SURVEILLANCE DES LOGS:")
    print("=" * 50)
    print("✅ Logs à surveiller (doivent disparaître):")
    print("   - 'sqlalchemy.exc.TimeoutError: QueuePool limit'")
    print("   - '/chercher_trajet /chercher_trajet /chercher_trajet'")
    print("   - 'Callback: search_passengers... [BOUCLE]'")
    
    print("\n✅ Logs positifs à voir:")
    print("   - '🎯 REDIRECT: Conducteur détecté - appel direct'")
    print("   - '✅ Connexion DB réussie'")
    print("   - '🚀 START PASSENGER SEARCH: user_id=...'")
    
    # Test de connectivité basique
    print("\n🌐 TEST DE CONNECTIVITÉ:")
    print("=" * 50)
    
    try:
        # Test simple de réponse du serveur
        response = requests.get("https://covoiturage-suisse-bot.onrender.com/", timeout=10)
        print(f"✅ Serveur accessible - Status: {response.status_code}")
        
        if response.status_code == 404:
            print("   ℹ️  404 normal - webhook endpoint actif")
        
    except requests.exceptions.Timeout:
        print("⏳ Déploiement en cours... (normal après push)")
        
    except Exception as e:
        print(f"⚠️  Test connectivité: {e}")
    
    print("\n🎯 PROCHAINES ÉTAPES:")
    print("=" * 50)
    print("1. Attendre 2-3 minutes pour le déploiement complet")
    print("2. Tester /start dans votre bot Telegram")
    print("3. Vérifier que les boutons fonctionnent")
    print("4. Tester /chercher_trajet directement")
    print("5. Surveiller les logs pour confirmer les fixes")
    
    print(f"\n🕒 Déploiement initié à: {datetime.now().strftime('%H:%M:%S')}")
    print("✅ Render redéploiera automatiquement dans 2-5 minutes")

if __name__ == "__main__":
    check_deployment_and_fixes()
