#!/usr/bin/env python3
"""
Test d'intégration pour les types de trajets (simple, régulier, aller-retour)
"""

import logging
import sys
import os

# Ajouter le chemin de base pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test des imports
def test_imports():
    """Test que tous les imports nécessaires fonctionnent."""
    try:
        from handlers.create_trip_handler import (
            create_trip_conv_handler,
            SELECT_TRIP_TYPE,
            REGULAR_DAYS_SELECTION,
            RETURN_DATE_SELECTION,
            RETURN_TIME_SELECTION,
            handle_trip_type_selection,
            handle_regular_days_selection,
            handle_return_trip_options,
            create_regular_trips,
            create_round_trip
        )
        print("✅ Tous les imports sont réussis")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_conversation_handler():
    """Test que le ConversationHandler est bien configuré."""
    try:
        from handlers.create_trip_handler import create_trip_conv_handler
        
        # Vérifier que tous les états sont définis
        required_states = [
            'SELECT_TRIP_TYPE',
            'REGULAR_DAYS_SELECTION', 
            'RETURN_DATE_SELECTION',
            'RETURN_TIME_SELECTION'
        ]
        
        states = create_trip_conv_handler.states
        
        for state_name in required_states:
            # Obtenir la valeur numérique de l'état
            from handlers.create_trip_handler import (
                SELECT_TRIP_TYPE, REGULAR_DAYS_SELECTION, 
                RETURN_DATE_SELECTION, RETURN_TIME_SELECTION
            )
            
            state_values = {
                'SELECT_TRIP_TYPE': SELECT_TRIP_TYPE,
                'REGULAR_DAYS_SELECTION': REGULAR_DAYS_SELECTION,
                'RETURN_DATE_SELECTION': RETURN_DATE_SELECTION,
                'RETURN_TIME_SELECTION': RETURN_TIME_SELECTION
            }
            
            state_value = state_values[state_name]
            if state_value in states:
                print(f"✅ État {state_name} ({state_value}) configuré")
            else:
                print(f"❌ État {state_name} ({state_value}) manquant")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur dans la configuration du ConversationHandler: {e}")
        return False

def test_functions_exist():
    """Test que toutes les fonctions critiques existent."""
    try:
        from handlers.create_trip_handler import (
            select_trip_type,
            handle_trip_type_selection,
            handle_day_toggle,
            create_days_selection_keyboard,
            handle_regular_time_input,
            handle_return_time_input,
            handle_return_trip_options,
            create_regular_trips,
            create_round_trip,
            generate_group_id
        )
        
        functions = [
            'select_trip_type',
            'handle_trip_type_selection', 
            'handle_day_toggle',
            'create_days_selection_keyboard',
            'handle_regular_time_input',
            'handle_return_time_input',
            'handle_return_trip_options',
            'create_regular_trips',
            'create_round_trip',
            'generate_group_id'
        ]
        
        for func_name in functions:
            print(f"✅ Fonction {func_name} existe")
            
        return True
    except ImportError as e:
        print(f"❌ Fonction manquante: {e}")
        return False

def main():
    """Test principal."""
    print("🧪 Test d'intégration des types de trajets\n")
    
    tests = [
        ("Imports", test_imports),
        ("ConversationHandler", test_conversation_handler),
        ("Fonctions", test_functions_exist)
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
        print("🎉 Tous les tests sont passés ! L'intégration semble fonctionnelle.")
        return True
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return False

if __name__ == "__main__":
    main()
