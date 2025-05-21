#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/handlers/preferences/trip_preferences_handler.py
"""
Handler pour les préférences de trajet.
Permet aux utilisateurs de définir leurs préférences pour un trajet.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler

logger = logging.getLogger(__name__)

# Définir les préférences possibles
PREFERENCES = {
    "smoking": {
        "name": "Fumeur",
        "options": [
            {"id": "no_smoking", "label": "🚭 Non-fumeur"},
            {"id": "smoking_outside", "label": "🚬 Pauses cigarette"},
            {"id": "smoking_allowed", "label": "🚬 Fumeur autorisé"}
        ]
    },
    "music": {
        "name": "Musique",
        "options": [
            {"id": "no_music", "label": "🔇 Pas de musique"},
            {"id": "music_low", "label": "🔈 Musique douce"},
            {"id": "music_ok", "label": "🔊 Musique ok"}
        ]
    },
    "talk_preference": {
        "name": "Conversation",
        "options": [
            {"id": "quiet", "label": "😶 Je préfère le silence"},
            {"id": "depends", "label": "😐 Selon l'humeur"},
            {"id": "chatty", "label": "😃 J'aime discuter"}
        ]
    },
    "pets_allowed": {
        "name": "Animaux",
        "options": [
            {"id": "no_pets", "label": "🐾 Pas d'animaux"},
            {"id": "small_pets", "label": "🐱 Petits animaux ok"},
            {"id": "all_pets", "label": "🐕 Tous animaux ok"}
        ]
    },
    "luggage_size": {
        "name": "Bagages",
        "options": [
            {"id": "small", "label": "👜 Petit sac"},
            {"id": "medium", "label": "🎒 Valise moyenne"},
            {"id": "large", "label": "🧳 Grosse valise"}
        ]
    }
}

async def show_preferences_menu(update: Update, context: CallbackContext):
    """Affiche le menu des préférences de trajet"""
    query = update.callback_query
    if query:
        await query.answer()
    
    # Créer les boutons pour chaque catégorie de préférence
    keyboard = []
    for pref_id, pref_data in PREFERENCES.items():
        # Vérifier si cette préférence est déjà définie
        current_value = context.user_data.get('trip_preferences', {}).get(pref_id)
        current_label = ""
        
        if current_value:
            for option in pref_data["options"]:
                if option["id"] == current_value:
                    current_label = f": {option['label'].split(' ', 1)[0]}"
                    break
        
        keyboard.append([
            InlineKeyboardButton(
                f"{pref_data['name']}{current_label}", 
                callback_data=f"pref:{pref_id}"
            )
        ])
    
    # Boutons de sauvegarde et d'annulation
    keyboard.append([
        InlineKeyboardButton("✅ Enregistrer", callback_data="pref:save"),
        InlineKeyboardButton("❌ Annuler", callback_data="pref:cancel")
    ])
    
    # Afficher le message avec les boutons
    message_text = (
        "🔧 *Préférences pour ce trajet*\n\n"
        "Ces préférences seront visibles par les autres utilisateurs.\n"
        "Sélectionnez une option dans chaque catégorie:"
    )
    
    if query:
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    return "CHOOSING_PREFERENCE"

async def show_preference_options(update: Update, context: CallbackContext):
    """Affiche les options pour une préférence spécifique"""
    query = update.callback_query
    await query.answer()
    
    # Récupérer l'ID de la préférence
    _, pref_id = query.data.split(':', 1)
    
    # Vérifier si la préférence existe
    if pref_id not in PREFERENCES:
        await query.edit_message_text("❌ Préférence non valide.")
        return "CHOOSING_PREFERENCE"
    
    # Récupérer les données de la préférence
    pref_data = PREFERENCES[pref_id]
    
    # Créer les boutons pour chaque option
    keyboard = []
    for option in pref_data["options"]:
        keyboard.append([
            InlineKeyboardButton(
                option["label"], 
                callback_data=f"option:{pref_id}:{option['id']}"
            )
        ])
    
    # Bouton pour revenir au menu des préférences
    keyboard.append([
        InlineKeyboardButton("🔙 Retour", callback_data="option:back")
    ])
    
    # Afficher le message avec les options
    await query.edit_message_text(
        f"🔧 {pref_data['name']}\n\n"
        f"Choisissez votre préférence:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return "SELECTING_OPTION"

async def handle_option_selection(update: Update, context: CallbackContext):
    """Gère la sélection d'une option de préférence"""
    query = update.callback_query
    await query.answer()
    
    # Récupérer les données du callback
    parts = query.data.split(':', 2)
    
    if len(parts) == 2 and parts[1] == "back":
        # L'utilisateur veut revenir au menu des préférences
        return await show_preferences_menu(update, context)
    
    if len(parts) != 3:
        # Format de données invalide
        await query.edit_message_text("❌ Option non valide.")
        return "CHOOSING_PREFERENCE"
    
    _, pref_id, option_id = parts
    
    # Initialiser le dictionnaire des préférences si nécessaire
    if 'trip_preferences' not in context.user_data:
        context.user_data['trip_preferences'] = {}
    
    # Sauvegarder l'option sélectionnée
    context.user_data['trip_preferences'][pref_id] = option_id
    
    # Revenir au menu des préférences
    return await show_preferences_menu(update, context)

async def handle_preferences_action(update: Update, context: CallbackContext, next_state=None):
    """Gère les actions de sauvegarde ou d'annulation des préférences"""
    query = update.callback_query
    await query.answer()
    
    # Récupérer l'action
    _, action = query.data.split(':', 1)
    
    if action == "save":
        # Sauvegarder les préférences dans la base de données
        preferences = context.user_data.get('trip_preferences', {})
        
        # Message de confirmation
        pref_text = "\n".join([
            f"✓ {PREFERENCES[pref_id]['name']}: {next(option['label'] for option in PREFERENCES[pref_id]['options'] if option['id'] == option_id)}"
            for pref_id, option_id in preferences.items()
        ])
        
        await query.edit_message_text(
            f"✅ *Préférences enregistrées*\n\n{pref_text}",
            parse_mode="Markdown"
        )
        
        # Passer à l'état suivant
        return next_state
    
    elif action == "cancel":
        # Annuler les modifications
        await query.edit_message_text("❌ Modification des préférences annulée.")
        
        # Si next_state est fourni, y retourner, sinon retourner à "CANCEL"
        return next_state if next_state else "CANCEL"
    
    else:
        # Action non reconnue
        await query.edit_message_text("❌ Action non valide.")
        return "CANCEL"

# Ces fonctions peuvent être référencées dans vos ConversationHandler
preference_handlers = {
    "CHOOSING_PREFERENCE": [
        CallbackQueryHandler(show_preference_options, pattern=r"^pref:[a-z_]+$"),
        CallbackQueryHandler(
            lambda u, c: handle_preferences_action(u, c, "NEXT_STATE"), 
            pattern=r"^pref:(save|cancel)$"
        )
    ],
    "SELECTING_OPTION": [
        CallbackQueryHandler(handle_option_selection, pattern=r"^option:.+$")
    ]
}

def register(application):
    """Enregistre les handlers pour les préférences de trajet"""
    logger.info("Enregistrement des handlers de préférences de trajet")
    
    # Si vous avez des handlers spécifiques à enregistrer en dehors des ConversationHandlers, faites-le ici
    pass
