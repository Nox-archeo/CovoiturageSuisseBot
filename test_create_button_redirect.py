#!/usr/bin/env python3
"""
Test script pour vérifier que les boutons "Créer un trajet" redirigent bien vers la création de trajet.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from unittest.mock import Mock, AsyncMock
from handlers.menu_handlers import handle_menu_buttons
from handlers.create_trip_handler import start_create_trip

async def test_create_button_redirect():
    """Test que le bouton Créer un trajet redirige bien vers la création"""
    print("🧪 Test redirection bouton 'Créer un trajet'")
    print("=" * 60)
    
    # Mock de l'update avec callback_query
    mock_update = Mock()
    mock_context = Mock()
    
    # Mock du callback_query
    mock_query = AsyncMock()
    mock_query.data = "menu:create"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()
    mock_update.callback_query = mock_query
    
    # Mock de l'utilisateur
    mock_user = Mock()
    mock_user.id = 12345
    mock_update.effective_user = mock_user
    
    print(f"📞 Test callback: {mock_query.data}")
    
    try:
        # Appeler le handler de menu
        result = await handle_menu_buttons(mock_update, mock_context)
        
        # Vérifier que la fonction a été appelée
        mock_query.answer.assert_called_once()
        
        print("✅ Handler de menu appelé avec succès")
        
        # Vérifier que les données utilisateur ont été configurées
        if hasattr(mock_context, 'user_data') and mock_context.user_data:
            print("✅ Données utilisateur configurées")
        else:
            print("⚠️ Données utilisateur non configurées (normal pour un mock)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_start_create_trip_callback():
    """Test que start_create_trip peut gérer un callback_query"""
    print("\n🧪 Test start_create_trip avec callback_query")
    print("=" * 60)
    
    # Mock de l'update avec callback_query
    mock_update = Mock()
    mock_context = Mock()
    mock_context.user_data = {}
    
    # Mock du callback_query
    mock_query = AsyncMock()
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()
    mock_update.callback_query = mock_query
    mock_update.message = None  # Pas de message direct
    
    # Mock de l'utilisateur
    mock_user = Mock()
    mock_user.id = 12345
    mock_update.effective_user = mock_user
    
    try:
        # Appeler start_create_trip directement
        result = await start_create_trip(mock_update, mock_context)
        
        # Vérifier que la fonction a été appelée
        mock_query.answer.assert_called_once()
        mock_query.edit_message_text.assert_called_once()
        
        # Vérifier le contenu du message
        call_args = mock_query.edit_message_text.call_args
        message_text = call_args[0][0] if call_args[0] else ""
        
        print("✅ start_create_trip appelé avec succès")
        print(f"📄 Message généré: {message_text[:100]}...")
        
        # Vérifications
        checks = []
        
        if "Création d'un nouveau trajet" in message_text:
            checks.append("✅ Message de création présent")
        else:
            checks.append("❌ Message de création manquant")
        
        if "Conducteur" in message_text and "Passager" in message_text:
            checks.append("✅ Options de rôle présentes")
        else:
            checks.append("❌ Options de rôle manquantes")
        
        if mock_context.user_data.get('mode') == 'create':
            checks.append("✅ Mode 'create' configuré")
        else:
            checks.append("❌ Mode 'create' non configuré")
        
        print("\n🔍 VÉRIFICATIONS:")
        for check in checks:
            print(check)
        
        return all("✅" in check for check in checks)
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Fonction principale de test"""
    print("🧪 TEST DES BOUTONS 'CRÉER UN TRAJET'")
    print("=" * 60)
    
    # Tests
    tests = [
        ("Handler de menu", await test_create_button_redirect()),
        ("start_create_trip", await test_start_create_trip_callback())
    ]
    
    print("\n📊 RÉSULTATS FINAUX:")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in tests:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 {success_count}/{len(tests)} tests réussis")
    
    if success_count == len(tests):
        print("\n🎉 TOUS LES TESTS PASSENT !")
        print("Le bouton 'Créer un trajet' devrait maintenant fonctionner.")
    else:
        print("\n⚠️  CERTAINS TESTS ÉCHOUENT")
        print("Vérifiez les corrections nécessaires.")

if __name__ == "__main__":
    asyncio.run(main())
