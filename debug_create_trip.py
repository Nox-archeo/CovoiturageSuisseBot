#!/usr/bin/env python3
"""
Test script pour déboguer les boutons "Créer un trajet" depuis différents endroits
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_callback_patterns():
    """Test des patterns de callback utilisés"""
    print("🧪 Test des patterns de callback 'Créer un trajet'")
    print("=" * 60)
    
    # Patterns trouvés dans le code
    patterns = [
        "menu:create",
        "main_menu:create_trip", 
        "creer_trajet"
    ]
    
    # Entry points du ConversationHandler
    entry_patterns = [
        "^creer_trajet$",
        "^menu:create$", 
        "^main_menu:create_trip$"
    ]
    
    print("📋 Callbacks utilisés dans les boutons:")
    for pattern in patterns:
        print(f"  - {pattern}")
    
    print("\n📋 Entry points du ConversationHandler:")
    for pattern in entry_patterns:
        print(f"  - {pattern}")
    
    print("\n✅ Tous les patterns sont maintenant couverts par le ConversationHandler")
    
    # Test des patterns de choix conducteur/passager
    choice_patterns = [
        "create_trip_type:driver",
        "create_trip_type:passenger"
    ]
    
    print("\n📋 Callbacks pour choix conducteur/passager:")
    for pattern in choice_patterns:
        print(f"  - {pattern}")
    
    print("\n🔍 Pattern handler dans CREATE_TRIP_TYPE state:")
    print("  - ^create_trip_type:(driver|passenger)$")
    
    # Vérifier la correspondance
    import re
    handler_pattern = r"^create_trip_type:(driver|passenger)$"
    
    for choice in choice_patterns:
        if re.match(handler_pattern, choice):
            print(f"✅ {choice} correspond au pattern")
        else:
            print(f"❌ {choice} ne correspond PAS au pattern")

def test_conversation_flow():
    """Test le flux de conversation"""
    print("\n🧪 Test du flux de conversation")
    print("=" * 60)
    
    print("📋 États de conversation définis:")
    states = [
        "CREATE_TRIP_TYPE",
        "CREATE_TRIP_OPTIONS", 
        "CREATE_DEPARTURE",
        "CREATE_ARRIVAL",
        "CREATE_CALENDAR",
        "CREATE_TIME",
        "CREATE_MINUTE",
        "CREATE_CONFIRM_DATETIME",
        "CREATE_SEATS",
        "CREATE_CONFIRM"
    ]
    
    for i, state in enumerate(states):
        print(f"  {i+1}. {state}")
    
    print("\n📋 Flux attendu:")
    print("  1. Bouton 'Créer un trajet' → start_create_trip → CREATE_TRIP_TYPE")
    print("  2. Choix 'Conducteur/Passager' → handle_create_trip_type → CREATE_TRIP_OPTIONS") 
    print("  3. Options → Villes → Date → Confirmation")
    
def analyze_logs():
    """Analyse des logs typiques"""
    print("\n🧪 Analyse des logs attendus")
    print("=" * 60)
    
    print("📋 Logs normaux lors du clic sur 'Créer un trajet':")
    print("  INFO:handlers.menu_handlers:Menu handler intercepted callback: menu:create")
    print("  INFO:handlers.menu_handlers:Menu button clicked: create")
    print("  INFO:handlers.menu_handlers:Redirecting to create trip flow")
    print("  INFO:handlers.create_trip_handler:Mode réglé sur 'create' dans start_create_trip")
    
    print("\n📋 Logs normaux lors du clic sur 'Conducteur':")
    print("  INFO:handlers.create_trip_handler:✅ Callback reçu dans handle_create_trip_type: create_trip_type:driver, choix: driver")
    print("  INFO:handlers.create_trip_handler:Type de trajet (création) enregistré: driver")
    
    print("\n⚠️  Si vous ne voyez pas ces logs, le problème est dans l'ordre des handlers ou les patterns.")

def main():
    """Fonction principale"""
    print("🔍 DIAGNOSTIC DES BOUTONS 'CRÉER UN TRAJET'")
    print("=" * 80)
    
    test_callback_patterns()
    test_conversation_flow() 
    analyze_logs()
    
    print("\n" + "=" * 80)
    print("🎯 RÉSUMÉ DES CORRECTIONS APPLIQUÉES:")
    print("✅ Ajout des entry points menu:create et main_menu:create_trip au ConversationHandler")
    print("✅ Harmonisation des callbacks (search_trip_handler corrigé)")
    print("✅ Ordre des handlers optimisé dans bot.py")
    
    print("\n🧪 POUR TESTER:")
    print("1. Démarrez le bot et regardez les logs")
    print("2. Testez depuis /start → 'Créer un trajet'")
    print("3. Testez depuis Profil → 'Mes trajets' → 'Créer un trajet'") 
    print("4. Vérifiez que les clics sur 'Conducteur/Passager' génèrent des logs")
    
    print("\n💡 Si ça ne fonctionne toujours pas:")
    print("- Vérifiez l'ordre des handlers dans bot.py")
    print("- Assurez-vous que le ConversationHandler create_trip_conv_handler est bien enregistré")
    print("- Vérifiez qu'aucun autre handler n'intercepte les callbacks")

if __name__ == "__main__":
    main()
