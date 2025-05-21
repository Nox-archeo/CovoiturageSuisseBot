#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/handlers/trip_search/search_handler.py
"""
Handler pour la recherche avancée de trajets.
Permet aux utilisateurs de trouver des trajets adaptés à leurs besoins.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, 
    ConversationHandler, 
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters
)
import logging

logger = logging.getLogger(__name__)

# États pour la conversation de recherche
(
    SELECTING_DEPARTURE,
    SELECTING_ARRIVAL,
    SELECTING_DATE,
    SELECTING_TIME,
    CONFIRMING_SEARCH,
    VIEWING_RESULTS,
    FILTERING_RESULTS,
    SORTING_RESULTS,
    BOOKING_TRIP,
    CONFIRMING_BOOKING,
    ENTERING_DEPARTURE,
    ENTERING_ARRIVAL,
    VIEWING_TRIP_DETAILS,
    RATING_TRIP,
    SETTING_PREFERENCES
) = range(15)

async def start_search(update: Update, context: CallbackContext):
    """Démarre le processus de recherche de trajet"""
    # Créer un clavier avec les villes principales
    keyboard = []
    popular_cities = ["Fribourg", "Genève", "Lausanne", "Zürich", "Berne", "Bâle"]
    
    for city in popular_cities:
        keyboard.append([InlineKeyboardButton(city, callback_data=f"from_{city}")])
    
    keyboard.append([InlineKeyboardButton("🔍 Recherche avancée", callback_data="advanced_search")])
    keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel_search")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🔍 Recherche de trajets\n\n"
            "1️⃣ Choisissez votre ville de départ:\n"
            "- Sélectionnez une ville dans la liste\n"
            "- Ou utilisez la recherche avancée",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🔍 Recherche de trajets\n\n"
            "1️⃣ Choisissez votre ville de départ:\n"
            "- Sélectionnez une ville dans la liste\n"
            "- Ou utilisez la recherche avancée",
            reply_markup=reply_markup
        )
    return SELECTING_DEPARTURE

async def search_trips(update: Update, context):
    """Recherche de trajets selon les critères fournis"""
    query = update.callback_query
    await query.answer()
    
    # Ici viendrait la logique de recherche des trajets
    # Pour l'instant, affichons un message temporaire
    await query.edit_message_text(
        "🔍 Recherche en cours...\n\n"
        "Cette fonctionnalité sera bientôt disponible.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Retour au menu", callback_data="back_to_menu")
        ]])
    )
    return ConversationHandler.END

async def cancel_search(update: Update, context):
    """Annule la recherche en cours"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Recherche annulée.")
    else:
        await update.message.reply_text("❌ Recherche annulée.")
    
    context.user_data.clear()  # Nettoyer les données utilisateur
    return ConversationHandler.END

def register(application):
    """Enregistre les handlers pour la recherche de trajets"""
    # Handler pour la recherche
    search_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("chercher", start_search),
            CallbackQueryHandler(start_search, pattern="^search_trip$")
        ],
        states={
            SELECTING_DEPARTURE: [
                CallbackQueryHandler(cancel_search, pattern="^cancel_search$"),
                # Autres handlers pour SELECTING_DEPARTURE
            ],
            SELECTING_ARRIVAL: [
                # Handlers pour SELECTING_ARRIVAL
            ],
            # ... autres états ...
        },
        fallbacks=[
            CommandHandler("cancel", cancel_search),
            CallbackQueryHandler(cancel_search, pattern="^cancel_search$")
        ],
        name="search_conversation",
        allow_reentry=True
    )
    
    application.add_handler(search_conv_handler)
    application.add_handler(CallbackQueryHandler(search_trips, pattern="^public:"))
