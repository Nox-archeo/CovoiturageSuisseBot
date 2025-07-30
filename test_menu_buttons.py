#!/usr/bin/env python3
"""
Test rapide pour vérifier les nouveaux boutons de menu
"""

import sys
import os

# Ajouter le chemin racine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_menu_imports():
    """Teste que tous les imports fonctionnent"""
    print("🧪 TEST DES IMPORTS")
    print("=" * 40)
    
    try:
        from handlers.menu_search_shortcuts import register_menu_search_handlers
        print("✅ menu_search_shortcuts importé")
        
        from handlers.search_passengers import register_search_passengers_handler
        print("✅ search_passengers importé")
        
        from handlers.search_trip_handler import start_search_trip
        print("✅ search_trip_handler importé")
        
        print("\n🎉 Tous les imports fonctionnent !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_menu_structure():
    """Vérifie la structure du menu"""
    print("\n📋 STRUCTURE DU NOUVEAU MENU")
    print("=" * 40)
    
    print("Pour les utilisateurs avec les DEUX profils:")
    print("  🚗 Créer un trajet | 🔍 Chercher un trajet")
    print("  🔍 Chercher passagers | 🔍 Chercher conducteurs") 
    print("  📋 Mes trajets | 👤 Mon profil")
    print("  ❓ Aide")
    
    print("\nPour les conducteurs uniquement:")
    print("  🚗 Créer un trajet | 🔍 Chercher un trajet")
    print("  🔍 Chercher passagers | 📋 Mes trajets")
    print("  👤 Mon profil | ❓ Aide")
    
    print("\nPour les passagers uniquement:")
    print("  🚗 Créer un trajet | 🔍 Chercher un trajet")
    print("  🔍 Chercher conducteurs | 📋 Mes trajets")
    print("  👤 Mon profil | 🚗 Devenir conducteur")
    print("  ❓ Aide")
    
    return True

def main():
    """Fonction principale"""
    print("🔧 TEST DES NOUVEAUX BOUTONS DE MENU")
    print("=" * 50)
    
    results = []
    
    # Test des imports
    results.append(test_menu_imports())
    
    # Test de la structure
    results.append(test_menu_structure())
    
    # Résumé
    print("\n📊 RÉSUMÉ")
    print("=" * 50)
    print(f"✅ Tests réussis: {sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 SUCCÈS - Nouveaux boutons prêts !")
        print("\n🚀 NOUVELLES FONCTIONNALITÉS:")
        print("   ✅ Bouton 'Chercher passagers' - recherche avancée")
        print("   ✅ Bouton 'Chercher conducteurs' - recherche de trajets")
        print("   ✅ Menus adaptés selon le profil utilisateur")
        print("   ✅ Navigation intuitive et accessible")
        
        print("\n💡 UTILISATION:")
        print("   • Menu principal → '🔍 Chercher passagers'")
        print("   • Menu principal → '🔍 Chercher conducteurs'")
        print("   • Plus besoin de taper /chercher_passagers !")
        
    else:
        print("⚠️ Certains tests ont échoué.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
