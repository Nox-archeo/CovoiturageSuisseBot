#!/usr/bin/env python3
"""Test rapide de la commande /creer"""

import asyncio
from unittest.mock import Mock, AsyncMock
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

# Import de nos handlers
from handlers.create_trip_handler import creer_command

async def test_creer_command():
    """Test si la commande /creer fonctionne"""
    
    # Mock des objets Telegram
    user = User(id=123456, first_name="Test", is_bot=False)
    chat = Chat(id=123456, type="private")
    message = Mock(spec=Message)
    message.from_user = user
    message.chat = chat
    message.text = "/creer"
    
    update = Mock(spec=Update)
    update.message = message
    update.effective_user = user
    update.effective_chat = chat
    
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    
    try:
        # Test de la fonction
        result = await creer_command(update, context)
        print(f"✅ Commande /creer OK - Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Erreur /creer: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_creer_command())
    print("✅ Test réussi!" if success else "❌ Test échoué!")
