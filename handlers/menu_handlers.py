from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler, 
    CommandHandler, 
    CallbackContext, 
    ConversationHandler, 
    MessageHandler, 
    filters,
    ContextTypes
)
from utils.languages import TRANSLATIONS
from database.models import User
from database import get_db

import logging
from handlers.create_trip_handler import start_create_trip as enter_create_trip_flow
from handlers.search_trip_handler import start_search_trip as enter_search_trip_flow
# Utiliser le nouveau gestionnaire de profil
from handlers.profile_handler import profile_handler

logger = logging.getLogger(__name__)

# States for driver availability conversation
DRIVER_OPTION, DRIVER_AVAILABILITY, DRIVER_AVAIL_TIME, DRIVER_AVAIL_SEATS, DRIVER_AVAIL_DEST, DRIVER_AVAIL_DEST_CITY, CONFIRM_AVAILABILITY = range(7)

# Fonction factice pour résoudre le problème de vérification dans start_fixed_bot.py
# La vraie fonction sera importée dynamiquement dans handle_menu_selection
async def list_my_trips(update, context):
    """Fonction factice qui sera remplacée par l'import dynamique"""
    # Import dynamique pour éviter les imports circulaires
    from handlers.trip_handlers import list_my_trips as real_list_my_trips
    return await real_list_my_trips(update, context)

# Fonction pour annuler une conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule la conversation en cours"""
    # Cas 1: Annulation via un callback
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Opération annulée.")
    # Cas 2: Annulation via une commande
    elif update.message:
        await update.message.reply_text("❌ Opération annulée.")
    
    # Nettoyer les données utilisateur
    context.user_data.clear()
    return ConversationHandler.END

async def start_command(update: Update, context: CallbackContext):
    """Commande /start améliorée avec plus d'explications et d'aide"""
    keyboard = [
        [
            InlineKeyboardButton("🚗 Créer un trajet", callback_data="menu:create"),
            InlineKeyboardButton("🔍 Chercher un trajet", callback_data="menu:search_trip")
        ],
        [
            InlineKeyboardButton("📋 Mes trajets", callback_data="menu:my_trips"),
            InlineKeyboardButton("👤 Mon profil", callback_data="menu:profile")
        ],
        [
            InlineKeyboardButton("❓ Aide", callback_data="menu:help")
        ]
    ]
    
    welcome_text = (
        "👋 *Bienvenue sur CovoiturageSuisse!*\n\n"
        "Cette application vous permet de trouver ou proposer des trajets "
        "en covoiturage partout en Suisse.\n\n"
        "Que souhaitez-vous faire?"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END # End any previous conversation if user hits /start

async def handle_menu_buttons(update: Update, context: CallbackContext):
    """Gère les clics sur les boutons du menu principal."""
    query = update.callback_query
    await query.answer()
    
    # Ajouter un log pour voir quel callback est intercepté
    logger.info(f"Menu handler intercepted callback: {query.data}")
    
    # Ne pas intercepter les callbacks du profil ou menu:profile
    if query.data.startswith("profile:") or query.data == "menu:profile":
        logger.info(f"Menu handler: Ignorer le callback de profil: {query.data}")
        # Assurez-vous que le callback n'est pas géré par ce handler
        return ConversationHandler.END
    
    # Vérifier si c'est un callback de calendrier, le menu handler ne devrait pas les intercepter
    if query.data.startswith("create_cal_") or query.data.startswith("calendar:"):
        logger.info(f"Menu handler: Ignorer le callback de calendrier: {query.data}")
        return  # Laissez-le être géré par le gestionnaire de calendrier approprié
    
    action = query.data.split(":")[1] if ":" in query.data else query.data # e.g., "menu:create_trip" -> "create_trip"

    logger.info(f"Menu button clicked: {action}")

    if action == "create" or action == "create_trip" or action == "creer_trajet":
        # This should call the entry point of the create_trip_conv_handler
        logger.info("Redirecting to create trip flow")
        return await enter_create_trip_flow(update, context)
    
    elif action == "search_trip" or action == "rechercher":
        # This should call the entry point of the search_trip_conv_handler
        return await enter_search_trip_flow(update, context)

    elif action == "my_trips":
        # Import dynamically or ensure it's available
        from handlers.trip_handlers import list_my_trips_menu # Assuming a function that shows trip categories
        return await list_my_trips_menu(update, context)
        
    elif action == "profile":
        # Utiliser le nouveau gestionnaire de profil
        logger.info("Button profile clicked, redirecting to profile_handler")
        try:
            return await profile_handler(update, context)
        except Exception as e:
            logger.error(f"Error in profile_handler: {str(e)}", exc_info=True)
            await query.edit_message_text("Une erreur s'est produite lors de l'affichage du profil. Veuillez réessayer.")
            return ConversationHandler.END

    elif action == "help":
        from handlers.help_handlers import help_guide # Assuming help_guide function
        return await help_guide(update, context)
    
    elif query.data == "back_to_menu":
        # This is a common callback, ensure start_command handles callback_query
        return await start_command(update, context)

    # ... (handle other specific menu actions like public:driver_trips if not covered by sub-menus)
    
    # If an action leads to a conversation, it should return the first state of that conversation.
    # If it's a one-off action, it might return ConversationHandler.END or nothing if not in a conversation.
    # For now, assume menu buttons either start a new conversation (handled by their respective handlers) or display info.
    return # Or an appropriate state if this itself is part of a simple menu conversation

# ... (handle_role_choice, handle_driver_option, etc. for driver availability) ...
# These functions should be part of the availability_conv_handler
async def handle_role_choice(update: Update, context: CallbackContext):
    """Gère le choix entre conducteur et passager pour disponibilité (example flow)."""
    query = update.callback_query
    await query.answer()
    
    # Example: This could be an entry point if 'menu:availability' was clicked
    # For now, this function is kept as an example; integrate it if you have a "declare availability" button
    # _, role = query.data.split(":", 1)
    # context.user_data['user_role'] = role
    # if role == "driver":
    #    # ...
    #    return DRIVER_OPTION
    await query.edit_message_text("Déclaration de disponibilité en cours de développement.")
    return ConversationHandler.END


# Placeholder for cancel function if not already globally available
async def cancel_conversation(update: Update, context: CallbackContext):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Opération annulée.")
    else:
        await update.message.reply_text("Opération annulée.")
    context.user_data.clear()
    return ConversationHandler.END

# Example ConversationHandler for driver availability (if you implement this flow)
# availability_conv_handler = ConversationHandler(
# entry_points=[CallbackQueryHandler(handle_role_choice, pattern='^role:(driver|passenger)$')],
# states={
# DRIVER_OPTION: [CallbackQueryHandler(handle_driver_option, pattern='^driver_option:(specific|available)$')],
# DRIVER_AVAILABILITY: [
# CallbackQueryHandler(handle_driver_availability, pattern='^avail_from_'),
# CallbackQueryHandler(handle_driver_availability, pattern='^avail_other_city$'),
# MessageHandler(filters.TEXT & ~filters.COMMAND, handle_driver_availability)
# ],
#         # ... other states ...
#     },
# fallbacks=[CallbackQueryHandler(cancel_conversation, pattern='^cancel_trip$')]
# )

def register(application):
    application.add_handler(CommandHandler("start", start_command))
    # General handler for menu callbacks that don't start a new major conversation
    # N'interceptez que des motifs très spécifiques pour éviter les conflits avec d'autres handlers
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:(?!profile$).*"))  # Exclure menu:profile
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^back_to_menu$"))
    # Ajoutez les callbacks spécifiques pour les boutons de menu principaux
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^creer_trajet$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^rechercher$"))
    # Ne pas gérer "profil" ici car il est géré par profile_handler
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^mes_trajets$"))


    # Add other handlers specific to menu_handlers.py, like the availability_conv_handler if used
    # application.add_handler(availability_conv_handler)

    # Handler for public trip listings if not part of search_handler
    # application.add_handler(CallbackQueryHandler(handle_public_trips, pattern="^public:"))
    logger.info("Menu handlers registered.")
