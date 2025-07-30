#!/usr/bin/env python3
"""
Test pour debug quel handler intercepte menu:create
"""

import logging
import sys
import os

# Ajouter le chemin de base pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import CallbackQueryHandler, Application

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_callback_handler(update: Update, context):
    """Handler de debug qui log tous les callbacks."""
    if update.callback_query:
        logger.info(f"🔍 DEBUG HANDLER: callback intercepté = {update.callback_query.data}")
        if update.callback_query.data == "menu:create":
            logger.info("🎯 menu:create intercepté par debug_callback_handler !")
    return  # Ne rien faire, juste logger

def test_handler_priority():
    """Test l'ordre des handlers pour voir qui intercepte menu:create."""
    try:
        from handlers.create_trip_handler import create_trip_conv_handler
        
        # Vérifier les entry_points
        entry_points = create_trip_conv_handler.entry_points
        
        print("📋 Entry points du create_trip_conv_handler:")
        for i, entry_point in enumerate(entry_points):
            print(f"  {i+1}. {entry_point}")
            if hasattr(entry_point, 'pattern'):
                print(f"     Pattern: {entry_point.pattern.pattern}")
        
        # Créer un handler de test
        debug_handler = CallbackQueryHandler(debug_callback_handler)
        
        print(f"\n🔍 Handler de debug créé: {debug_handler}")
        print("Pour tester, ajoutez ce handler EN PREMIER dans bot.py :")
        print("application.add_handler(CallbackQueryHandler(debug_callback_handler))")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Test principal."""
    print("🔍 Debug des handlers pour menu:create\n")
    
    test_handler_priority()

if __name__ == "__main__":
    main()
