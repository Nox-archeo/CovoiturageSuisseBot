from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from utils.languages import TRANSLATIONS

async def handle_menu_buttons(update: Update, context):
    """Gère les clics sur les boutons du menu"""
    query = update.callback_query
    user_lang = context.user_data.get('language', 'fr')
    
    if query.data == "search_trip":
        keyboard = [
            [InlineKeyboardButton("🔍 Ville de départ", callback_data="set_departure")],
            [InlineKeyboardButton("📆 Date", callback_data="set_date")],
            [InlineKeyboardButton("🔄 Menu principal", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            "🔍 Recherche de trajets\n"
            "Choisissez une ville de départ:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "create_trip":
        keyboard = [
            [InlineKeyboardButton("➕ Nouveau trajet", callback_data="new_trip")],
            [InlineKeyboardButton("📋 Mes trajets proposés", callback_data="my_trips")],
            [InlineKeyboardButton("🔄 Menu principal", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            "🚗 Création de trajet\n"
            "Que souhaitez-vous faire?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "my_trips":
        keyboard = [
            [InlineKeyboardButton("🚗 Trajets conducteur", callback_data="driver_trips")],
            [InlineKeyboardButton("🧍 Trajets passager", callback_data="passenger_trips")],
            [InlineKeyboardButton("🔄 Menu principal", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            "📊 Mes trajets\n"
            "Sélectionnez une catégorie:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "profile":
        keyboard = [
            [
                InlineKeyboardButton("🚗 Mode conducteur", callback_data="driver_profile"),
                InlineKeyboardButton("🧍 Mode passager", callback_data="passenger_profile")
            ],
            [InlineKeyboardButton("⭐ Notes reçues", callback_data="my_ratings")],
            [InlineKeyboardButton("🔄 Menu principal", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            "👤 Mon profil\n"
            "Que souhaitez-vous consulter?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def register(application):
    """Enregistre les handlers du menu"""
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern='^(search_trip|create_trip|my_trips|profile|back_to_menu)'))
