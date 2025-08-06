#!/usr/bin/env python3
"""
Handler pour les raccourcis de menu vers les fonctions de recherche.
Facilite l'accès direct aux fonctions de recherche depuis le menu principal.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler

logger = logging.getLogger(__name__)

# ❌ FONCTION SUPPRIMÉE: Cette fonction contournait le ConversationHandler
# async def menu_search_passengers(update: Update, context: CallbackContext):
#     """Redirige depuis le menu vers la recherche de passagers"""
#     query = update.callback_query
#     await query.answer()
#     
#     # Importer dynamiquement pour éviter les imports circulaires
#     from handlers.search_passengers import start_passenger_search
#     
#     logger.info("Redirection menu → recherche de passagers")
#     return await start_passenger_search(update, context)

async def menu_search_drivers(update: Update, context: CallbackContext):
    """Redirige depuis le menu vers la recherche de conducteurs (trajets existants)"""
    query = update.callback_query
    await query.answer()
    
    # Importer dynamiquement pour éviter les imports circulaires  
    from handlers.search_trip_handler import start_search_trip
    
    logger.info("Redirection menu → recherche de conducteurs")
    
    # Pré-configurer le contexte pour la recherche de conducteurs
    context.user_data['search_user_type'] = 'passenger'  # L'utilisateur est passager qui cherche un conducteur
    
    return await start_search_trip(update, context)

# Handlers pour les callbacks depuis le menu
# ❌ PROBLÈME RÉSOLU: menu_search_passengers_handler interceptait search_passengers 
# et empêchait le ConversationHandler de s'activer correctement
# menu_search_passengers_handler = CallbackQueryHandler(menu_search_passengers, pattern=r"^search_passengers$")
menu_search_drivers_handler = CallbackQueryHandler(menu_search_drivers, pattern=r"^search_drivers$")

def register_menu_search_handlers(application):
    """Enregistre les handlers de recherche depuis le menu"""
    logger.info("🔧 Enregistrement des handlers de recherche du menu")
    
    # ❌ SUPPRIMÉ: Handler qui intercepte search_passengers et empêche ConversationHandler
    # application.add_handler(menu_search_passengers_handler)
    application.add_handler(menu_search_drivers_handler)
    
    logger.info("✅ Handlers de recherche du menu enregistrés")
    logger.info("   - Callback: search_passengers → Recherche de passagers")
    logger.info("   - Callback: search_drivers → Recherche de conducteurs")
