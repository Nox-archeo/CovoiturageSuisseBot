from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database.models import Trip
from models.trip_preferences import Smoking, Music, TalkPreference, PetsAllowed, LuggageSize

SELECTING_PREF, ADDING_STOP, SETTING_TIME = range(3)

async def show_preferences_menu(update: Update, context):
    """Affiche le menu des préférences de trajet"""
    keyboard = [
        [
            InlineKeyboardButton("🚭 Non-fumeur", callback_data="pref_no_smoking"),
            InlineKeyboardButton("🚬 Fumeur", callback_data="pref_smoking")
        ],
        [
            InlineKeyboardButton("🔇 Calme", callback_data="pref_quiet"),
            InlineKeyboardButton("💬 Discussion", callback_data="pref_chatty")
        ],
        [
            InlineKeyboardButton("👩 Entre femmes", callback_data="pref_women_only"),
            InlineKeyboardButton("🐱 Animaux", callback_data="pref_pets")
        ],
        [
            InlineKeyboardButton("⏰ Horaire flexible", callback_data="pref_flex_time"),
            InlineKeyboardButton("🛄 Bagages", callback_data="pref_luggage")
        ],
        [InlineKeyboardButton("✅ Terminer", callback_data="pref_done")]
    ]
    
    await update.callback_query.message.edit_text(
        "🔧 Préférences du trajet\n"
        "Sélectionnez vos préférences:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_preference_choice(update: Update, context):
    """Gère le choix des préférences pour un trajet"""
    query = update.callback_query
    await query.answer()
    
    pref = query.data.replace("pref_", "")
    
    if pref == "done":
        return await finalize_trip_preferences(update, context)
        
    context.user_data.setdefault('trip_preferences', {})
    
    if pref == "no_smoking":
        context.user_data['trip_preferences']['smoking'] = Smoking.NO.value
    elif pref == "smoking":
        context.user_data['trip_preferences']['smoking'] = Smoking.YES.value
    elif pref == "quiet":
        context.user_data['trip_preferences']['talk'] = TalkPreference.QUIET.value
    elif pref == "chatty":
        context.user_data['trip_preferences']['talk'] = TalkPreference.CHATTY.value
    elif pref == "women_only":
        context.user_data['trip_preferences']['women_only'] = True
    
    # Mettre à jour l'affichage des préférences
    prefs_text = "Préférences sélectionnées:\n"
    for key, value in context.user_data['trip_preferences'].items():
        prefs_text += f"• {key}: {value}\n"
    
    await query.message.edit_text(
        prefs_text,
        reply_markup=query.message.reply_markup
    )

async def finalize_trip_preferences(update: Update, context):
    """Finalise les préférences du trajet"""
    # Sauvegarder les préférences dans la base de données
    # ...
    return await show_trip_summary(update, context)

# Fonction manquante nécessaire pour éviter une erreur
async def show_trip_summary(update: Update, context):
    """Affiche le résumé du trajet après avoir défini les préférences"""
    query = update.callback_query
    
    # Afficher un résumé des préférences
    prefs = context.user_data.get('trip_preferences', {})
    summary = "✅ Préférences enregistrées!\n\n"
    
    # Revenir à l'écran de confirmation du trajet
    # Cette fonction devrait normalement être liée à confirm_trip dans trip_handlers.py
    await query.edit_message_text(summary)
    return ConversationHandler.END

def register(application):
    """Enregistre les handlers de préférences"""
    # Handlers pour les préférences
    application.add_handler(CallbackQueryHandler(show_preferences_menu, pattern="^show_preferences$"))
    application.add_handler(CallbackQueryHandler(handle_preference_choice, pattern="^pref_"))
