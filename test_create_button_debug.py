#!/usr/bin/env python3
"""
Test rapide pour voir si la fonction start_create_trip fonctionne
"""

import logging
import sys
import os

# Ajouter le chemin de base pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_start_create_trip_import():
    """Test que la fonction start_create_trip peut être importée et utilisée."""
    try:
        from handlers.create_trip_handler import start_create_trip, select_trip_type
        print("✅ Fonctions start_create_trip et select_trip_type importées avec succès")
        
        # Vérifier que les patterns du ConversationHandler sont corrects
        from handlers.create_trip_handler import create_trip_conv_handler
        
        # Vérifier les entry_points
        entry_points = create_trip_conv_handler.entry_points
        patterns = []
        for entry_point in entry_points:
            if hasattr(entry_point, 'pattern'):
                patterns.append(entry_point.pattern.pattern)
        
        print(f"✅ Patterns d'entrée trouvés: {patterns}")
        
        # Vérifier que les patterns couvrent bien menu:create
        menu_create_covered = any('menu:create' in pattern for pattern in patterns)
        if menu_create_covered:
            print("✅ Le pattern 'menu:create' est couvert")
        else:
            print("❌ Le pattern 'menu:create' n'est PAS couvert")
            
        return menu_create_covered
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

def test_conversation_states():
    """Test que tous les états sont bien mappés."""
    try:
        from handlers.create_trip_handler import create_trip_conv_handler, SELECT_TRIP_TYPE
        
        states = create_trip_conv_handler.states
        
        if SELECT_TRIP_TYPE in states:
            handlers = states[SELECT_TRIP_TYPE]
            print(f"✅ État SELECT_TRIP_TYPE ({SELECT_TRIP_TYPE}) a {len(handlers)} handlers")
            
            # Vérifier les patterns des handlers
            for handler in handlers:
                if hasattr(handler, 'pattern'):
                    print(f"  - Pattern: {handler.pattern.pattern}")
                    
            return True
        else:
            print(f"❌ État SELECT_TRIP_TYPE ({SELECT_TRIP_TYPE}) non trouvé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des états: {e}")
        return False

def main():
    """Test principal."""
    print("🔍 Diagnostic rapide du bouton Créer\n")
    
    tests = [
        ("Import et patterns", test_start_create_trip_import),
        ("États de conversation", test_conversation_states)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        print("-" * 40)
        if test_func():
            passed += 1
            print(f"✅ {test_name} - RÉUSSI")
        else:
            print(f"❌ {test_name} - ÉCHEC")
    
    print(f"\n📊 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 La logique semble correcte. Le problème pourrait être ailleurs.")
    else:
        print("⚠️  Il y a un problème dans la configuration.")

if __name__ == "__main__":
    main()
