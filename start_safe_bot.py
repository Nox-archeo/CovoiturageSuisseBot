#!/usr/bin/env python3
"""
Script de démarrage sécurisé pour le bot de covoiturage suisse
Corrige automatiquement les problèmes de fichiers pickle corrompus
"""

import os
import pickle
import sys
from pathlib import Path

def fix_pickle_files():
    """Corrige les fichiers pickle corrompus"""
    pickle_files = ['bot_data.pickle', 'bot_data_complete_communes.pickle']
    
    for pickle_file in pickle_files:
        if os.path.exists(pickle_file):
            try:
                # Tester si le fichier peut être lu
                with open(pickle_file, 'rb') as f:
                    pickle.load(f)
                print(f"✅ {pickle_file} est valide")
            except Exception as e:
                print(f"⚠️  {pickle_file} corrompu: {e}")
                
                # Sauvegarder l'ancien fichier
                backup_name = f"{pickle_file}.backup"
                if os.path.exists(backup_name):
                    os.remove(backup_name)
                os.rename(pickle_file, backup_name)
                print(f"📦 Ancien fichier sauvegardé dans {backup_name}")
                
                # Créer un nouveau fichier valide
                data = {
                    'user_data': {},
                    'chat_data': {},
                    'bot_data': {},
                    'conversations': {}
                }
                
                with open(pickle_file, 'wb') as f:
                    pickle.dump(data, f)
                print(f"✅ Nouveau {pickle_file} créé")
        else:
            # Créer le fichier s'il n'existe pas
            data = {
                'user_data': {},
                'chat_data': {},
                'bot_data': {},
                'conversations': {}
            }
            
            with open(pickle_file, 'wb') as f:
                pickle.dump(data, f)
            print(f"✅ {pickle_file} créé")

def verify_system():
    """Vérifie que tous les composants sont OK"""
    print("🔍 VÉRIFICATION DU SYSTÈME")
    print("=" * 40)
    
    # Vérifier les fichiers de données critiques
    critical_files = [
        'data/swiss_localities.json',
        'database/covoiturage.db'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} trouvé")
        else:
            print(f"❌ {file_path} manquant")
            return False
    
    # Tester les imports critiques
    try:
        from utils.swiss_cities import find_locality
        from utils.route_distance import get_route_distance_km
        from handlers.create_trip_handler import compute_price_auto
        print("✅ Imports critiques OK")
        
        # Test rapide de fonctionnalité
        result = find_locality('1727')
        if result:
            print(f"✅ Recherche fonctionnelle: {result[0]['name']}")
        else:
            print("❌ Recherche non fonctionnelle")
            return False
            
    except Exception as e:
        print(f"❌ Erreur imports: {e}")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🤖 DÉMARRAGE SÉCURISÉ DU BOT DE COVOITURAGE SUISSE")
    print("=" * 60)
    
    # 1. Corriger les fichiers pickle
    print("\\n🔧 Correction des fichiers pickle...")
    fix_pickle_files()
    
    # 2. Vérifier le système
    print("\\n🔍 Vérification du système...")
    if not verify_system():
        print("❌ Le système n'est pas prêt")
        return 1
    
    # 3. Démarrer le bot
    print("\\n🚀 Démarrage du bot...")
    try:
        import bot
        print("✅ Bot importé avec succès")
        
        # Démarrer le bot
        bot.main()
        
    except KeyboardInterrupt:
        print("\\n⏸️  Bot arrêté par l'utilisateur")
        return 0
    except Exception as e:
        print(f"❌ Erreur démarrage: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
