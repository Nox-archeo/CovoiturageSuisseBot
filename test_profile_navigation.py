#!/usr/bin/env python
"""
Script de test pour vérifier la navigation dans le profil
Ce script simule des clics sur les boutons du profil et vérifie que les bons messages sont affichés.
"""
import logging
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Configurer le logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TestProfileNavigation:
    """
    Classe pour tester la navigation dans le profil
    """
    def __init__(self):
        self.update = MagicMock()
        self.context = MagicMock()
        self.query = AsyncMock()
        self.update.callback_query = self.query
        self.update.effective_user.id = 12345
        self.context.user_data = {}
        self.messages = []  # Pour stocker les messages envoyés

    def setup_query_data(self, data):
        """Configure la donnée du callback query"""
        self.query.data = data
        
    def setup_mocks(self):
        """Configure les mocks nécessaires"""
        # Remplacer la méthode edit_message_text pour capturer les messages
        async def capture_message(text=None, reply_markup=None, parse_mode=None):
            self.messages.append({
                'text': text,
                'reply_markup': reply_markup,
                'parse_mode': parse_mode,
                'timestamp': datetime.now()
            })
            logger.info(f"Message édité: {text[:50]}...")
            return True
        
        self.query.edit_message_text = capture_message
        self.query.answer = AsyncMock(return_value=True)

    async def test_profile_actions(self):
        """Teste les différentes actions du profil"""
        from handlers.profile_handler import handle_profile_action, show_my_trips
        
        # Test de l'action "my_trips"
        logger.info("=== Test de l'action 'my_trips' ===")
        self.setup_query_data("profile:my_trips")
        await handle_profile_action(self.update, self.context)
        
        # Vérifier que le message de "my_trips" a été affiché
        if self.messages:
            last_message = self.messages[-1]['text']
            if "Mes Trajets" in last_message:
                logger.info("✓ Le message 'Mes Trajets' a été affiché")
            else:
                logger.error(f"✗ Message inattendu: {last_message[:100]}...")
        else:
            logger.error("✗ Aucun message capturé pour 'my_trips'")
        
        # Nettoyer pour le prochain test
        self.messages = []
        
        # Test de l'action "back_to_profile"
        logger.info("=== Test du retour au profil ===")
        self.setup_query_data("profile:back_to_profile")
        await handle_profile_action(self.update, self.context)
        
        # Vérifier que le profil a été affiché
        if self.messages:
            last_message = self.messages[-1]['text']
            if "Profil de" in last_message:
                logger.info("✓ Le profil a été affiché")
            else:
                logger.error(f"✗ Message inattendu: {last_message[:100]}...")
        else:
            logger.error("✗ Aucun message capturé pour 'back_to_profile'")

async def main():
    """Fonction principale pour exécuter les tests"""
    # Simuler une base de données et des modèles pour les tests
    import sys
    from unittest.mock import patch
    
    # Créer des mocks pour les modules et fonctions externes
    class MockDB:
        def query(self, *args):
            return self
            
        def filter(self, *args):
            return self
            
        def first(self):
            # Simuler un utilisateur
            user = MagicMock()
            user.id = 1
            user.telegram_id = 12345
            user.full_name = "Test User"
            user.username = "testuser"
            return user
            
    # Patcher la fonction get_db pour retourner notre mock
    def mock_get_db():
        return MockDB()
    
    # Patcher les modèles pour les tests
    class MockTrip:
        pass
        
    class MockBooking:
        pass
        
    class MockUser:
        pass
    
    # Appliquer les patches
    with patch('handlers.profile_handler.get_db', mock_get_db), \
         patch('handlers.profile_handler.Trip', MockTrip), \
         patch('handlers.profile_handler.Booking', MockBooking), \
         patch('handlers.profile_handler.User', MockUser):
        # Exécuter les tests
        test = TestProfileNavigation()
        test.setup_mocks()
        await test.test_profile_actions()

if __name__ == "__main__":
    asyncio.run(main())
