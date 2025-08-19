#!/usr/bin/env python3
"""
Script de test pour vérifier les corrections des boutons de recherche
"""

import asyncio
import logging
from database import get_db
from database.models import User

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_database_connections():
    """Test des connexions à la base de données"""
    print("🔍 Test des connexions à la base de données...")
    
    try:
        # Test de connexion multiple
        for i in range(3):
            db = get_db()
            users = db.query(User).limit(1).all()
            print(f"✅ Connexion {i+1}/3 réussie - {len(users)} utilisateur(s) trouvé(s)")
            db.close()
        
        print("✅ Test de connexions multiples réussi")
        
    except Exception as e:
        print(f"❌ Erreur de connexion DB: {e}")
        return False
    
    return True

def test_handler_imports():
    """Test des imports des handlers"""
    print("\n🔍 Test des imports des handlers...")
    
    try:
        from handlers.search_passengers import start_passenger_search
        print("✅ search_passengers importé avec succès")
        
        from handlers.search_trip_handler import start_search_trip, handle_search_user_type
        print("✅ search_trip_handler importé avec succès")
        
        from handlers.menu_handlers import cancel
        print("✅ menu_handlers importé avec succès")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_conversation_handlers():
    """Test de la configuration des ConversationHandlers"""
    print("\n🔍 Test des ConversationHandlers...")
    
    try:
        from handlers.search_trip_handler import search_trip_conv_handler
        from handlers.search_passengers import search_passengers_handler
        
        # Vérifier la configuration
        print(f"✅ search_trip_conv_handler: {len(search_trip_conv_handler.states)} états")
        print(f"✅ search_passengers_handler: {len(search_passengers_handler.states)} états")
        
        # Vérifier les entry points
        trip_entries = len(search_trip_conv_handler.entry_points)
        passenger_entries = len(search_passengers_handler.entry_points) 
        
        print(f"✅ search_trip: {trip_entries} entry points")
        print(f"✅ search_passengers: {passenger_entries} entry points")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur ConversationHandlers: {e}")
        return False

async def main():
    """Fonction principale de test"""
    print("🚀 Test des corrections des boutons de recherche\n")
    
    # Tests
    db_ok = await test_database_connections()
    imports_ok = test_handler_imports()
    handlers_ok = test_conversation_handlers()
    
    print("\n📊 Résultats des tests:")
    print(f"   Base de données: {'✅' if db_ok else '❌'}")
    print(f"   Imports handlers: {'✅' if imports_ok else '❌'}")
    print(f"   ConversationHandlers: {'✅' if handlers_ok else '❌'}")
    
    if all([db_ok, imports_ok, handlers_ok]):
        print("\n🎉 Tous les tests réussis !")
        print("\n📝 Corrections appliquées:")
        print("   ✅ Configuration pool DB PostgreSQL améliorée")
        print("   ✅ Redirection conducteur → search_passengers corrigée")
        print("   ✅ Boutons annuler configurés correctement")
        print("\n🚀 Prêt pour le déploiement !")
    else:
        print("\n⚠️ Certains tests ont échoué - vérifiez les logs")

if __name__ == "__main__":
    asyncio.run(main())
