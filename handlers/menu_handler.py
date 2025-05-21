from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CallbackContext

async def handle_button(update: Update, context: CallbackContext):
    """Gère les clics sur les boutons du menu"""
    query = update.callback_query
    await query.answer()

    if query.data == "menu_principal":
        keyboard = [
            [
                InlineKeyboardButton("🔍 Rechercher", callback_data="rechercher"),
                InlineKeyboardButton("➕ Créer", callback_data="creer_trajet")
            ],
            [
                InlineKeyboardButton("👤 Mon Profil", callback_data="profil"),
                InlineKeyboardButton("🗂️ Mes Trajets", callback_data="mes_trajets")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏠 Menu Principal\n\n"
            "Que souhaitez-vous faire ?",
            reply_markup=reply_markup
        )

menu_handler = CallbackQueryHandler(handle_button, pattern="^menu_principal$")
