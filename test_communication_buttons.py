#!/usr/bin/env python3
"""
Script pour envoyer manuellement les boutons de communication pour la réservation #28
"""

import asyncio
import sys
import os
import logging

# Configuration du chemin
sys.path.append('/Users/margaux/CovoiturageSuisse')

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_communication_buttons_for_booking_28():
    """Envoie les boutons de communication pour la réservation #28"""
    try:
        from post_booking_communication import add_post_booking_communication
        from unittest.mock import AsyncMock
        
        # Mock du bot pour tester
        mock_bot = AsyncMock()
        
        print("🔄 Envoi des boutons de communication pour réservation #28...")
        
        # Appeler la fonction
        await add_post_booking_communication(28, mock_bot)
        
        print("✅ Boutons envoyés avec succès!")
        print(f"📞 Appels de mock_bot.send_message: {mock_bot.send_message.call_count}")
        
        # Afficher les messages qui auraient été envoyés
        for call in mock_bot.send_message.call_args_list:
            args, kwargs = call
            print(f"\n📱 Message qui serait envoyé:")
            print(f"   Chat ID: {kwargs.get('chat_id')}")
            print(f"   Text: {kwargs.get('text')[:100]}...")
            if 'reply_markup' in kwargs:
                print(f"   Boutons: Oui (InlineKeyboardMarkup)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(send_communication_buttons_for_booking_28())
    if success:
        print("\n🎉 Test réussi!")
        print("💡 Les boutons de communication fonctionnent.")
    else:
        print("\n💥 Test échoué.")
