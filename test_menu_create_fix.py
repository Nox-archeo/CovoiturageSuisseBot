#!/usr/bin/env python
"""
Script de test pour vérifier que le menu "Créer" fonctionne correctement
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import Application

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_handler_order():
    """Test l'ordre des handlers"""
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ Token non trouvé dans le fichier .env")
        return
    
    try:
        # Import handlers
        from handlers.create_trip_handler import create_trip_conv_handler
        from handlers.menu_handlers import handle_menu_buttons
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers in the same order as bot.py
        print("📝 Ajout du create_trip_conv_handler...")
        application.add_handler(create_trip_conv_handler)
        
        print("📝 Ajout des menu handlers...")
        from telegram.ext import CallbackQueryHandler
        application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:search_trip$"))
        
        # Check handlers order
        print("\n🔍 Vérification de l'ordre des handlers:")
        for i, handler in enumerate(application.handlers[0]):  # Group 0 handlers
            handler_type = type(handler).__name__
            if hasattr(handler, 'pattern') and handler.pattern:
                pattern = handler.pattern.pattern if hasattr(handler.pattern, 'pattern') else str(handler.pattern)
                print(f"  {i+1}. {handler_type} - Pattern: {pattern}")
            elif hasattr(handler, 'entry_points'):
                entry_patterns = []
                for ep in handler.entry_points:
                    if hasattr(ep, 'pattern'):
                        entry_patterns.append(ep.pattern.pattern if hasattr(ep.pattern, 'pattern') else str(ep.pattern))
                print(f"  {i+1}. {handler_type} - Entry points: {entry_patterns}")
            else:
                print(f"  {i+1}. {handler_type}")
        
        print("\n✅ Test completed. Le create_trip_conv_handler devrait être en première position.")
        print("📱 Vous pouvez maintenant tester le bot avec /start puis 'Créer'")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        logger.error(f"Erreur lors du test: {e}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(test_handler_order())
