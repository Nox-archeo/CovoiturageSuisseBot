from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler, CommandHandler, CallbackContext, 
    ConversationHandler, MessageHandler, filters
)
from database.models import User # Assuming User model
from database import get_db      # Assuming get_db function

import logging
logger = logging.getLogger(__name__)

# States for profile conversation
PROFILE_CHOOSING, TYPING_PHONE, EDIT_VEHICLE, VIEW_RATINGS = range(4) # Example states

async def profile_menu(update: Update, context: CallbackContext):
    """Shows the main profile menu."""
    query = update.callback_query
    if query:
        await query.answer()

    user_id = update.effective_user.id
    # db = get_db()
    # user = db.query(User).filter(User.telegram_id == user_id).first()
    # if not user:
    #     # Handle user not found, perhaps create one or ask to /start
    #     text = "Veuillez d'abord utiliser /start pour initialiser votre profil."
    #     if query: await query.edit_message_text(text)
    #     else: await update.message.reply_text(text)
    #     return ConversationHandler.END

    keyboard = [
        # [InlineKeyboardButton(f"{'✅' if user.is_driver else '☑️'} Mode Conducteur", callback_data="profile:set_driver")],
        # [InlineKeyboardButton(f"{'✅' if user.is_passenger else '☑️'} Mode Passager", callback_data="profile:set_passenger")],
        [InlineKeyboardButton("📱 Gérer Téléphone", callback_data="profile:phone")],
        [InlineKeyboardButton("🚗 Gérer Véhicule", callback_data="profile:vehicle")], # Example
        [InlineKeyboardButton("⭐ Mes Évaluations", callback_data="profile:ratings")], # Example
        [InlineKeyboardButton("⬅️ Retour au menu", callback_data="menu:back_to_menu")] # Consistent back
    ]
    
    text = "👤 *Mon Profil*\n\nQue souhaitez-vous faire?"
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return PROFILE_CHOOSING

async def handle_profile_choice(update: Update, context: CallbackContext):
    """Handles choices from the profile menu."""
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":")[1] # e.g., "profile:phone" -> "phone"

    db = get_db()
    user = db.query(User).filter(User.telegram_id == query.from_user.id).first()
    if not user: # Should ideally be handled by an earlier check or user creation
        await query.edit_message_text("Utilisateur non trouvé. Veuillez réessayer /start.")
        return ConversationHandler.END

    if choice == "set_driver":
        user.is_driver = not getattr(user, 'is_driver', False) # Toggle
        db.commit()
        await query.edit_message_text(f"Mode conducteur {'activé' if user.is_driver else 'désactivé'}!")
        return await profile_menu(update, context) # Refresh menu

    elif choice == "set_passenger":
        user.is_passenger = not getattr(user, 'is_passenger', False) # Toggle
        db.commit()
        await query.edit_message_text(f"Mode passager {'activé' if user.is_passenger else 'désactivé'}!")
        return await profile_menu(update, context) # Refresh menu

    elif choice == "phone":
        await query.edit_message_text(
            "📱 Veuillez entrer votre numéro de téléphone (ex: +41791234567)\n"
            "Ou tapez /annuler pour revenir."
        )
        return TYPING_PHONE
    
    elif choice == "vehicle":
        # Placeholder for vehicle management
        await query.edit_message_text("Gestion du véhicule en développement.")
        return PROFILE_CHOOSING # Stay in menu

    elif choice == "ratings":
        # Placeholder for ratings view
        await query.edit_message_text("Consultation des évaluations en développement.")
        return PROFILE_CHOOSING # Stay in menu
        
    elif choice == "back_to_menu":
        # Import ici pour éviter les imports circulaires
        from handlers.menu_handlers import start_command as show_main_menu
        await show_main_menu(update, context)
        return ConversationHandler.END

    return PROFILE_CHOOSING # Default fallback within conversation

async def handle_phone_input(update: Update, context: CallbackContext):
    """Handles the phone number input."""
    phone_number = update.message.text
    # Add validation for phone_number here
    # ...
    db = get_db()
    user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
    if user:
        user.phone_number = phone_number # Save validated number
        db.commit()
        await update.message.reply_text(f"✅ Numéro de téléphone enregistré: {phone_number}")
    else:
        await update.message.reply_text("Erreur: utilisateur non trouvé.")

    # Go back to profile menu
    await profile_menu(update, context)
    return PROFILE_CHOOSING


async def cancel_profile_conversation(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("Modification du profil annulée.")
    else:
        await update.message.reply_text("Modification du profil annulée.")
    
    # Go back to main menu
    from handlers.menu_handlers import start_command as show_main_menu
    await show_main_menu(update, context)
    return ConversationHandler.END

profile_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(profile_menu, pattern="^menu:profile$"),
        CommandHandler("profile", profile_menu) # Allow direct command
    ],
    states={
        PROFILE_CHOOSING: [
            CallbackQueryHandler(handle_profile_choice, pattern="^profile:(set_driver|set_passenger|phone|vehicle|ratings)$"),
            CallbackQueryHandler(cancel_profile_conversation, pattern="^profile:cancel$"), # Specific cancel for profile
            CallbackQueryHandler(lambda u,c: __import__('handlers.menu_handlers').menu_handlers.handle_menu_buttons(u,c), pattern="^menu:back_to_menu$")

        ],
        TYPING_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input),
        ],
        # Define other states like EDIT_VEHICLE, VIEW_RATINGS and their handlers
    },
    fallbacks=[
        CommandHandler("cancel", cancel_profile_conversation),
        CallbackQueryHandler(cancel_profile_conversation, pattern="^profile:cancel$"),
        # Fallback for unexpected input within this conversation
        MessageHandler(filters.ALL, lambda u, c: u.message.reply_text("Entrée non valide. Utilisez les boutons ou /cancel.") if u.message else c.bot.answer_callback_query(u.callback_query.id, "Action non valide.", show_alert=True) )
    ],
    map_to_parent={ # If called from a main menu conversation, how to return
        ConversationHandler.END: ConversationHandler.END # Or a specific state in parent
    },
    name="profile_conversation",  # Ajouté - c'est obligatoire pour persistent=True
    persistent=True,
    allow_reentry=True,
    per_message=False  # Changé - évite les warnings
)

def register(application):
    application.add_handler(profile_conv_handler)
    logger.info("Profile handlers registered.")
