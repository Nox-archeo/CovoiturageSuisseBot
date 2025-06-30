#!/usr/bin/env python
"""
Script de test pour les boutons après création de trajet
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au chemin Python
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_imports():
    """Test des imports des handlers"""
    print("🔄 Test des imports des handlers...")
    
    try:
        from handlers.create_trip_handler import (
            create_trip_conv_handler, 
            publish_trip_handler, 
            main_menu_handler, 
            my_trips_handler,
            handle_main_menu,
            handle_show_my_trips
        )
        print("✅ Tous les handlers importés avec succès")
        
        # Vérifier que les handlers ont les bons patterns
        print(f"✅ main_menu_handler pattern: {main_menu_handler.pattern.pattern}")
        print(f"✅ my_trips_handler pattern: {my_trips_handler.pattern.pattern}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'import : {e}")
        return False

def test_handler_functions():
    """Test que les fonctions handler existent et sont callable"""
    print("\n🔄 Test des fonctions handlers...")
    
    try:
        from handlers.create_trip_handler import handle_main_menu, handle_show_my_trips
        
        # Vérifier que les fonctions sont callable
        if callable(handle_main_menu):
            print("✅ handle_main_menu est callable")
        else:
            print("❌ handle_main_menu n'est pas callable")
            return False
            
        if callable(handle_show_my_trips):
            print("✅ handle_show_my_trips est callable")
        else:
            print("❌ handle_show_my_trips n'est pas callable")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des fonctions : {e}")
        return False

def test_bot_imports():
    """Test que bot.py peut importer tous les handlers"""
    print("\n🔄 Test des imports dans bot.py...")
    
    try:
        # Simuler l'import comme dans bot.py
        from handlers.create_trip_handler import (
            create_trip_conv_handler, 
            publish_trip_handler, 
            main_menu_handler, 
            my_trips_handler
        )
        
        print("✅ bot.py peut importer tous les handlers")
        
        # Vérifier les types
        from telegram.ext import CallbackQueryHandler, ConversationHandler
        
        if isinstance(create_trip_conv_handler, ConversationHandler):
            print("✅ create_trip_conv_handler est un ConversationHandler")
        else:
            print("❌ create_trip_conv_handler n'est pas un ConversationHandler")
            return False
            
        if isinstance(main_menu_handler, CallbackQueryHandler):
            print("✅ main_menu_handler est un CallbackQueryHandler")
        else:
            print("❌ main_menu_handler n'est pas un CallbackQueryHandler")
            return False
            
        if isinstance(my_trips_handler, CallbackQueryHandler):
            print("✅ my_trips_handler est un CallbackQueryHandler")
        else:
            print("❌ my_trips_handler n'est pas un CallbackQueryHandler")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des imports bot.py : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_target_functions():
    """Test que les fonctions cibles (menu principal et mes trajets) existent"""
    print("\n🔄 Test des fonctions cibles...")
    
    try:
        # Test import de la fonction du menu principal
        from handlers.menu_handlers import start_command
        if callable(start_command):
            print("✅ start_command (menu principal) disponible")
        else:
            print("❌ start_command n'est pas callable")
            return False
        
        # Test import de la fonction mes trajets
        from handlers.trip_handlers import list_my_trips
        if callable(list_my_trips):
            print("✅ list_my_trips disponible")
        else:
            print("❌ list_my_trips n'est pas callable")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des fonctions cibles : {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test des boutons après création de trajet")
    print("=" * 45)
    
    tests = [
        test_imports,
        test_handler_functions,
        test_target_functions,
        test_bot_imports
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 45)
    print("📊 Résultats des tests :")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Tous les tests réussis ({passed}/{total})")
        print("\n🎉 Les boutons devraient maintenant fonctionner !")
        print("\nPour tester :")
        print("  1. Démarrez le bot : python bot.py")
        print("  2. Créez un nouveau trajet")
        print("  3. Les boutons 'Mes trajets' et 'Menu principal' devraient maintenant fonctionner")
        return True
    else:
        print(f"❌ {total - passed} test(s) échoué(s) sur {total}")
        print("\n⚠️ Veuillez corriger les erreurs avant de tester le bot")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
