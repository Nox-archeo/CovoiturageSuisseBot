#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/utils/location_picker.py
"""
Module de sélection de localité pour le bot CovoiturageSuisse.
Implémente un sélecteur interactif de villes.
"""
import logging
import re
from typing import List, Dict, Tuple, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, filters
from utils.swiss_cities import load_localities, find_locality, format_locality_result

logger = logging.getLogger(__name__)

# Charger les localités
SWISS_LOCALITIES = load_localities()

def search_cities(query: str, max_results: int = 5) -> List[Tuple[str, Dict]]:
    """
    Recherche des villes correspondant à la requête.
    
    Args:
        query: La requête de recherche (nom ou NPA)
        max_results: Nombre maximum de résultats à retourner
        
    Returns:
        Liste des villes trouvées (nom, données)
    """
    results = []
    
    # Vérifier si la requête est un code postal
    is_zip = re.match(r'^\d{4}$', query.strip())
    
    if is_zip:
        # Recherche par NPA
        for name, data in SWISS_LOCALITIES.items():
            if data.get('zip') == query.strip():
                results.append((name, data))
                if len(results) >= max_results:
                    break
    
    # Si pas assez de résultats par NPA, rechercher par nom
    if len(results) < max_results:
        # Préparer la requête pour recherche insensible à la casse
        query_lower = query.lower()
        
        for name, data in SWISS_LOCALITIES.items():
            if query_lower in name.lower():
                # Éviter les doublons
                if not any(name == existing[0] for existing in results):
                    results.append((name, data))
                    if len(results) >= max_results:
                        break
    
    return results

def get_location_keyboard(results: List[Tuple[str, Dict]], action: str) -> InlineKeyboardMarkup:
    """
    Crée un clavier avec les résultats de recherche de localités.
    
    Args:
        results: Liste des résultats (nom, données)
        action: Préfixe de l'action pour les callback_data (ex: "departure" ou "arrival")
        
    Returns:
        Clavier InlineKeyboardMarkup avec les résultats
    """
    keyboard = []
    
    # Ajouter un bouton pour chaque résultat
    for name, data in results:
        # Afficher le nom et le NPA
        button_text = f"{name} ({data.get('zip', 'N/A')})"
        callback_data = f"{action}:{name}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Bouton pour rechercher à nouveau
    keyboard.append([InlineKeyboardButton("🔍 Nouvelle recherche", callback_data=f"{action}:search")])
    
    # Bouton pour annuler
    keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data=f"{action}:cancel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_popular_cities_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    Crée un clavier avec les villes populaires.
    
    Args:
        action: Préfixe de l'action pour les callback_data (ex: "departure" ou "arrival")
        
    Returns:
        Clavier InlineKeyboardMarkup avec les villes populaires
    """
    popular_cities = [
        "Zürich", "Genève", "Bâle", "Lausanne", "Berne", 
        "Lucerne", "Fribourg", "Neuchâtel", "Sion"
    ]
    
    keyboard = []
    for i in range(0, len(popular_cities), 3):
        row = []
        for city in popular_cities[i:i+3]:
            row.append(InlineKeyboardButton(city, callback_data=f"{action}:{city}"))
        keyboard.append(row)
    
    # Bouton pour recherche personnalisée
    keyboard.append([InlineKeyboardButton("🔍 Autre ville...", callback_data=f"{action}:search")])
    
    # Bouton pour annuler
    keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data=f"{action}:cancel")])
    
    return InlineKeyboardMarkup(keyboard)

async def start_location_selection(update: Update, context: CallbackContext, action: str, message_text: str):
    """
    Lance le processus de sélection de localité.
    
    Args:
        update: Update Telegram
        context: Contexte de la conversation
        action: Préfixe de l'action pour les callback_data (ex: "departure" ou "arrival")
        message_text: Texte à afficher dans le message
    
    Returns:
        Prochain état de la conversation ("ENTERING_LOCATION")
    """
    keyboard = get_popular_cities_keyboard(action)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=keyboard
        )
    
    # Sauvegarder l'action pour pouvoir l'utiliser dans le handler de message
    context.user_data['location_action'] = action
    
    return "ENTERING_LOCATION"

async def handle_location_selection(update: Update, context: CallbackContext, next_state: str):
    """
    Gère la sélection d'une localité dans le clavier.
    
    Args:
        update: Update Telegram
        context: Contexte de la conversation
        next_state: État suivant dans la conversation
    
    Returns:
        Prochain état de la conversation
    """
    query = update.callback_query
    await query.answer()
    
    # Extraire action et valeur
    action, value = query.data.split(':', 1)
    
    if value == "search":
        # L'utilisateur veut faire une recherche personnalisée
        await query.edit_message_text(
            "🏙️ Entrez le nom de la ville ou le code postal (NPA):"
        )
        # Sauvegarder l'action pour l'utiliser ensuite
        context.user_data['location_action'] = action
        return "SEARCHING_LOCATION"
    
    elif value == "cancel":
        # L'utilisateur annule
        await query.edit_message_text("❌ Sélection de localité annulée.")
        return "CANCEL"
    
    else:
        # L'utilisateur a sélectionné une ville
        city_name = value
        
        # Stocker la ville sélectionnée dans context.user_data
        context.user_data[action] = city_name
        
        # Message de confirmation
        action_text = "de départ" if action == "departure" else "d'arrivée" if action == "arrival" else ""
        await query.edit_message_text(f"✅ Ville {action_text} sélectionnée: *{city_name}*", parse_mode="Markdown")
        
        # Passer à l'étape suivante
        return next_state

async def handle_location_query(update: Update, context: CallbackContext):
    """
    Gère la recherche de localité lorsque l'utilisateur entre un texte.
    
    Args:
        update: Update Telegram
        context: Contexte de la conversation
    
    Returns:
        Prochain état de la conversation
    """
    query_text = update.message.text.strip()
    action = context.user_data.get('location_action', 'location')
    
    # Rechercher les villes correspondantes
    results = search_cities(query_text)
    
    if not results:
        # Aucun résultat trouvé
        await update.message.reply_text(
            "❌ Aucune ville trouvée. Veuillez réessayer avec un autre nom ou code postal."
        )
        return "SEARCHING_LOCATION"
    
    # Afficher les résultats sous forme de boutons
    keyboard = get_location_keyboard(results, action)
    
    await update.message.reply_text(
        "🏙️ Sélectionnez une ville parmi les résultats:",
        reply_markup=keyboard
    )
    
    return "SELECTING_FROM_RESULTS"

# Ne pas définir directement des handlers ici, ils doivent être créés par le module qui les utilise
# Définition des patterns regex pour les handlers
LOCATION_SELECTION_PATTERN = r"^(departure|arrival):.+$"

# Documentation pour aider à la création des handlers
"""
Pour utiliser les fonctions de ce module dans un ConversationHandler:

location_handlers = {
    "ENTERING_LOCATION": [
        CallbackQueryHandler(
            lambda u, c: handle_location_selection(u, c, "NEXT_STATE"), 
            pattern=LOCATION_SELECTION_PATTERN
        )
    ],
    "SEARCHING_LOCATION": [
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_query)
    ],
    "SELECTING_FROM_RESULTS": [
        CallbackQueryHandler(
            lambda u, c: handle_location_selection(u, c, "NEXT_STATE"), 
            pattern=LOCATION_SELECTION_PATTERN
        )
    ]
}
"""
