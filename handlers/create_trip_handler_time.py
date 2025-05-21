#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/handlers/create_trip_handler_time.py
"""
Fonctions de sélection d'heures pour le module create_trip_handler
Complète les fonctionnalités de sélection d'horaires
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

async def create_hour_selection_keyboard():
    """Crée un clavier de sélection d'heure avec toutes les heures de la journée."""
    keyboard = []
    
    # Heures de la journée par blocs de 4
    for row_start in range(0, 24, 4):
        row = []
        for hour in range(row_start, min(row_start + 4, 24)):
            hour_str = f"{hour:02d}h"
            row.append(InlineKeyboardButton(hour_str, callback_data=f"create_hour:{hour}"))
        keyboard.append(row)
    
    # Options d'horaires flexibles
    keyboard.append([
        InlineKeyboardButton("🌅 Matin (6h-12h)", callback_data="create_flex_time:morning")
    ])
    keyboard.append([
        InlineKeyboardButton("☀️ Après-midi (12h-18h)", callback_data="create_flex_time:afternoon")
    ])
    keyboard.append([
        InlineKeyboardButton("🌙 Soirée (18h-23h)", callback_data="create_flex_time:evening")
    ])
    keyboard.append([
        InlineKeyboardButton("⏰ Heure à convenir", callback_data="create_flex_time:tbd")
    ])
    
    # Boutons de navigation et annulation
    keyboard.append([
        InlineKeyboardButton("🔙 Retour au calendrier", callback_data="create_back_to_calendar"),
        InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)

async def create_minute_selection_keyboard(hour):
    """Crée un clavier de sélection des minutes par tranches de 5 minutes."""
    keyboard = []
    
    # Minutes par tranches de 5, en blocs de 4
    minutes = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    for row_start in range(0, len(minutes), 4):
        row = []
        for minute in minutes[row_start:row_start+4]:
            minute_str = f"{minute:02d}"
            row.append(InlineKeyboardButton(
                minute_str, 
                callback_data=f"create_minute:{hour}:{minute}"
            ))
        keyboard.append(row)
    
    # Boutons de navigation
    keyboard.append([
        InlineKeyboardButton("🔙 Retour", callback_data="create_back_to_hour"),
        InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_hour_selection(update: Update, context: CallbackContext):
    """Gère la sélection de l'heure par bouton et passe à la sélection des minutes."""
    query = update.callback_query
    await query.answer()
    logger.info(f"[HOUR] Callback reçu: {query.data}")
    
    if query.data.startswith("create_hour:"):
        # Extraction de l'heure sélectionnée
        hour = int(query.data.split(":")[1])
        context.user_data['selected_hour'] = hour
        logger.info(f"[HOUR] Heure sélectionnée: {hour}")
        
        # Afficher les options de minutes
        minute_keyboard = await create_minute_selection_keyboard(hour)
        await query.edit_message_text(
            f"⏱️ Veuillez sélectionner les minutes:",
            reply_markup=minute_keyboard
        )
        
        return "CREATE_MINUTE"
    
    elif query.data == "create_back_to_calendar":
        # Retour au calendrier
        selected_date = context.user_data.get('selected_date', datetime.now())
        month = selected_date.month
        year = selected_date.year
        
        from handlers.create_trip_handler import create_calendar_markup
        
        markup = await create_calendar_markup(year, month)
        await query.edit_message_text(
            "📅 Sélectionnez la date du trajet:",
            reply_markup=markup
        )
        return "CREATE_CALENDAR"
    
    # Fallback
    await query.edit_message_text(
        "❌ Action non reconnue. Veuillez réessayer.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Réessayer", callback_data="create_trip:calendar_retry")
        ]])
    )
    return "CREATE_TIME"

async def handle_minute_selection_callback(update: Update, context: CallbackContext):
    """Gère la sélection des minutes par bouton et finalise la date/heure."""
    query = update.callback_query
    await query.answer()
    logger.info(f"[MINUTE] Callback reçu: {query.data}")
    
    if query.data.startswith("create_minute:"):
        # Extraction de l'heure et des minutes
        parts = query.data.split(":")
        if len(parts) != 3:
            logger.error(f"[MINUTE] Format callback invalide: {query.data}")
            await query.edit_message_text("❌ Erreur: Format invalide.")
            return "CREATE_CALENDAR"
            
        hour = int(parts[1])
        minute = int(parts[2])
        
        # Récupérer la date précédemment sélectionnée
        selected_date = context.user_data.get('selected_date')
        if not selected_date:
            logger.error("[MINUTE] Date non trouvée dans le contexte")
            await query.edit_message_text("❌ Erreur: Date non définie.")
            return "CREATE_CALENDAR"
        
        # Créer l'objet datetime complet
        selected_datetime = selected_date.replace(hour=hour, minute=minute)
        context.user_data['selected_datetime'] = selected_datetime
        context.user_data['date'] = selected_datetime.strftime('%d/%m/%Y %H:%M')
        context.user_data['datetime_obj'] = selected_datetime
        
        # Récupération des données de trajet pour le récapitulatif
        departure = context.user_data.get('departure', {})
        arrival = context.user_data.get('arrival', {})
        departure_display = departure.get('name', str(departure)) if departure else 'N/A'
        arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
        
        # Afficher la date/heure sélectionnée avec confirmation
        await query.edit_message_text(
            f"📅 Date et heure sélectionnées: {selected_datetime.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Récapitulatif:\n"
            f"De: {departure_display}\n"
            f"À: {arrival_display}\n\n"
            "Étape 6️⃣ - Combien de places disponibles? (1-8)"
        )
        
        return "CREATE_SEATS"
    
    elif query.data == "create_back_to_hour":
        # Retour à la sélection de l'heure
        hour_keyboard = await create_hour_selection_keyboard()
        await query.edit_message_text(
            "⏰ Veuillez sélectionner l'heure du trajet:",
            reply_markup=hour_keyboard
        )
        return "CREATE_TIME"
    
    # Fallback
    await query.edit_message_text(
        "❌ Action non reconnue. Veuillez réessayer.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Réessayer", callback_data="create_trip:calendar_retry")
        ]])
    )
    return "CREATE_MINUTE"

async def handle_flex_time_selection(update: Update, context: CallbackContext):
    """Gère la sélection d'horaires vagues (matin, après-midi, etc.)"""
    query = update.callback_query
    await query.answer()
    logger.info(f"[FLEX_TIME] Callback reçu: {query.data}")
    
    if query.data.startswith("create_flex_time:"):
        # Extraire l'option d'horaire flexible
        time_option = query.data.split(":")[1]
        
        # Définir les plages d'heures correspondant aux options
        time_ranges = {
            "morning": "Matinée (6h-12h)",
            "afternoon": "Après-midi (12h-18h)",
            "evening": "Soirée (18h-23h)",
            "tbd": "Heure à convenir"
        }
        
        # Stocker l'option d'horaire flexible
        flex_time_display = time_ranges.get(time_option, "Horaire flexible")
        context.user_data['flex_time'] = time_option
        context.user_data['flex_time_display'] = flex_time_display
        
        # Créer un datetime représentatif pour la BDD
        selected_date = context.user_data.get('selected_date')
        if not selected_date:
            logger.error("[FLEX_TIME] Date non trouvée dans le contexte")
            await query.edit_message_text("❌ Erreur: Date non définie.")
            return "CREATE_CALENDAR"
        
        # Assignation d'une heure représentative pour la plage horaire
        if time_option == "morning":
            hour, minute = 9, 0
        elif time_option == "afternoon":
            hour, minute = 14, 0
        elif time_option == "evening":
            hour, minute = 20, 0
        else:  # tbd - à convenir
            hour, minute = 12, 0
        
        # Stocker le datetime et le marquer comme flexible
        selected_datetime = selected_date.replace(hour=hour, minute=minute)
        context.user_data['selected_datetime'] = selected_datetime
        context.user_data['date'] = f"{selected_date.strftime('%d/%m/%Y')} ({flex_time_display})"
        context.user_data['datetime_obj'] = selected_datetime
        context.user_data['is_flex_time'] = True
        
        # Récupération des données de trajet pour le récapitulatif
        departure = context.user_data.get('departure', {})
        arrival = context.user_data.get('arrival', {})
        departure_display = departure.get('name', str(departure)) if departure else 'N/A'
        arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
        
        # Afficher la date/heure sélectionnée
        await query.edit_message_text(
            f"📅 Date sélectionnée: {selected_date.strftime('%d/%m/%Y')}\n"
            f"⏰ Horaire: {flex_time_display}\n\n"
            f"Récapitulatif:\n"
            f"De: {departure_display}\n"
            f"À: {arrival_display}\n\n"
            "Étape 6️⃣ - Combien de places disponibles? (1-8)"
        )
        
        return "CREATE_SEATS"
    
    # Fallback
    await query.edit_message_text(
        "❌ Action non reconnue. Veuillez réessayer.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Réessayer", callback_data="create_trip:calendar_retry")
        ]])
    )
    return "FLEX_HOUR"
