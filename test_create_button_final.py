#!/usr/bin/env python3
"""
Test final pour vérifier que le bouton "Créer" fonctionne dans tous les contextes
"""

import logging
import sys
import os

# Ajouter le chemin de base pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_create_button_patterns():
    """Test que tous les patterns sont corrects."""
    try:
        from handlers.create_trip_handler import create_trip_conv_handler
        
        print("🔍 Test des patterns du bouton Créer\n")
        
        # Vérifier les entry points
        entry_points = create_trip_conv_handler.entry_points
        patterns = []
        
        for entry_point in entry_points:
            if hasattr(entry_point, 'pattern'):
                pattern = entry_point.pattern.pattern
                patterns.append(pattern)
                print(f"✅ Pattern trouvé: {pattern}")
        
        # Vérifier que menu:create est couvert
        menu_create_covered = any('menu:create' in pattern for pattern in patterns)
        
        if menu_create_covered:
            print("✅ Le pattern 'menu:create' est couvert")
        else:
            print("❌ Le pattern 'menu:create' n'est PAS couvert")
            return False
        
        print(f"\n📊 Total: {len(entry_points)} entry points trouvés")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_button_consistency():
    """Test que tous les boutons utilisent menu:create."""
    print("\n🔍 Test de cohérence des boutons\n")
    
    # Rechercher tous les boutons "Créer"
    import subprocess
    result = subprocess.run(
        ['grep', '-r', 'Créer.*callback_data', '.', '--include=*.py'],
        capture_output=True, text=True
    )
    
    lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
    
    menu_create_count = 0
    other_count = 0
    
    for line in lines:
        if 'callback_data="menu:create"' in line:
            menu_create_count += 1
        elif 'callback_data=' in line and 'Créer' in line:
            other_count += 1
            print(f"⚠️  Bouton non-unifié: {line.strip()}")
    
    print(f"✅ Boutons avec menu:create: {menu_create_count}")
    print(f"⚠️  Boutons avec autres callback_data: {other_count}")
    
    return other_count == 0

def main():
    """Test principal."""
    print("🧪 Test final du bouton Créer\n")
    
    success1 = test_create_button_patterns()
    success2 = test_button_consistency()
    
    print(f"\n📊 Résultats:")
    print(f"  - Patterns: {'✅ OK' if success1 else '❌ ÉCHEC'}")
    print(f"  - Cohérence: {'✅ OK' if success2 else '❌ ÉCHEC'}")
    
    if success1 and success2:
        print("\n🎉 Tous les tests sont réussis !")
        print("Le bouton 'Créer' devrait maintenant fonctionner partout.")
    else:
        print("\n❌ Il reste des problèmes à corriger.")
    
    return success1 and success2

if __name__ == "__main__":
    main()
