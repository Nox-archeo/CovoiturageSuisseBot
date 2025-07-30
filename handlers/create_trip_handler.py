#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/handlers/create_trip_handler_fixed.py
import logging
import json
import calendar
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from database.models import Trip, User
from database import get_db
from utils.validators import validate_date, validate_price, validate_seats
from utils.swiss_cities import find_locality, format_locality_result, load_localities as load_all_localities
from utils.date_picker import (
    start_date_selection, handle_calendar_navigation, 
    handle_day_selection, handle_time_selection, handle_minute_selection,
    handle_flex_time_selection, handle_datetime_action,
    CALENDAR_NAVIGATION_PATTERN, CALENDAR_DAY_SELECTION_PATTERN, 
    CALENDAR_CANCEL_PATTERN, TIME_SELECTION_PATTERN, TIME_BACK_PATTERN, TIME_CANCEL_PATTERN,
    MINUTE_SELECTION_PATTERN, MINUTE_BACK_PATTERN, MINUTE_CANCEL_PATTERN,
    FLEX_TIME_PATTERN, DATETIME_ACTION_PATTERN
)
import os
import json
import logging
from geopy.distance import geodesic

# Configuration du logger
logger = logging.getLogger(__name__)

# États de conversation pour la création de trajet
(
    CREATE_TRIP_TYPE,
    CREATE_TRIP_OPTIONS,
    CREATE_DEPARTURE,
    CREATE_ARRIVAL,
    CREATE_DATE,
    CREATE_SEATS,
    CREATE_PRICE,
    CREATE_CONFIRM,
    CREATE_CALENDAR, 
    CREATE_TIME,     
    CREATE_MINUTE,   
    CREATE_CONFIRM_DATETIME,
    FLEX_HOUR,
    HOUR,  # État pour la saisie de l'heure après la date
    # Nouveaux états pour trajets réguliers
    REGULAR_DAYS_SELECTION,
    REGULAR_CALENDAR_SELECTION,
    REGULAR_TIME_TYPE,  # Nouveau : choisir heure unique ou indépendante
    # Nouveaux états pour trajets aller-retour
    RETURN_DATE,  # Sélection de la date de retour
    RETURN_TIME,  # Sélection de l'heure de retour
    RETURN_CONFIRM_DATETIME  # Confirmation de la date/heure de retour
) = range(20)

# --- UTILS GPS pour calcul automatique du prix ---
CITIES_COORDS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'src', 'bot', 'data', 'cities.json'
)
def load_city_coords():
    with open(CITIES_COORDS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return { (c['name'], c.get('npa')): (c.get('lat'), c.get('lon')) for c in data['cities'] if 'lat' in c and 'lon' in c }

CITY_COORDS = load_city_coords()

def get_coords(city):
    name = city.get('name')
    npa = city.get('zip') or city.get('npa')
    # Recherche stricte puis souple
    return CITY_COORDS.get((name, npa)) or next((v for (n, z), v in CITY_COORDS.items() if n == name), (None, None))

def compute_price_auto(dep, arr):
    """Calcule automatiquement le prix et la distance entre deux villes"""
    from utils.swiss_cities import find_locality
    from utils.route_distance import get_route_distance_km
    
    # Rechercher les coordonnées des villes
    dep_results = find_locality(dep)
    arr_results = find_locality(arr)
    
    if not dep_results or not arr_results:
        return None, None
    
    dep_data = dep_results[0]
    arr_data = arr_results[0]
    
    # Calculer la distance avec notre nouveau système
    distance = get_route_distance_km(
        (dep_data['lat'], dep_data['lon']),
        (arr_data['lat'], arr_data['lon']),
        dep, arr
    )
    
    if not distance:
        return None, None
    
    # Barème de prix
    if 1 <= distance < 25:
        price = distance * 0.75
    elif 25 <= distance <= 40:
        price = distance * 0.5
    elif distance > 40:
        price = distance * 0.25
    else:
        price = 0
    
    return round(price, 2), round(distance, 1)

async def handle_hour_input(update: Update, context: CallbackContext):
    """Gère l'entrée manuelle de l'heure du trajet."""
    user_input = update.message.text.strip()
    
    try:
        # Vérifier si l'entrée contient des heures et minutes (format HH:MM)
        if ":" in user_input:
            hour_str, minute_str = user_input.split(":")
            hour = int(hour_str)
            minute = int(minute_str)
            
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                await update.message.reply_text("⚠️ Format d'heure invalide. Veuillez entrer une heure valide (ex: 13:30)")
                return HOUR
        else:
            # Si seulement l'heure est fournie
            hour = int(user_input)
            minute = 0
            
            if not (0 <= hour <= 23):
                await update.message.reply_text("⚠️ Format d'heure invalide. Veuillez entrer une heure valide (0-23)")
                return HOUR
        
        # Récupérer la date précédemment sélectionnée
        selected_date = context.user_data.get('selected_date')
        if not selected_date:
            await update.message.reply_text("❌ Erreur: Veuillez d'abord sélectionner une date.")
            return CREATE_CALENDAR
        
        # Créer l'objet datetime complet
        selected_datetime = selected_date.replace(hour=hour, minute=minute)
        context.user_data['selected_datetime'] = selected_datetime
        context.user_data['date'] = selected_datetime.strftime('%d/%m/%Y %H:%M')
        context.user_data['datetime_obj'] = selected_datetime
        
        # Passer directement à l'étape des sièges
        departure = context.user_data.get('departure', {})
        arrival = context.user_data.get('arrival', {})
        departure_display = departure.get('name', str(departure)) if departure else 'N/A'
        arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
        
        # Adapter le message selon le rôle
        trip_role = context.user_data.get('trip_type', 'driver')
        if trip_role == 'passenger':
            seats_message = "Étape 6️⃣ - Combien de places voulez-vous réserver? (1-4)"
        else:
            seats_message = "Étape 6️⃣ - Combien de places disponibles? (1-8)"
        
        await update.message.reply_text(
            f"📅 Date et heure sélectionnées: {selected_datetime.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Récapitulatif:\n"
            f"De: {departure_display}\n"
            f"À: {arrival_display}\n\n"
            f"{seats_message}"
        )
        
        return CREATE_SEATS
        
    except ValueError:
        await update.message.reply_text("⚠️ Format d'heure invalide. Veuillez entrer une heure au format HH:MM (ex: 13:30)")
        return HOUR

async def handle_manual_time_input(update: Update, context: CallbackContext):
    """Gère la saisie manuelle de l'heure."""
    time_text = update.message.text.strip()
    try:
        hour, minute = map(int, time_text.split(":"))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            selected_date = context.user_data.get('selected_date', datetime.now())
            selected_datetime = selected_date.replace(hour=hour, minute=minute)
            context.user_data['selected_datetime'] = selected_datetime
            await update.message.reply_text(
                f"Heure sélectionnée: {hour:02d}:{minute:02d}\n"
                f"Date et heure: {selected_datetime.strftime('%d/%m/%Y à %H:%M')}"
            )
            return CREATE_SEATS
        else:
            await update.message.reply_text("Heure invalide. Veuillez entrer une heure entre 00:00 et 23:59.")
            return CREATE_TIME
    except Exception:
        await update.message.reply_text("Format d'heure invalide. Utilisez le format HH:MM (ex: 13:30).")
        return CREATE_TIME

async def handle_minute_selection(update: Update, context: CallbackContext):
    """Gère la sélection des minutes."""
    query = update.callback_query
    await query.answer()
    logger.info(f"[MINUTE] Callback reçu: {query.data}")
    
    if query.data.startswith("create_minute:"):
        # Format create_minute:hour:minute
        parts = query.data.split(":")
        if len(parts) == 3:
            hour = int(parts[1])
            minute = int(parts[2])
        else:
            logger.error(f"[MINUTE] Format callback invalide: {query.data}")
            minute = 0
            hour = context.user_data.get('selected_hour', 0)
    else:
        # Ancien format minute:minute
        minute = int(query.data.split(":")[1])
        hour = context.user_data.get('selected_hour', 0)
    
    # Vérifier si c'est un trajet régulier
    regular_time_type = context.user_data.get('regular_time_type')
    regular_dates = context.user_data.get('regular_dates', [])
    
    if regular_time_type and regular_dates:
        # Trajet régulier
        departure = context.user_data.get('departure', {})
        arrival = context.user_data.get('arrival', {})
        departure_display = departure.get('name', str(departure)) if departure else 'N/A'
        arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
        
        if regular_time_type == 'same':
            # Même horaire pour toutes les dates
            time_str = f"{hour:02d}:{minute:02d}"
            
            # Créer les datetime objects pour toutes les dates
            context.user_data['regular_times'] = {}
            for date_str in regular_dates:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                full_datetime = date_obj.replace(hour=hour, minute=minute)
                context.user_data['regular_times'][date_str] = full_datetime.strftime('%d/%m/%Y %H:%M')
            
            # Adapter le message selon le rôle
            trip_role = context.user_data.get('trip_type', 'driver')
            if trip_role == 'passenger':
                seats_message = "Étape 6️⃣ - Combien de places voulez-vous réserver? (1-4)"
            else:
                seats_message = "Étape 6️⃣ - Combien de places disponibles? (1-8)"
            
            await query.edit_message_text(
                f"✅ **Horaire appliqué à tous les trajets**\n\n"
                f"De: {departure_display}\n"
                f"À: {arrival_display}\n"
                f"⏰ Heure: {time_str}\n"
                f"📊 {len(regular_dates)} trajet{'s' if len(regular_dates) > 1 else ''}\n\n"
                f"{seats_message}"
            )
            
            return CREATE_SEATS
            
        elif regular_time_type == 'individual':
            # Horaires individuels - sauvegarder pour la date actuelle
            current_date = context.user_data.get('current_regular_date')
            current_index = context.user_data.get('current_date_index', 0)
            
            if not context.user_data.get('regular_times'):
                context.user_data['regular_times'] = {}
            
            # Sauvegarder l'horaire pour cette date
            date_obj = datetime.strptime(current_date, '%Y-%m-%d')
            full_datetime = date_obj.replace(hour=hour, minute=minute)
            context.user_data['regular_times'][current_date] = full_datetime.strftime('%d/%m/%Y %H:%M')
            
            # Vérifier s'il y a d'autres dates
            next_index = current_index + 1
            if next_index < len(regular_dates):
                # Passer à la date suivante
                next_date = regular_dates[next_index]
                context.user_data['current_regular_date'] = next_date
                context.user_data['current_date_index'] = next_index
                
                date_display = datetime.strptime(next_date, '%Y-%m-%d').strftime('%A %d %B %Y')
                
                message_text = (
                    f"⏰ **Horaires individuels**\n\n"
                    f"De: {departure_display}\n"
                    f"À: {arrival_display}\n\n"
                    f"📅 **Date {next_index + 1}/{len(regular_dates)}:** {date_display}\n\n"
                    "Choisissez l'heure de départ pour cette date:"
                )
                
                # Afficher la sélection d'heure pour la date suivante
                hours_keyboard = []
                for hour_opt in range(6, 23):  # 6h à 22h
                    hours_keyboard.append([InlineKeyboardButton(f"{hour_opt:02d}:00", callback_data=f"create_hour:{hour_opt}")])
                
                await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(hours_keyboard))
                return CREATE_TIME
            else:
                # Toutes les dates ont été configurées - aller aux sièges
                # Adapter le message selon le rôle
                trip_role = context.user_data.get('trip_type', 'driver')
                if trip_role == 'passenger':
                    seats_message = "Étape 6️⃣ - Combien de places voulez-vous réserver? (1-4)"
                else:
                    seats_message = "Étape 6️⃣ - Combien de places disponibles? (1-8)"
                
                await query.edit_message_text(
                    f"✅ **Tous les horaires configurés**\n\n"
                    f"De: {departure_display}\n"
                    f"À: {arrival_display}\n"
                    f"📊 {len(regular_dates)} trajet{'s' if len(regular_dates) > 1 else ''} avec horaires individuels\n\n"
                    f"{seats_message}"
                )
                
                return CREATE_SEATS
    else:
        # Trajet simple - comportement normal
        selected_date = context.user_data.get('selected_date', datetime.now())
        selected_datetime = selected_date.replace(hour=hour, minute=minute)
        context.user_data['selected_datetime'] = selected_datetime
        
        # DEBUG: Ajouter des logs pour diagnostiquer le problème aller-retour
        is_selecting_return = context.user_data.get('selecting_return', False)
        trip_options = context.user_data.get('trip_options', {})
        is_round_trip = trip_options.get('round_trip', False)
        logger.debug(f"[MINUTE_SELECTION] is_selecting_return: {is_selecting_return}")
        logger.debug(f"[MINUTE_SELECTION] is_round_trip: {is_round_trip}")
        logger.debug(f"[MINUTE_SELECTION] user_data keys: {list(context.user_data.keys())}")
        
        # Vérifier si nous sommes dans un processus de sélection de retour
        if is_selecting_return:
            logger.debug("[MINUTE_SELECTION] IMPORTANT - Mode retour détecté, NE PAS écraser datetime_obj")
            # C'est la sélection de l'heure de retour - nettoyer le flag et appeler le handler de retour
            context.user_data['selecting_return'] = False
            logger.debug("[MINUTE_SELECTION] Redirection vers handle_return_date_confirmed")
            return await handle_return_date_confirmed(update, context)
        
        # SEULEMENT pour les trajets simples : stocker dans datetime_obj
        context.user_data['date'] = selected_datetime.strftime('%d/%m/%Y %H:%M')
        context.user_data['datetime_obj'] = selected_datetime
        logger.debug(f"[MINUTE_SELECTION] Trajet simple - datetime_obj stocké: {selected_datetime}")
        
        # Récupération des données de trajet pour le récapitulatif
        departure = context.user_data.get('departure', {})
        arrival = context.user_data.get('arrival', {})
        departure_display = departure.get('name', str(departure)) if departure else 'N/A'
        arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
        
        # Adapter le message selon le rôle
        trip_role = context.user_data.get('trip_type', 'driver')
        if trip_role == 'passenger':
            seats_message = "Étape 6️⃣ - Combien de places voulez-vous réserver? (1-4)"
        else:
            seats_message = "Étape 6️⃣ - Combien de places disponibles? (1-8)"
        
        await query.edit_message_text(
            f"📅 Date et heure sélectionnées: {selected_datetime.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Récapitulatif:\n"
            f"De: {departure_display}\n"
            f"À: {arrival_display}\n\n"
            f"{seats_message}"
        )
        
        return CREATE_SEATS

# Charger les villes au démarrage
def load_cities_list():
    """Charge les villes depuis swiss_localities.json pour les suggestions."""
    try:
        localities = load_all_localities() # from utils.swiss_cities
        if localities:
            logger.info(f"Chargé {len(localities)} localités pour create_trip_handler")
            return sorted(list(localities.keys())) 
        else:
            logger.warning("Aucune localité trouvée dans create_trip_handler, utilisation de la liste par défaut")
            # Fallback list
            return sorted(["Zürich", "Genève", "Bâle", "Lausanne", "Berne", "Lucerne", "Fribourg", "Neuchâtel", "Sion"])
    except Exception as e:
        logger.error(f"Erreur chargement des localités dans create_trip_handler: {e}")
        # Fallback list
        return sorted(["Zürich", "Genève", "Bâle", "Lausanne", "Berne", "Lucerne", "Fribourg", "Neuchâtel", "Sion"])

SWISS_CITIES_SUGGESTIONS = load_cities_list()

async def start_create_trip(update: Update, context: CallbackContext):
    """Lance le processus de création de trajet."""
    logger.info(f"🚀 DEBUG - start_create_trip appelé. Update type: {type(update)}")
    if update.callback_query:
        logger.info(f"🚀 DEBUG - Callback data: {update.callback_query.data}")
        logger.info(f"🚀 DEBUG - MESSAGE: Appelé par CALLBACK - ConversationHandler actif")
    else:
        logger.info(f"🚀 DEBUG - Pas de callback, c'est un message")
        logger.info(f"🚀 DEBUG - MESSAGE: Appelé par COMMANDE - ConversationHandler peut ne pas être actif")
    logger.info(f"🚀 DEBUG - User ID: {update.effective_user.id}")
    
    # Vérifier si l'utilisateur a un profil
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        # Utilisateur sans profil - rediriger vers la création
        keyboard = [
            [InlineKeyboardButton("✅ Créer mon profil", callback_data="menu:create_profile")],
            [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
        ]
        
        text = (
            "❌ *Profil requis*\n\n"
            "Vous devez créer un profil avant de pouvoir créer un trajet."
        )
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        db.close()
        return ConversationHandler.END
    
    db.close()
    
    context.user_data.clear()
    context.user_data['mode'] = 'create'
    context.user_data['current_state'] = CREATE_TRIP_TYPE # For fallback
    logger.info("Mode réglé sur 'create' dans start_create_trip")
    
    keyboard = [
        [
            InlineKeyboardButton("🚗 Je propose un trajet (conducteur)", callback_data="create_trip_type:driver"),
        ],
        [
            InlineKeyboardButton("🧍 Je cherche un trajet (passager)", callback_data="create_trip_type:passenger")
        ],
        [InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")]
    ]
    
    message_text = (
        "🚗 *Création d'un nouveau trajet*\n\n"
        "Étape 1️⃣ - Choisissez votre rôle :\n\n"
        "🚗 **Conducteur** : Vous proposez votre véhicule\n"
        "🧍 **Passager** : Vous recherchez un conducteur\n\n"
        "Sélectionnez votre rôle :"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
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
    logger.info("✅ Boutons Conducteur/Passager affichés")
    logger.info(f"🔄 RETOUR - start_create_trip retourne l'état: {CREATE_TRIP_TYPE}")
    return CREATE_TRIP_TYPE

async def handle_create_trip_type(update: Update, context: CallbackContext):
    """Gère le choix du type de trajet (conducteur/passager)."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Ajouter des logs détaillés pour débugger
        logger.info(f"🔍 DEBUG - Callback reçu: {query.data}")
        logger.info(f"🔍 DEBUG - User ID: {update.effective_user.id}")
        logger.info(f"🔍 DEBUG - Context user_data avant: {context.user_data}")
        
        # query.data will be "create_trip_type:driver" or "create_trip_type:passenger"
        choice = query.data.split(":")[1] 
        logger.info(f"✅ Callback reçu dans handle_create_trip_type: {query.data}, choix: {choice}")
            
        context.user_data['trip_type'] = choice
        logger.info(f"Type de trajet (création) enregistré: {choice}")
        logger.info(f"🔍 DEBUG - Context user_data après: {context.user_data}")
        
        context.user_data['current_state'] = CREATE_TRIP_OPTIONS
        return await show_create_trip_options(update, context) # show_create_trip_options should return CREATE_TRIP_OPTIONS
    except Exception as e:
        logger.error(f"❌ Erreur dans handle_create_trip_type: {e}", exc_info=True)
        await query.message.reply_text("Une erreur s'est produite. Veuillez réessayer.")
        return ConversationHandler.END

async def show_create_trip_options(update: Update, context: CallbackContext):
    """Affiche les options supplémentaires pour la création de trajet."""
    logger.info(f"Entrée dans show_create_trip_options avec update type: {type(update)}")
    query = update.callback_query if hasattr(update, 'callback_query') else None
    
    if 'trip_options' not in context.user_data:
        context.user_data['trip_options'] = {}
    
    keyboard_options = [
        [InlineKeyboardButton(f"{'🔴' if context.user_data['trip_options'].get('simple', False) else '🔘'} Trajet simple", callback_data="create_trip_option:simple")],
        [InlineKeyboardButton(f"{'🔴' if context.user_data['trip_options'].get('regular', False) else '🔘'} Trajet régulier", callback_data="create_trip_option:regular")],
        [InlineKeyboardButton(f"{'🔴' if context.user_data['trip_options'].get('round_trip', False) else '🔘'} Aller-retour", callback_data="create_trip_option:round_trip")]
        # Potentially "women_only" option here could be added separately with checkbox logic
    ]
    keyboard_options.append([
        InlineKeyboardButton("▶️ Continuer", callback_data="create_trip_options:continue"),
        InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel_options")
    ])
    
    role_text = "conducteur" if context.user_data.get('trip_type') == "driver" else "passager"
    
    # Vérifier quelle option est sélectionnée pour donner du feedback
    selected_options = []
    if context.user_data['trip_options'].get('simple', False):
        selected_options.append("Trajet simple")
    if context.user_data['trip_options'].get('regular', False):
        selected_options.append("Trajet régulier")
    if context.user_data['trip_options'].get('round_trip', False):
        selected_options.append("Aller-retour")
    
    selected_text = f"\n\n🎯 **Sélectionné:** {', '.join(selected_options)}" if selected_options else "\n\n⚠️ **Aucun type de trajet sélectionné**"
    
    message_text = (
        f"🚗 *Création d'un nouveau trajet* ({role_text})\n\n"
        f"Étape 2️⃣ - **Choisissez le type de trajet** (obligatoire):\n\n"
        f"🔘 **Trajet simple** : Un trajet unique à une date précise\n"
        f"🔘 **Trajet régulier** : Trajets répétés chaque semaine\n"
        f"🔘 **Aller-retour** : Trajet avec retour le même jour\n\n"
        f"📝 *Cliquez sur UNE seule option pour la sélectionner.*{selected_text}"
    )
    
    if query:
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard_options), parse_mode="Markdown")
    # else if called without query (e.g. after text input, though not typical for this step)
    # await update.effective_message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard_options), parse_mode="Markdown")
    return CREATE_TRIP_OPTIONS


# --- Correction du handler d'options pour permettre la sélection puis la validation ---

# Correction FINALE : handler d'options qui fonctionne comme le bouton "start"
async def handle_create_trip_options(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("create_trip_option:"):
        option = query.data.split(":")[1]
        context.user_data.setdefault('trip_options', {})
        
        # Logique de sélection exclusive pour le type de trajet
        if option in ['simple', 'regular', 'round_trip']:
            # Désélectionner toutes les autres options de type de trajet
            context.user_data['trip_options']['simple'] = False
            context.user_data['trip_options']['regular'] = False
            context.user_data['trip_options']['round_trip'] = False
            
            # Sélectionner uniquement l'option choisie
            context.user_data['trip_options'][option] = True
            
            logger.info(f"✅ Option de trajet sélectionnée: {option}")
        else:
            # Pour les autres options (comme women_only), garder la logique de toggle
            context.user_data['trip_options'][option] = not context.user_data['trip_options'].get(option, False)
        
        return await show_create_trip_options(update, context) # Refresh options view

    elif query.data == "create_trip_options:continue":
        # Vérifier qu'une option de type de trajet a été sélectionnée
        trip_options = context.user_data.get('trip_options', {})
        has_trip_type = (trip_options.get('simple', False) or 
                        trip_options.get('regular', False) or 
                        trip_options.get('round_trip', False))
        
        if not has_trip_type:
            # Forcer l'utilisateur à choisir un type de trajet
            await query.answer("⚠️ Vous devez choisir un type de trajet (Simple, Régulier ou Aller-retour)", show_alert=True)
            return CREATE_TRIP_OPTIONS
        
        # Vérifier si c'est un trajet régulier
        is_regular = trip_options.get('regular', False)
        
        if is_regular:
            # Aller directement au calendrier interactif pour trajets réguliers
            now = datetime.now()
            context.user_data['calendar_year'] = now.year
            context.user_data['calendar_month'] = now.month
            context.user_data['selected_calendar_dates'] = set()
            context.user_data['selected_days'] = []  # Vide au début
            
            # Afficher le calendrier interactif
            calendar_keyboard = create_interactive_calendar(now.year, now.month, [], set())
            
            await query.edit_message_text(
                f"📅 **Trajet régulier - Sélection des dates**\n\n"
                f"Cliquez directement sur les dates que vous voulez pour vos trajets :\n"
                f"• Cliquez sur **L, M, M, J, V, S, D** pour sélectionner tous les jours de cette semaine (optionnel)\n"
                f"• Ou cliquez directement sur les dates individuelles (recommandé)\n\n"
                f"✅ = Sélectionné\n"
                f"☑️ = Disponible\n"
                f"❌ = Date passée",
                reply_markup=calendar_keyboard,
                parse_mode="Markdown"
            )
            return REGULAR_CALENDAR_SELECTION
        else:
            # Flux normal pour trajet simple
            context.user_data['current_state'] = CREATE_DEPARTURE
            keyboard_dep = [
                [InlineKeyboardButton(city, callback_data=f"create_dep_city:{city}")] for city in SWISS_CITIES_SUGGESTIONS[:5]
            ]
            keyboard_dep.append([InlineKeyboardButton("Autre ville...", callback_data="create_dep_other")])
            keyboard_dep.append([InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel_departure")])
            await query.edit_message_text("Étape 3️⃣ - Choisissez votre ville de départ:", reply_markup=InlineKeyboardMarkup(keyboard_dep))
            return CREATE_DEPARTURE

    # Fallback or error
    return CREATE_TRIP_OPTIONS

async def handle_create_departure_city_callback(update: Update, context: CallbackContext):
    """Gère le clic sur un bouton de ville de départ suggérée ou 'Autre ville'."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data

    if callback_data == "create_dep_other":
        await query.edit_message_text("Veuillez entrer le nom de votre ville de départ ou son NPA:")
        return CREATE_DEPARTURE
    elif callback_data.startswith("create_dep_city:"):
        city_name = callback_data.split(":")[1]
        context.user_data['departure'] = {'name': city_name}
        logger.info(f"Ville de départ sélectionnée: {city_name}")
        
        keyboard_arr = [
            [InlineKeyboardButton(city, callback_data=f"create_arr_city:{city}")] 
            for city in SWISS_CITIES_SUGGESTIONS[:5]
        ]
        keyboard_arr.append([InlineKeyboardButton("Autre ville...", callback_data="create_arr_other")])
        keyboard_arr.append([InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")])
        
        await query.edit_message_text(
            f"Départ depuis: {city_name}\nChoisissez votre destination:",
            reply_markup=InlineKeyboardMarkup(keyboard_arr)
        )
        return CREATE_ARRIVAL

async def handle_create_departure_text(update: Update, context: CallbackContext):
    """Gère la saisie texte pour la ville de départ."""
    user_input = update.message.text.strip()
    matches = find_locality(user_input)

    if matches:
        keyboard = []
        for match in matches[:5]:  # Limite à 5 résultats
            display_text = f"{match['name']} ({match['zip']})"
            callback_data = f"create_dep_loc:{match['zip']}|{match['name']}"
            keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("🔄 Réessayer", callback_data="create_dep_retry_text")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel_departure")])
        
        await update.message.reply_text(
            "📍 Voici les localités trouvées. Choisissez votre ville de départ :",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "❌ Ville non trouvée. Veuillez réessayer avec un autre nom ou NPA.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel_departure")
            ]])
        )
    return CREATE_DEPARTURE

async def handle_create_departure_loc_callback(update: Update, context: CallbackContext):
    """Gère le clic sur une localité spécifique après recherche texte."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data

    if callback_data == "create_dep_retry_text":
        await query.edit_message_text("⌨️ Veuillez entrer le nom de votre ville de départ ou son NPA:")
        return CREATE_DEPARTURE

    elif callback_data.startswith("create_dep_loc:"):
        try:
            # Extraction correcte des données du callback
            locality_part = callback_data.split(":")[1]
            zip_code, name = locality_part.split('|')
            context.user_data['departure'] = {'name': name, 'zip': zip_code}
            logger.info(f"Ville de départ confirmée: {name} ({zip_code})")

            # Passage à la sélection de la ville d'arrivée
            keyboard_arr = [
                [InlineKeyboardButton(city, callback_data=f"create_arr_city:{city}")] 
                for city in SWISS_CITIES_SUGGESTIONS[:5]
            ]
            keyboard_arr.append([InlineKeyboardButton("🏙️ Autre ville...", callback_data="create_arr_other")])
            keyboard_arr.append([InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")])

            await query.edit_message_text(
                f"🌍 Départ depuis: {name}\nChoisissez votre destination:",
                reply_markup=InlineKeyboardMarkup(keyboard_arr)
            )
            return CREATE_ARRIVAL

        except Exception as e:
            logger.error(f"Erreur lors de la sélection de la ville de départ: {e}")
            await query.edit_message_text(
                "Une erreur s'est produite. Veuillez réessayer.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Réessayer", callback_data="create_dep_retry_text")
                ]])
            )
            return CREATE_DEPARTURE

    return CREATE_DEPARTURE

async def handle_create_arrival_city_callback(update: Update, context: CallbackContext):
    """Gère le clic sur un bouton de ville d'arrivée."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    departure_display = context.user_data.get('departure', {}).get('name', 'N/A')

    if callback_data == "create_arr_other":
        await query.edit_message_text(
            f"Départ: {departure_display}\n"
            "⌨️ Veuillez entrer le nom de votre ville d'arrivée ou son NPA:"
        )
        return CREATE_ARRIVAL
        
    elif callback_data.startswith("create_arr_city:"):
        city_name = callback_data.split(":")[1]
        context.user_data['arrival'] = {'name': city_name}
        logger.info(f"Ville d'arrivée (création) sélectionnée: {city_name}")
        
        # Vérifier si c'est un trajet régulier qui a déjà ses dates
        is_regular = context.user_data.get('trip_options', {}).get('regular', False)
        regular_dates = context.user_data.get('regular_dates')
        
        if is_regular and regular_dates:
            # Trajet régulier avec dates déjà sélectionnées - aller directement aux sièges
            departure = context.user_data.get('departure', {})
            arrival = context.user_data.get('arrival', {})
            departure_display = departure.get('name', str(departure)) if departure else 'N/A'
            arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
            
            dates_display = "\n".join([f"📅 {datetime.strptime(d, '%Y-%m-%d').strftime('%A %d %B %Y')}" for d in regular_dates[:3]])
            if len(regular_dates) > 3:
                dates_display += f"\n... et {len(regular_dates) - 3} autres dates"
            
            # Trajet régulier avec dates déjà sélectionnées - aller à la sélection du type d'heure
            await query.edit_message_text(
                f"🕐 **Gestion des horaires pour vos trajets réguliers**\n\n"
                f"Comment souhaitez-vous gérer les horaires ?\n\n"
                f"🕐 **Même heure** : La même heure pour tous vos trajets\n"
                f"⏰ **Horaires indépendants** : Une heure différente pour chaque date",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("� Même heure pour tous", callback_data="regular_time:same")],
                    [InlineKeyboardButton("⏰ Horaires indépendants", callback_data="regular_time:individual")],
                    [InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")]
                ]),
                parse_mode="Markdown"
            )
            return REGULAR_TIME_TYPE
        else:
            # Trajet simple - afficher le calendrier de sélection de date
            now = datetime.now()
            markup = await create_calendar_markup(now.year, now.month)
            await query.edit_message_text(
                "📅 Sélectionnez la date du trajet:",
                reply_markup=markup
            )
            return CREATE_CALENDAR

    return CREATE_ARRIVAL

async def handle_create_arrival_text(update: Update, context: CallbackContext):
    """Gère la saisie texte pour la ville d'arrivée."""
    user_input = update.message.text.strip()
    matches = find_locality(user_input)
    departure = context.user_data.get('departure', {})
    departure_display = departure.get('name', str(departure)) if departure else 'N/A'

    if matches:
        keyboard = []
        for match in matches[:5]:  # Limite à 5 résultats comme pour le départ
            display_text = format_locality_result(match)
            # Correction du format du callback_data pour correspondre au pattern attendu
            callback_data = f"create_arr_loc:{match['zip']}|{match['name']}"  # Pas de changement nécessaire
            keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("🔄 Réessayer", callback_data="create_arr_retry_text")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")])
        
        await update.message.reply_text(
            f"Départ: {departure_display}\n"
            "📍 Voici les localités trouvées. Choisissez votre ville d'arrivée :",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            f"Départ: {departure_display}\n"
            "❌ Ville non trouvée. Veuillez réessayer avec un autre nom ou NPA."
        )
    return CREATE_ARRIVAL

async def handle_create_arrival_loc_callback(update: Update, context: CallbackContext):
    """Gère le clic sur une localité spécifique pour l'arrivée."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    departure = context.user_data.get('departure', {})
    departure_display = departure.get('name', str(departure)) if departure else 'N/A'
    
    if callback_data == "create_arr_retry_text":
        await query.edit_message_text(
            f"Départ: {departure_display}\n"
            "⌨️ Veuillez entrer le nom de votre ville d'arrivée ou son NPA:"
        )
        return CREATE_ARRIVAL

    elif callback_data.startswith("create_arr_loc:"):
        try:
            locality_part = callback_data.split(":")[1]
            zip_code, name = locality_part.split('|')
            context.user_data['arrival'] = {'name': name, 'zip': zip_code}
            logger.info(f"Ville d'arrivée (recherche) sélectionnée: {name} ({zip_code})")

            # Vérifier si c'est un trajet régulier qui a déjà ses dates
            is_regular = context.user_data.get('trip_options', {}).get('regular', False)
            regular_dates = context.user_data.get('regular_dates')
            
            if is_regular and regular_dates:
                # Trajet régulier avec dates déjà sélectionnées - aller à la sélection du type d'horaire
                departure = context.user_data.get('departure', {})
                arrival = context.user_data.get('arrival', {})
                departure_display = departure.get('name', str(departure)) if departure else 'N/A'
                arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
                
                dates_display = "\n".join([f"📅 {datetime.strptime(d, '%Y-%m-%d').strftime('%A %d %B %Y')}" for d in regular_dates[:3]])
                if len(regular_dates) > 3:
                    dates_display += f"\n... et {len(regular_dates) - 3} autres dates"
                
                message_text = (
                    f"✅ **Trajets réguliers configurés**\n\n"
                    f"De: {departure_display}\n"
                    f"À: {arrival_display}\n"
                    f"Dates:\n{dates_display}\n\n"
                    f"📊 **Total:** {len(regular_dates)} trajet{'s' if len(regular_dates) > 1 else ''}\n\n"
                    "⏰ Comment souhaitez-vous gérer les horaires ?"
                )
                
                keyboard = [
                    [InlineKeyboardButton("🕒 Même horaire pour toutes les dates", callback_data="regular_time:same")],
                    [InlineKeyboardButton("⏰ Horaires individuels par date", callback_data="regular_time:individual")]
                ]
                await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
                return REGULAR_TIME_TYPE
            else:
                # Trajet simple - afficher le calendrier de sélection de date
                now = datetime.now()
                markup = await create_calendar_markup(now.year, now.month)
                await query.edit_message_text(
                    "📅 Sélectionnez la date du trajet:",
                    reply_markup=markup
                )
                return CREATE_CALENDAR
            
        except Exception as e:
            logger.error(f"[ERROR] Erreur sélection ville: {str(e)}", exc_info=True)
            await query.edit_message_text(
                "❌ Une erreur s'est produite. Veuillez réessayer.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Réessayer", callback_data="create_arr_retry_text")
                ]])
            )
            return CREATE_ARRIVAL

    return CREATE_ARRIVAL

async def handle_regular_time_type(update: Update, context: CallbackContext):
    """Gère la sélection du type d'horaire pour les trajets réguliers."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    regular_dates = context.user_data.get('regular_dates', [])
    
    if callback_data == "regular_time:same":
        # Même horaire pour toutes les dates
        context.user_data['regular_time_type'] = 'same'
        
        departure = context.user_data.get('departure', {})
        arrival = context.user_data.get('arrival', {})
        departure_display = departure.get('name', str(departure)) if departure else 'N/A'
        arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
        
        message_text = (
            f"✅ **Même horaire pour toutes les dates**\n\n"
            f"De: {departure_display}\n"
            f"À: {arrival_display}\n"
            f"📊 {len(regular_dates)} trajet{'s' if len(regular_dates) > 1 else ''}\n\n"
            "⏰ Choisissez l'heure de départ pour tous les trajets:"
        )
        
        # Utiliser le sélecteur d'heure existant
        hours_keyboard = []
        for hour in range(6, 23):  # 6h à 22h
            hours_keyboard.append([InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"create_hour:{hour}")])
        
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(hours_keyboard))
        return CREATE_TIME
        
    elif callback_data == "regular_time:individual":
        # Horaires individuels par date
        context.user_data['regular_time_type'] = 'individual'
        context.user_data['regular_times'] = {}
        context.user_data['current_date_index'] = 0
        
        # Commencer avec la première date
        first_date = regular_dates[0]
        context.user_data['current_regular_date'] = first_date
        
        departure = context.user_data.get('departure', {})
        arrival = context.user_data.get('arrival', {})
        departure_display = departure.get('name', str(departure)) if departure else 'N/A'
        arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
        
        date_display = datetime.strptime(first_date, '%Y-%m-%d').strftime('%A %d %B %Y')
        
        message_text = (
            f"⏰ **Horaires individuels**\n\n"
            f"De: {departure_display}\n"
            f"À: {arrival_display}\n\n"
            f"📅 **Date 1/{len(regular_dates)}:** {date_display}\n\n"
            "Choisissez l'heure de départ pour cette date:"
        )
        
        # Utiliser le sélecteur d'heure existant
        hours_keyboard = []
        for hour in range(6, 23):  # 6h à 22h
            hours_keyboard.append([InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"create_hour:{hour}")])
        
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(hours_keyboard))
        return CREATE_TIME
    
    return REGULAR_TIME_TYPE

async def handle_create_date_confirmed(update: Update, context: CallbackContext):
    """Appelé après confirmation de la date et heure par le date_picker."""
    # selected_datetime devrait être dans context.user_data par le date_picker
    selected_dt = context.user_data.get('selected_datetime')
    if not selected_dt:
        logger.error("selected_datetime non trouvé dans handle_create_date_confirmed")
        await update.effective_message.reply_text("Une erreur s'est produite avec la date. Veuillez réessayer.")
        return CREATE_DATE

    context.user_data['date'] = selected_dt.strftime('%d/%m/%Y %H:%M')
    context.user_data['datetime_obj'] = selected_dt
    
    logger.debug(f"[DATE_CONFIRMED] Date d'aller stockée: {selected_dt}")
    logger.debug(f"[DATE_CONFIRMED] context.user_data['datetime_obj'] = {context.user_data['datetime_obj']}")
    
    # Vérifier si c'est un trajet aller-retour
    trip_options = context.user_data.get('trip_options', {})
    is_round_trip = trip_options.get('round_trip', False)
    
    logger.debug(f"[DATE_CONFIRMED] is_round_trip: {is_round_trip}")
    logger.debug(f"[DATE_CONFIRMED] trip_options: {trip_options}")
    
    if is_round_trip:
        # Pour les trajets aller-retour, demander la date de retour
        logger.debug("[DATE_CONFIRMED] Redirection vers start_return_date_selection")
        logger.debug(f"[DATE_CONFIRMED] IMPORTANT - Trajet aller-retour détecté ! Début sélection retour")
        await start_return_date_selection(update, context)
        logger.debug(f"[DATE_CONFIRMED] IMPORTANT - Retour état RETURN_DATE")
        return RETURN_DATE
    
    # Pour les trajets simples et réguliers, continuer normalement
    departure = context.user_data.get('departure', {})
    arrival = context.user_data.get('arrival', {})
    departure_display = departure.get('name', str(departure)) if departure else 'N/A'
    arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
    date_display = context.user_data['date']

    # Adapter le message selon le rôle
    trip_role = context.user_data.get('trip_type', 'driver')
    if trip_role == 'passenger':
        seats_message = "Étape 6️⃣ - Combien de places voulez-vous réserver? (1-4)"
    else:
        seats_message = "Étape 6️⃣ - Combien de places disponibles? (1-8)"

    message_text = (
        f"Récapitulatif partiel:\n"
        f"De: {departure_display}\n"
        f"À: {arrival_display}\n"
        f"Date: {date_display}\n\n"
        f"{seats_message}"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(message_text)
    else:
        await update.message.reply_text(message_text)
    return CREATE_SEATS


async def handle_create_seats(update: Update, context: CallbackContext):
    """Gère l'entrée du nombre de sièges."""
    seats_text = update.message.text
    if not validate_seats(seats_text):
        await update.message.reply_text("❌ Nombre de places invalide. Entrez un nombre entre 1 et 8.")
        return CREATE_SEATS
    
    context.user_data['seats'] = int(seats_text)
    trip_role = context.user_data.get('trip_type', 'driver')
    logger.info(f"Nombre de sièges (création, rôle {trip_role}): {seats_text}")
    
    # VÉRIFICATION CRUCIALE : Pour les trajets aller-retour, vérifier si on a la date de retour
    trip_options = context.user_data.get('trip_options', {})
    is_round_trip = trip_options.get('round_trip', False)
    has_return_date = context.user_data.get('return_datetime_obj') is not None
    
    logger.debug(f"[SEATS] is_round_trip: {is_round_trip}, has_return_date: {has_return_date}")
    
    if is_round_trip and not has_return_date:
        # Pour les trajets aller-retour sans date de retour, aller à la sélection de date de retour
        logger.debug("[SEATS] TRAJET ALLER-RETOUR sans date de retour - Redirection vers sélection retour")
        await start_return_date_selection(update, context)
        return RETURN_DATE
    
    # --- Calcul automatique du prix ---
    # Utiliser la fonction de calcul partagée
    return await handle_seats_to_price_calculation(update, context)

# --- Modification du résumé pour afficher le prix auto ---
async def handle_create_price(update: Update, context: CallbackContext, auto=False):
    # Ne pas demander de saisie, juste afficher le résumé
    dep = context.user_data.get('departure', {})
    arr = context.user_data.get('arrival', {})
    dep_display = dep.get('name', dep) if isinstance(dep, dict) else dep
    arr_display = arr.get('name', arr) if isinstance(arr, dict) else arr
    prix = context.user_data.get('price', 'N/A')
    dist = context.user_data.get('distance_km', 'N/A')
    
    # Traduction du rôle en français
    trip_type = context.user_data.get('trip_type', 'N/A')
    if trip_type == 'driver':
        role_fr = "🚗 Conducteur"
    elif trip_type == 'passenger':
        role_fr = "🧍 Passager"
    else:
        role_fr = trip_type
    
    # Vérification si c'est un trajet aller-retour
    is_round_trip = context.user_data.get('trip_options', {}).get('round_trip', False)
    
    # Formatage de la date/heure de départ
    datetime_obj = context.user_data.get('datetime_obj')
    if datetime_obj:
        date_formatted = datetime_obj.strftime('%d/%m/%Y à %H:%M')
    else:
        # Fallback sur l'ancienne clé 'date' si elle existe
        date_str = context.user_data.get('date', 'N/A')
        if date_str != 'N/A':
            if hasattr(date_str, 'strftime'):
                date_formatted = date_str.strftime('%d/%m/%Y à %H:%M')
            else:
                date_formatted = str(date_str)
        else:
            date_formatted = 'Non définie'
    
    # Formatage de la date/heure de retour pour les trajets aller-retour
    return_date_formatted = None
    if is_round_trip:
        return_datetime_obj = context.user_data.get('return_datetime_obj')
        if return_datetime_obj:
            return_date_formatted = return_datetime_obj.strftime('%d/%m/%Y à %H:%M')
    
    # Options en français
    options = context.user_data.get('trip_options', {})
    if options.get('simple'):
        options_str = "✅ Trajet simple"
    elif is_round_trip:
        options_str = "🔄 Trajet aller-retour"
    else:
        options_str = "📋 Options avancées"
    
    # Adaptation du message selon le rôle
    if trip_type == 'passenger':
        # CORRECTION : Pour les passagers, le prix est divisé par le nombre de places recherchées
        seats = context.user_data.get('seats', 1)
        prix_par_place = round(prix / seats, 2)
        
        if is_round_trip and return_date_formatted:
            # Affichage pour trajet aller-retour passager
            summary = (
                "🎯 *Résumé de votre demande de trajet aller-retour*\n\n"
                f"👤 *Rôle :* {role_fr}\n"
                f"⚙️ *Type :* {options_str}\n\n"
                f"🔄 **Trajet ALLER :**\n"
                f"🌍 *Départ :* {dep_display}\n"
                f"🏁 *Arrivée :* {arr_display}\n"
                f"📅 *Date et heure :* {date_formatted}\n\n"
                f"🔄 **Trajet RETOUR :**\n"
                f"🌍 *Départ :* {arr_display}\n"
                f"🏁 *Arrivée :* {dep_display}\n"
                f"📅 *Date et heure :* {return_date_formatted}\n\n"
                f"📏 *Distance (par trajet) :* {dist} km\n"
                f"👥 *Places recherchées :* {seats}\n"
                f"💰 *Prix total (aller + retour) :* {prix * 2} CHF\n"
                f"💰 *Prix par place (aller + retour) :* {round((prix * 2) / seats, 2)} CHF\n\n"
                "✨ *Vos demandes seront visibles par les conducteurs disponibles.*\n"
                "📞 *Ils pourront vous proposer leurs services.*\n\n"
                "Confirmez-vous la publication de ces demandes ?"
            )
        else:
            # Affichage pour trajet simple passager
            summary = (
                "🎯 *Résumé de votre demande de trajet*\n\n"
                f"👤 *Rôle :* {role_fr}\n"
                f"⚙️ *Type :* {options_str}\n\n"
                f"🌍 *Départ :* {dep_display}\n"
                f"🏁 *Arrivée :* {arr_display}\n"
                f"📅 *Date et heure :* {date_formatted}\n\n"
                f"📏 *Distance :* {dist} km\n"
                f"👥 *Places recherchées :* {seats}\n"
                f"💰 *Prix total du trajet :* {prix} CHF\n"
                f"💰 *Prix par place :* {prix_par_place} CHF (partagé entre {seats} passagers)\n\n"
                "✨ *Votre demande sera visible par les conducteurs disponibles.*\n"
                "📞 *Ils pourront vous proposer leurs services.*\n\n"
                "Confirmez-vous la publication de cette demande ?"
            )
        button_text = "✅ Publier ma demande !"
    else:
        if is_round_trip and return_date_formatted:
            # Affichage pour trajet aller-retour conducteur
            summary = (
                "🎯 *Résumé de votre offre de trajet aller-retour*\n\n"
                f"👤 *Rôle :* {role_fr}\n"
                f"⚙️ *Type :* {options_str}\n\n"
                f"🔄 **Trajet ALLER :**\n"
                f"🌍 *Départ :* {dep_display}\n"
                f"🏁 *Arrivée :* {arr_display}\n"
                f"📅 *Date et heure :* {date_formatted}\n\n"
                f"🔄 **Trajet RETOUR :**\n"
                f"🌍 *Départ :* {arr_display}\n"
                f"🏁 *Arrivée :* {dep_display}\n"
                f"📅 *Date et heure :* {return_date_formatted}\n\n"
                f"📏 *Distance (par trajet) :* {dist} km\n"
                f"💺 *Places disponibles :* {context.user_data.get('seats', 'N/A')}\n"
                f"💰 *Prix total (aller + retour) :* {prix * 2} CHF\n\n"
                f"💡 *Comment ça marche :*\n"
                f"• Prix total fixe par trajet : {prix} CHF\n"
                f"• Prix par passager = {prix} CHF ÷ nombre de passagers\n"
                f"• Plus de passagers = prix moins cher pour chacun\n"
                f"• Remboursement automatique si le prix diminue\n\n"
                "✨ *Vos trajets seront visibles par les passagers intéressés.*\n\n"
                "Confirmez-vous la création de ces trajets ?"
            )
        else:
            # Affichage pour trajet simple conducteur
            summary = (
                "🎯 *Résumé de votre offre de trajet*\n\n"
                f"👤 *Rôle :* {role_fr}\n"
                f"⚙️ *Type :* {options_str}\n\n"
                f"🌍 *Départ :* {dep_display}\n"
                f"🏁 *Arrivée :* {arr_display}\n"
                f"📅 *Date et heure :* {date_formatted}\n\n"
                f"📏 *Distance :* {dist} km\n"
                f"💺 *Places disponibles :* {context.user_data.get('seats', 'N/A')}\n"
                f"💰 *Prix total du trajet :* {prix} CHF\n\n"
                f"💡 *Comment ça marche :*\n"
                f"• Prix total fixe du trajet : {prix} CHF\n"
                f"• Prix par passager = {prix} CHF ÷ nombre de passagers\n"
                f"• Plus de passagers = prix moins cher pour chacun\n"
                f"• Remboursement automatique si le prix diminue\n\n"
                "✨ *Votre trajet sera visible par les passagers intéressés.*\n\n"
                "Confirmez-vous la création de ce trajet ?"
            )
        button_text = "✅ Créer ce trajet !"
    
    keyboard = [
        [InlineKeyboardButton(button_text, callback_data="create_confirm_yes")],
        [InlineKeyboardButton("❌ Non, annuler", callback_data="create_trip:cancel_confirm")]
    ]
    if update.message:
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CREATE_CONFIRM

# =============================================================================
# FONCTIONS POUR TRAJETS ALLER-RETOUR
# =============================================================================

async def start_return_date_selection(update: Update, context: CallbackContext):
    """Démarre la sélection de la date de retour pour un trajet aller-retour."""
    logger.debug("[RETURN_DATE] Démarrage de la sélection de date de retour")
    
    departure_date = context.user_data.get('datetime_obj')
    departure_display = departure_date.strftime('%d/%m/%Y à %H:%M') if departure_date else 'N/A'
    
    departure = context.user_data.get('departure', {})
    arrival = context.user_data.get('arrival', {})
    departure_city = departure.get('name', str(departure)) if departure else 'N/A'
    arrival_city = arrival.get('name', str(arrival)) if arrival else 'N/A'
    
    # Marquer que nous sommes dans le processus de sélection de retour
    context.user_data['selecting_return'] = True
    logger.debug("[RETURN_DATE] Flag selecting_return défini à True")
    logger.debug(f"[RETURN_DATE] IMPORTANT - Interface retour affichée, flag selecting_return=True")
    
    message_text = (
        f"🔄 *TRAJET ALLER-RETOUR - ÉTAPE 2/2*\n\n"
        f"✅ **ALLER CONFIGURÉ :**\n"
        f"📍 {departure_city} → {arrival_city}\n"
        f"📅 {departure_display}\n\n"
        f"📅 **MAINTENANT : CONFIGUREZ LE RETOUR**\n"
        f"📍 {arrival_city} → {departure_city}\n\n"
        f"👆 *Sélectionnez la DATE de retour dans le calendrier ci-dessous :*"
    )
    
    # Créer le calendrier pour la sélection de date de retour
    now = datetime.now()
    calendar_markup = await create_calendar_markup(now.year, now.month)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            message_text, 
            parse_mode="Markdown",
            reply_markup=calendar_markup
        )
    else:
        await update.message.reply_text(
            message_text, 
            parse_mode="Markdown",
            reply_markup=calendar_markup
        )
    
    return RETURN_DATE

async def handle_return_date_confirmed(update: Update, context: CallbackContext):
    """Appelé après confirmation de la date et heure de retour."""
    # Récupérer la date de retour spécifique
    selected_dt = context.user_data.get('return_selected_datetime')
    if not selected_dt:
        # Fallback vers selected_datetime si return_selected_datetime n'existe pas
        selected_dt = context.user_data.get('selected_datetime')
        if not selected_dt:
            logger.error("Aucune date de retour trouvée dans handle_return_date_confirmed")
            await update.effective_message.reply_text("Une erreur s'est produite avec la date de retour. Veuillez réessayer.")
            return RETURN_DATE

    logger.debug(f"[RETURN_DATE_CONFIRMED] Date de retour récupérée: {selected_dt}")

    # IMPORTANT: Stocker immédiatement la date de retour pour éviter l'écrasement
    context.user_data['return_date'] = selected_dt.strftime('%d/%m/%Y %H:%M')
    context.user_data['return_datetime_obj'] = selected_dt
    
    # Nettoyer le flag de sélection de retour
    context.user_data['selecting_return'] = False
    
    # Vérifier la logique des dates aller/retour
    departure_date = context.user_data.get('datetime_obj')
    logger.debug(f"[RETURN_DATE_VALIDATION] departure_date depuis context: {departure_date}")
    logger.debug(f"[RETURN_DATE_VALIDATION] selected_dt (retour): {selected_dt}")
    
    if departure_date and selected_dt:
        # Comparer les dates (sans l'heure)
        departure_date_only = departure_date.date()
        return_date_only = selected_dt.date()
        
        logger.debug(f"[RETURN_DATE_VALIDATION] Aller: {departure_date} ({departure_date_only})")
        logger.debug(f"[RETURN_DATE_VALIDATION] Retour: {selected_dt} ({return_date_only})")
        logger.debug(f"[RETURN_DATE_VALIDATION] Comparaison - Même jour? {return_date_only == departure_date_only}")
        logger.debug(f"[RETURN_DATE_VALIDATION] Comparaison - Retour avant aller? {return_date_only < departure_date_only}")
        logger.debug(f"[RETURN_DATE_VALIDATION] Comparaison - Retour après aller? {return_date_only > departure_date_only}")
        # Si c'est le même jour, vérifier que l'heure de retour est après l'heure d'aller
        if return_date_only == departure_date_only:
            # Même jour : l'heure de retour doit être après l'heure d'aller  
            if selected_dt <= departure_date:
                await update.effective_message.reply_text(
                    "❌ Pour un aller-retour le même jour, l'heure de retour doit être après l'heure d'aller.\n\n"
                    f"🚗 Aller : {departure_date.strftime('%H:%M')}\n"
                    f"🔄 Retour : {selected_dt.strftime('%H:%M')}\n\n"
                    "Veuillez sélectionner une heure de retour plus tardive."
                )
                return RETURN_DATE
        # Si c'est un jour antérieur, refuser
        elif return_date_only < departure_date_only:
            await update.effective_message.reply_text(
                "❌ La date de retour ne peut pas être avant la date d'aller.\n\n"
                f"🚗 Aller : {departure_date.strftime('%d/%m/%Y')}\n" 
                f"🔄 Retour : {selected_dt.strftime('%d/%m/%Y')}\n\n"
                "Veuillez sélectionner une date de retour après ou le même jour que l'aller."
            )
            return RETURN_DATE
        # Si c'est un jour postérieur, tout va bien (pas de vérification d'heure nécessaire)
        else:
            logger.debug(f"[RETURN_DATE_VALIDATION] Jour postérieur détecté - validation OK")
    
    departure = context.user_data.get('departure', {})
    arrival = context.user_data.get('arrival', {})
    departure_display = departure.get('name', str(departure)) if departure else 'N/A'
    arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
    
    departure_date_display = context.user_data.get('date', 'N/A')
    return_date_display = context.user_data.get('return_date', 'N/A')

    # Vérifier si on a déjà le nombre de places
    seats = context.user_data.get('seats')
    if seats:
        # Si on a déjà les places, aller directement au calcul de prix
        message_text = (
            f"✅ **Trajet aller-retour configuré :**\n\n"
            f"🚗 **Aller :**\n"
            f"📍 {departure_display} → {arrival_display}\n"
            f"📅 {departure_date_display}\n\n"
            f"🔄 **Retour :**\n"
            f"📍 {arrival_display} → {departure_display}\n"
            f"📅 {return_date_display}\n\n"
            f"💺 **Places disponibles :** {seats}\n\n"
            f"🔄 Calcul du prix en cours..."
        )
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message_text, parse_mode="Markdown")
        else:
            await update.message.reply_text(message_text, parse_mode="Markdown")
        
        # Continuer avec le calcul de prix automatiquement
        return await handle_seats_to_price_calculation(update, context)
    else:
        # Si on n'a pas encore les places, les demander
        message_text = (
            f"✅ **Trajet aller-retour configuré :**\n\n"
            f"🚗 **Aller :**\n"
            f"📍 {departure_display} → {arrival_display}\n"
            f"📅 {departure_date_display}\n\n"
            f"🔄 **Retour :**\n"
            f"📍 {arrival_display} → {departure_display}\n"
            f"📅 {return_date_display}\n\n"
            f"Passons maintenant au nombre de places :"
        )
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message_text, parse_mode="Markdown")
        else:
            await update.message.reply_text(message_text, parse_mode="Markdown")
        
        return CREATE_SEATS

async def handle_seats_to_price_calculation(update: Update, context: CallbackContext):
    """Fait le calcul de prix après avoir obtenu le nombre de places."""
    trip_role = context.user_data.get('trip_type', 'driver')
    
    # --- Calcul automatique du prix ---
    dep = context.user_data.get('departure', {})
    arr = context.user_data.get('arrival', {})
    
    # Extraire les noms des localités pour le calcul de prix
    dep_name = dep.get('name', '') if isinstance(dep, dict) else str(dep)
    arr_name = arr.get('name', '') if isinstance(arr, dict) else str(arr)
    
    prix, dist = compute_price_auto(dep_name, arr_name)
    context.user_data['price'] = prix
    context.user_data['distance_km'] = dist
    
    if prix is None:
        await update.effective_message.reply_text("Impossible de calculer le prix automatiquement (coordonnées manquantes). Veuillez contacter le support.")
        return ConversationHandler.END
    
    # Message adapté selon le rôle
    if trip_role == 'passenger':
        await update.effective_message.reply_text(
            f"💰 Budget estimé : {prix} CHF par place pour {dist} km.\n"
            f"Ce montant sera proposé aux conducteurs intéressés."
        )
    else:
        # CORRECTION CRITIQUE: Le prix calculé est le prix TOTAL du trajet
        # Le prix par passager dépend du nombre réel de passagers, pas des places disponibles
        
        # Stocker le prix total du trajet
        context.user_data['total_trip_price'] = prix
        
        await update.effective_message.reply_text(
            f"💰 Le prix total du trajet est calculé à {prix} CHF pour {dist} km.\n\n"
            f"✅ **LOGIQUE DE PRIX CORRIGÉE :**\n"
            f"• Prix total du trajet : {prix} CHF\n"
            f"• Prix par passager = Prix total ÷ Nombre de passagers ayant payé\n\n"
            f"📊 **Exemples de répartition :**\n"
            f"• 1 passager → {prix} CHF par passager\n"
            f"• 2 passagers → {round(prix / 2, 2)} CHF par passager\n"
            f"• 3 passagers → {round(prix / 3, 2)} CHF par passager\n\n"
            f"🔄 **Remboursement automatique :**\n"
            f"Si un passager supplémentaire s'ajoute après un paiement, "
            f"les passagers précédents seront automatiquement remboursés de la différence via PayPal."
        )
        
        # Le prix stocké pour la création du trajet reste le prix total
        context.user_data['price'] = prix
    
    # Passer directement à la confirmation
    return await handle_create_price(update, context, auto=True)

async def handle_create_confirm(update: Update, context: CallbackContext):
    """Confirme et sauvegarde le trajet."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_confirm_yes":
        try:
            db = get_db()
            user_id = update.effective_user.id
            db_user = db.query(User).filter(User.telegram_id == user_id).first()
            if not db_user:
                logger.error(f"Utilisateur non trouvé dans la BDD: {user_id}")
                await query.edit_message_text("❌ Erreur: Utilisateur non trouvé. Veuillez d'abord utiliser /start.")
                context.user_data.clear()
                return ConversationHandler.END

            departure_data = context.user_data.get('departure', {})
            arrival_data = context.user_data.get('arrival', {})
            trip_options = context.user_data.get('trip_options', {})
            trip_role = context.user_data.get('trip_type', 'driver')  # 'driver' ou 'passenger'
            
            logger.info(f"Création de trajet avec rôle: {trip_role}")
            
            # Vérifier si c'est un trajet régulier
            is_regular = trip_options.get('regular', False)
            regular_dates = context.user_data.get('regular_dates', [])
            
            if is_regular and regular_dates:
                # Créer des trajets réguliers multiples
                created_trips = []
                for date_str in regular_dates:
                    # Convertir la date string en datetime avec l'heure
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    # Utiliser l'heure du trajet simple ou par défaut 08:00
                    time_obj = context.user_data.get('datetime_obj')
                    if time_obj:
                        departure_time = date_obj.replace(hour=time_obj.hour, minute=time_obj.minute)
                    else:
                        departure_time = date_obj.replace(hour=8, minute=0)
                    
                    # Configuration des IDs selon le rôle
                    if trip_role == 'passenger':
                        # Passager : creator_id = user, driver_id = None (à remplir plus tard)
                        driver_id = None
                        creator_id = db_user.id
                    else:
                        # Conducteur : driver_id = user, creator_id = user
                        driver_id = db_user.id
                        creator_id = db_user.id
                    
                    new_trip = Trip(
                        driver_id=driver_id,
                        creator_id=creator_id,
                        trip_role=trip_role,
                        departure_city=departure_data.get('name', str(departure_data)),
                        arrival_city=arrival_data.get('name', str(arrival_data)),
                        departure_time=departure_time,
                        seats_available=context.user_data.get('seats'),
                        price_per_seat=context.user_data.get('price'),
                        is_published=True,
                        
                        # Marquer comme trajet régulier
                        recurring=True,
                        
                        # Options du trajet
                        smoking=trip_options.get('smoking', 'no_smoking'),
                        music=trip_options.get('music', 'music_ok'),
                        talk_preference=trip_options.get('talk', 'depends'),
                        pets_allowed=trip_options.get('pets', 'no_pets'),
                        luggage_size=trip_options.get('luggage', 'medium'),
                        stops=trip_options.get('stops', ''),
                        highway=trip_options.get('highway', True),
                        flexible_time=trip_options.get('flexible_time', False),
                        women_only=trip_options.get('women_only', False),
                        instant_booking=trip_options.get('instant_booking', True),
                        meeting_point=context.user_data.get('meeting_point', ''),
                        car_description=context.user_data.get('car_description', ''),
                        total_distance=context.user_data.get('total_distance', 0.0),
                        estimated_duration=context.user_data.get('estimated_duration', 0),
                        booking_deadline=departure_time,
                        additional_info=context.user_data.get('additional_info', '')
                    )
                    db.add(new_trip)
                    created_trips.append(new_trip)
                
                db.commit()
                logger.info(f"Créé {len(created_trips)} trajets réguliers.")
                
                # Message de confirmation pour trajets multiples
                dates_display = "\n".join([f"📅 {datetime.strptime(d, '%Y-%m-%d').strftime('%A %d %B %Y')}" for d in regular_dates[:5]])
                if len(regular_dates) > 5:
                    dates_display += f"\n... et {len(regular_dates) - 5} autres dates"
                
                keyboard_after_save = [
                    [InlineKeyboardButton("📋 Mes trajets", callback_data="main_menu:my_trips")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
                ]
                await query.edit_message_text(
                    f"✅ *Trajets réguliers créés avec succès!*\n\n"
                    f"🌍 De: {departure_data.get('name', str(departure_data))}\n"
                    f"🏁 À: {arrival_data.get('name', str(arrival_data))}\n\n"
                    f"📊 **{len(created_trips)} trajets créés:**\n"
                    f"{dates_display}\n\n"
                    f"Ils sont maintenant visibles pour les passagers potentiels.",
                    reply_markup=InlineKeyboardMarkup(keyboard_after_save),
                    parse_mode="Markdown"
                )
            elif trip_options.get('round_trip', False):
                # Créer un trajet aller-retour (deux trajets liés)
                
                # Configuration des IDs selon le rôle
                if trip_role == 'passenger':
                    # Passager : creator_id = user, driver_id = None (à remplir plus tard)
                    driver_id = None
                    creator_id = db_user.id
                else:
                    # Conducteur : driver_id = user, creator_id = user
                    driver_id = db_user.id
                    creator_id = db_user.id
                
                # Créer le trajet aller
                departure_datetime = context.user_data.get('datetime_obj')
                outbound_trip = Trip(
                    driver_id=driver_id,
                    creator_id=creator_id,
                    trip_role=trip_role,
                    departure_city=departure_data.get('name', str(departure_data)),
                    arrival_city=arrival_data.get('name', str(arrival_data)),
                    departure_time=departure_datetime,
                    seats_available=context.user_data.get('seats'),
                    price_per_seat=context.user_data.get('price'),
                    is_published=True,
                    
                    # Trajet simple (pas récurrent)
                    recurring=False,
                    
                    # Options du trajet
                    smoking=trip_options.get('smoking', 'no_smoking'),
                    music=trip_options.get('music', 'music_ok'),
                    talk_preference=trip_options.get('talk', 'depends'),
                    pets_allowed=trip_options.get('pets', 'no_pets'),
                    luggage_size=trip_options.get('luggage', 'medium'),
                    stops=trip_options.get('stops', ''),
                    highway=trip_options.get('highway', True),
                    flexible_time=trip_options.get('flexible_time', False),
                    women_only=trip_options.get('women_only', False),
                    instant_booking=trip_options.get('instant_booking', True),
                    meeting_point=context.user_data.get('meeting_point', ''),
                    car_description=context.user_data.get('car_description', ''),
                    total_distance=context.user_data.get('total_distance', 0.0),
                    estimated_duration=context.user_data.get('estimated_duration', 0),
                    booking_deadline=departure_datetime,
                    additional_info=context.user_data.get('additional_info', '')
                )
                db.add(outbound_trip)
                db.flush()  # Pour obtenir l'ID du trajet aller
                
                # Créer le trajet retour
                return_datetime = context.user_data.get('return_datetime_obj')
                return_trip = Trip(
                    driver_id=driver_id,
                    creator_id=creator_id,
                    trip_role=trip_role,
                    departure_city=arrival_data.get('name', str(arrival_data)),  # Inversé
                    arrival_city=departure_data.get('name', str(departure_data)),  # Inversé
                    departure_time=return_datetime,
                    seats_available=context.user_data.get('seats'),
                    price_per_seat=context.user_data.get('price'),
                    is_published=True,
                    
                    # Trajet simple (pas récurrent)
                    recurring=False,
                    
                    # Lien vers le trajet aller
                    return_trip_id=outbound_trip.id,
                    
                    # Options du trajet (identiques)
                    smoking=trip_options.get('smoking', 'no_smoking'),
                    music=trip_options.get('music', 'music_ok'),
                    talk_preference=trip_options.get('talk', 'depends'),
                    pets_allowed=trip_options.get('pets', 'no_pets'),
                    luggage_size=trip_options.get('luggage', 'medium'),
                    stops=trip_options.get('stops', ''),
                    highway=trip_options.get('highway', True),
                    flexible_time=trip_options.get('flexible_time', False),
                    women_only=trip_options.get('women_only', False),
                    instant_booking=trip_options.get('instant_booking', True),
                    meeting_point=context.user_data.get('meeting_point', ''),
                    car_description=context.user_data.get('car_description', ''),
                    total_distance=context.user_data.get('total_distance', 0.0),
                    estimated_duration=context.user_data.get('estimated_duration', 0),
                    booking_deadline=return_datetime,
                    additional_info=context.user_data.get('additional_info', '')
                )
                db.add(return_trip)
                
                # Mettre à jour le trajet aller avec la référence du retour
                outbound_trip.return_trip_id = return_trip.id
                
                db.commit()
                db.refresh(outbound_trip)
                db.refresh(return_trip)
                logger.info(f"Trajet aller-retour créé: aller ID {outbound_trip.id}, retour ID {return_trip.id}")

                keyboard_after_save = [
                    [InlineKeyboardButton("📋 Mes trajets", callback_data="main_menu:my_trips")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
                ]
                
                # Message adapté selon le rôle
                departure_date_str = departure_datetime.strftime('%d/%m/%Y à %H:%M') if departure_datetime else 'N/A'
                return_date_str = return_datetime.strftime('%d/%m/%Y à %H:%M') if return_datetime else 'N/A'
                
                if trip_role == 'passenger':
                    success_message = (
                        f"✅ *Demande d'aller-retour publiée avec succès!*\n\n"
                        f"🚗 **Aller :**\n"
                        f"📍 {outbound_trip.departure_city} → {outbound_trip.arrival_city}\n"
                        f"📅 {departure_date_str}\n\n"
                        f"🔄 **Retour :**\n"
                        f"📍 {return_trip.departure_city} → {return_trip.arrival_city}\n"
                        f"📅 {return_date_str}\n\n"
                        f"💰 Budget: {outbound_trip.price_per_seat} CHF/place (chaque trajet)\n\n"
                        f"🚗 *Votre demande est maintenant visible par les conducteurs.*\n"
                        f"Vous recevrez une notification quand un conducteur proposera ses services."
                    )
                else:
                    success_message = (
                        f"✅ *Trajet aller-retour créé avec succès!*\n\n"
                        f"🚗 **Aller :**\n"
                        f"📍 {outbound_trip.departure_city} → {outbound_trip.arrival_city}\n"
                        f"📅 {departure_date_str}\n\n"
                        f"🔄 **Retour :**\n"
                        f"📍 {return_trip.departure_city} → {return_trip.arrival_city}\n"
                        f"📅 {return_date_str}\n\n"
                        f"💰 Prix: {outbound_trip.price_per_seat} CHF/place (chaque trajet)\n"
                        f"💺 {outbound_trip.seats_available} places disponibles\n\n"
                        f"🌍 *Vos trajets sont maintenant visibles dans l'annuaire public.*"
                    )
                
                await query.edit_message_text(
                    success_message,
                    reply_markup=InlineKeyboardMarkup(keyboard_after_save),
                    parse_mode="Markdown"
                )
            else:
                # Créer un trajet simple normal
                
                # Configuration des IDs selon le rôle
                if trip_role == 'passenger':
                    # Passager : creator_id = user, driver_id = None (à remplir plus tard)
                    driver_id = None
                    creator_id = db_user.id
                else:
                    # Conducteur : driver_id = user, creator_id = user
                    driver_id = db_user.id
                    creator_id = db_user.id
                
                new_trip = Trip(
                    driver_id=driver_id,
                    creator_id=creator_id,
                    trip_role=trip_role,
                    departure_city=departure_data.get('name', str(departure_data)),
                    arrival_city=arrival_data.get('name', str(arrival_data)),
                    departure_time=context.user_data.get('datetime_obj'),
                    seats_available=context.user_data.get('seats'),
                    price_per_seat=context.user_data.get('price'),
                    is_published=True,
                    
                    # Trajet simple
                    recurring=False,
                    
                    # Options du trajet
                    smoking=trip_options.get('smoking', 'no_smoking'),
                    music=trip_options.get('music', 'music_ok'),
                    talk_preference=trip_options.get('talk', 'depends'),
                    pets_allowed=trip_options.get('pets', 'no_pets'),
                    luggage_size=trip_options.get('luggage', 'medium'),
                    stops=trip_options.get('stops', ''),
                    highway=trip_options.get('highway', True),
                    flexible_time=trip_options.get('flexible_time', False),
                    women_only=trip_options.get('women_only', False),
                    instant_booking=trip_options.get('instant_booking', True),
                    meeting_point=context.user_data.get('meeting_point', ''),
                    car_description=context.user_data.get('car_description', ''),
                    total_distance=context.user_data.get('total_distance', 0.0),
                    estimated_duration=context.user_data.get('estimated_duration', 0),
                    booking_deadline=context.user_data.get('datetime_obj'),
                    additional_info=context.user_data.get('additional_info', '')
                )
                db.add(new_trip)
                db.commit()
                db.refresh(new_trip)
                logger.info(f"Nouveau trajet ID {new_trip.id} sauvegardé en BDD.")

                keyboard_after_save = [
                    [InlineKeyboardButton("📋 Mes trajets", callback_data="main_menu:my_trips")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
                ]
                
                # Message adapté selon le rôle
                if trip_role == 'passenger':
                    success_message = (
                        f"✅ *Demande de trajet publiée avec succès!*\n\n"
                        f"🌍 De: {new_trip.departure_city}\n"
                        f"🏁 À: {new_trip.arrival_city}\n"
                        f"🗓️ Le: {new_trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                        f"💰 Budget: {new_trip.price_per_seat} CHF/place\n\n"
                        f"🚗 *Votre demande est maintenant visible par les conducteurs.*\n"
                        f"Vous recevrez une notification quand un conducteur proposera ses services."
                    )
                else:
                    success_message = (
                        f"✅ *Trajet créé avec succès!*\n\n"
                        f"🌍 De: {new_trip.departure_city}\n"
                        f"🏁 À: {new_trip.arrival_city}\n"
                        f"🗓️ Le: {new_trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                        f"💰 Prix: {new_trip.price_per_seat} CHF/place\n\n"
                        f"👥 *Il est maintenant visible pour les passagers potentiels.*"
                    )
                
                await query.edit_message_text(
                    success_message,
                    reply_markup=InlineKeyboardMarkup(keyboard_after_save),
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du trajet: {e}", exc_info=True)
            await query.edit_message_text("❌ Oups! Une erreur est survenue lors de la sauvegarde. Veuillez réessayer.")

    context.user_data.clear()
    return ConversationHandler.END

async def handle_create_cancel(update: Update, context: CallbackContext):
    """Annule la conversation de création de trajet."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Création de trajet annulée.")
    else:
        await update.message.reply_text("❌ Création de trajet annulée.")
    context.user_data.clear()
    return ConversationHandler.END

async def handle_unexpected_input(update: Update, context: CallbackContext):
    """Fonction de fallback pour gérer les entrées inattendues dans la conversation."""
    # Si le mode est "search", ne pas intercepter l'entrée
    if context.user_data.get('mode') == 'search':
        return -1  # -1 signifie "continuer à chercher d'autres gestionnaires"
        
    logger.warning(f"Entrée inattendue reçue dans la conversation create_trip: {update}")
    
    message = "Désolé, je n'ai pas compris cette entrée. Veuillez utiliser les options fournies."
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(message)
    elif update.message:
        await update.message.reply_text(message)
    
    # Retour à l'état actuel (ne pas terminer la conversation)
    return context.user_data.get('current_state', CREATE_TRIP_TYPE)

# Handler pour le bouton de publication (en dehors de la conversation)
async def publish_created_trip(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    trip_id = int(query.data.split(":")[1])
    
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        await query.edit_message_text("❌ Trajet introuvable.")
        return
    
    # Vérifier si le trajet appartient à l'utilisateur (sécurité additionnelle)
    # user_id = update.effective_user.id
    # if trip.driver.telegram_id != user_id: # ou une logique plus complexe si passagers peuvent publier
    #     await query.edit_message_text("❌ Vous n'êtes pas autorisé à publier ce trajet.")
    #     return

    trip.is_published = True
    db.commit()
    logger.info(f"Trajet ID {trip_id} publié.")
    
    keyboard_published = [
        [InlineKeyboardButton("📋 Mes trajets", callback_data="main_menu:my_trips")],
        [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
    ]
    await query.edit_message_text(
        f"✅ Trajet {trip.departure_city} → {trip.arrival_city} publié avec succès!",
        reply_markup=InlineKeyboardMarkup(keyboard_published)
    )

async def create_calendar_markup(year: int, month: int) -> InlineKeyboardMarkup:
    """Crée un clavier calendrier interactif."""
    keyboard = []
    current_date = datetime.now()
    logger.info(f"Création du calendrier pour {month}/{year}")
    
    # En-tête avec mois/année et navigation
    keyboard.append([
        InlineKeyboardButton("◀️", callback_data=f"create_cal_month:{year}:{month}:prev"),
        InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton("▶️", callback_data=f"create_cal_month:{year}:{month}:next")
    ])
    
    # Jours de la semaine
    days = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
    keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in days])
    
    # Obtenir le calendrier du mois
    month_cal = calendar.monthcalendar(year, month)
    
    # Ajouter les jours
    for week in month_cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                date = datetime(year, month, day)
                if date < current_date.replace(hour=0, minute=0, second=0, microsecond=0):
                    # Désactiver les dates passées
                    row.append(InlineKeyboardButton("✖️", callback_data="ignore"))
                else:
                    row.append(InlineKeyboardButton(
                        str(day),
                        callback_data=f"create_cal_date:{year}:{month}:{day}"
                    ))
        keyboard.append(row)
    
    # Bouton d'annulation
    keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_calendar_navigation(update: Update, context: CallbackContext):
    """Gère la navigation dans le calendrier."""
    query = update.callback_query
    await query.answer()
    logger.info(f"[CAL NAV] callback reçu: {query.data}")
    try:
        _, action, year, month = query.data.split(":")
        year, month = int(year), int(month)
        if action == "cal_month":
            # Extrait l'action (prev/next) depuis le 5ème élément
            action = query.data.split(":")[4] if len(query.data.split(":")) >= 5 else "none"
        
        if action == "prev":
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        elif action == "next":
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
        
        logger.info(f"[CAL NAV] Nouvelle date après navigation: {month}/{year}")
        markup = await create_calendar_markup(year, month)
        await query.edit_message_text(
            "📅 Sélectionnez la date du trajet:",
            reply_markup=markup
        )
        return CREATE_CALENDAR
    except Exception as e:
        logger.error(f"[CAL NAV] Erreur navigation calendrier: {str(e)}", exc_info=True)
        return CREATE_CALENDAR

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
    
    # Bouton d'annulation
    keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")])
    
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

async def handle_calendar_date_selection(update: Update, context: CallbackContext):
    """Gère la sélection d'une date dans le calendrier et passe à l'étape HOUR."""
    query = update.callback_query
    await query.answer()
    logger.info(f"[CAL DATE] callback reçu: {query.data}")
    
    try:
        # Extraire la date du callback
        parts = query.data.split(":")
        if len(parts) != 4:
            logger.error(f"[CAL DATE] Format callback invalide: {query.data}")
            raise ValueError(f"Format invalide: {query.data}")
        
        prefix, year, month, day = parts
        # Vérifier qu'il s'agit bien d'un callback de date de calendrier
        if prefix != "create_cal_date":
            logger.error(f"[CAL DATE] Préfixe de callback invalide: {prefix}")
            raise ValueError(f"Préfixe invalide: {prefix}")
            
        year, month, day = int(year), int(month), int(day)
        
        # Créer et stocker la date
        selected_date = datetime(year, month, day)
        context.user_data['selected_date'] = selected_date
        logger.info(f"[CAL DATE] Date sélectionnée: {selected_date}")
        
        # Vérifier si nous sommes dans le processus de sélection de retour
        is_selecting_return = context.user_data.get('selecting_return', False)
        logger.debug(f"[CAL DATE] is_selecting_return: {is_selecting_return}")
        logger.debug(f"[CAL DATE] IMPORTANT - État selecting_return: {is_selecting_return}")
        
        if is_selecting_return:
            logger.debug(f"[CAL DATE] IMPORTANT - Mode retour activé, affichage sélection heure retour")
            # Pour le retour, afficher un message plus clair
            departure = context.user_data.get('departure', {})
            arrival = context.user_data.get('arrival', {})
            departure_city = departure.get('name', str(departure)) if departure else 'N/A'
            arrival_city = arrival.get('name', str(arrival)) if arrival else 'N/A'
            
            # Afficher les options d'heures pour le retour
            hour_keyboard = await create_hour_selection_keyboard()
            await query.edit_message_text(
                f"🔄 *TRAJET ALLER-RETOUR - RETOUR*\n\n"
                f"� {arrival_city} → {departure_city}\n"
                f"�🗓️ *Date sélectionnée :* {selected_date.strftime('%d/%m/%Y')}\n\n"
                f"⏰ *Maintenant, sélectionnez l'HEURE de départ du retour :*",
                reply_markup=hour_keyboard,
                parse_mode="Markdown"
            )
            return RETURN_TIME
        else:
            # Pour l'aller, comportement normal
            hour_keyboard = await create_hour_selection_keyboard()
            await query.edit_message_text(
                f"🗓️ Date sélectionnée: {selected_date.strftime('%d/%m/%Y')}\n"
                f"⏰ Veuillez sélectionner l'heure du trajet:",
                reply_markup=hour_keyboard
            )
            return CREATE_TIME
    
    except Exception as e:
        logger.error(f"[CAL DATE] Erreur lors de la sélection de date: {str(e)}", exc_info=True)
        await query.edit_message_text(
            "❌ Une erreur s'est produite lors de la sélection de la date. Veuillez réessayer.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Réessayer", callback_data="create_trip:calendar_retry")
            ]])
        )
        return CREATE_CALENDAR

async def handle_unexpected_calendar_callback(update: Update, context: CallbackContext):
    """Intercepte tout callback inattendu dans le calendrier."""
    query = update.callback_query
    await query.answer()
    logger.warning(f"[CALENDAR] Callback inattendu reçu: {query.data}")
    
    # Vérifiez si c'est le bouton "ignore"
    if query.data == "ignore":
        return CREATE_CALENDAR
    
    await query.edit_message_text(
        "❌ Action non reconnue dans le calendrier.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Réessayer", callback_data="create_trip:calendar_retry")
        ]])
    )
    return CREATE_CALENDAR

# Fonction pour gérer le bouton de retry du calendrier
async def handle_calendar_retry(update: Update, context: CallbackContext):
    """Gère le bouton de réessai du calendrier."""
    query = update.callback_query
    await query.answer()
    
    # Afficher le calendrier du mois courant
    now = datetime.now()
    markup = await create_calendar_markup(now.year, now.month)
    
    await query.edit_message_text(
        "📅 Sélectionnez la date du trajet:",
        reply_markup=markup
    )
    return CREATE_CALENDAR

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
        
        # Vérifier si nous sommes dans le processus de sélection de retour
        is_selecting_return = context.user_data.get('selecting_return', False)
        logger.debug(f"[HOUR] is_selecting_return: {is_selecting_return}")
        logger.debug(f"[HOUR] IMPORTANT - État selecting_return: {is_selecting_return}")
        
        # Vérifier si c'est un trajet régulier
        regular_time_type = context.user_data.get('regular_time_type')
        
        if is_selecting_return:
            logger.debug(f"[HOUR] IMPORTANT - Mode retour, sélection minutes retour")
            # Pour le retour, afficher un message spécifique
            departure = context.user_data.get('departure', {})
            arrival = context.user_data.get('arrival', {})
            departure_city = departure.get('name', str(departure)) if departure else 'N/A'
            arrival_city = arrival.get('name', str(arrival)) if arrival else 'N/A'
            selected_date = context.user_data.get('selected_date', datetime.now())
            
            # Afficher les options de minutes
            minute_keyboard = await create_minute_selection_keyboard(hour)
            await query.edit_message_text(
                f"🔄 *TRAJET ALLER-RETOUR - RETOUR*\n\n"
                f"📍 {arrival_city} → {departure_city}\n"
                f"📅 {selected_date.strftime('%d/%m/%Y')}\n"
                f"🕐 *Heure sélectionnée :* {hour:02d}:XX\n\n"
                f"⏰ *Maintenant, sélectionnez les MINUTES :*",
                reply_markup=minute_keyboard,
                parse_mode="Markdown"
            )
            return CREATE_MINUTE
        
        elif regular_time_type:
            # Trajet régulier - afficher les options de minutes avec contexte approprié
            current_date = context.user_data.get('current_regular_date')
            if current_date:
                date_display = datetime.strptime(current_date, '%Y-%m-%d').strftime('%A %d %B %Y')
                message_prefix = f"📅 {date_display}\n⏱️ "
            else:
                message_prefix = "⏱️ "
        else:
            # Trajet simple
            message_prefix = "⏱️ "
        
        if not is_selecting_return:
            # Afficher les options de minutes
            minute_keyboard = await create_minute_selection_keyboard(hour)
            await query.edit_message_text(
                f"{message_prefix}Veuillez sélectionner les minutes:",
                reply_markup=minute_keyboard
            )
        
        return CREATE_MINUTE
    
    elif query.data == "create_back_to_calendar":
        # Retour au calendrier
        selected_date = context.user_data.get('selected_date', datetime.now())
        month = selected_date.month
        year = selected_date.year
        
        markup = await create_calendar_markup(year, month)
        await query.edit_message_text(
            "📅 Sélectionnez la date du trajet:",
            reply_markup=markup
        )
        return CREATE_CALENDAR
    
    # Fallback
    await query.edit_message_text(
        "❌ Action non reconnue. Veuillez réessayer.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Réessayer", callback_data="create_trip:calendar_retry")
        ]])
    )
    return CREATE_TIME

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
            return CREATE_CALENDAR
        
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
        
        # Créer des boutons de confirmation
        keyboard = [
            [InlineKeyboardButton("✅ Confirmer", callback_data="datetime:confirm")],
            [InlineKeyboardButton("🔄 Changer", callback_data="datetime:change")],
            [InlineKeyboardButton("❌ Annuler", callback_data="datetime:cancel")]
        ]
        
        # Afficher la date/heure sélectionnée avec confirmation
        await query.edit_message_text(
            f"📅 Date sélectionnée: {selected_date.strftime('%d/%m/%Y')}\n"
            f"⏰ Horaire: {flex_time_display}\n\n"
            f"Récapitulatif:\n"
            f"De: {departure_display}\n"
            f"À: {arrival_display}\n\n"
            "Confirmez-vous cette sélection?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CREATE_CONFIRM_DATETIME
    
    # Fallback
    await query.edit_message_text(
        "❌ Action non reconnue. Veuillez réessayer.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Réessayer", callback_data="create_trip:calendar_retry")
        ]])
    )
    return FLEX_HOUR

# === FONCTIONS POUR TRAJETS RÉGULIERS ===

def create_days_selection_keyboard(selected_days):
    """Crée le clavier pour la sélection des jours de la semaine."""
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    keyboard = []
    
    # Créer une rangée pour chaque jour
    for i, day in enumerate(days):
        if day in selected_days:
            button_text = f"✅ {day}"
        else:
            button_text = f"☑️ {day}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"regular_day_toggle:{i}")])
    
    # Ajouter les boutons de validation et d'annulation
    if selected_days:
        keyboard.append([
            InlineKeyboardButton("➡️ Continuer", callback_data="regular_days_continue"),
            InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")
        ])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_regular_day_toggle(update: Update, context: CallbackContext):
    """Gère l'activation/désactivation des jours de la semaine."""
    query = update.callback_query
    await query.answer()
    
    day_num = int(query.data.split(":")[1])
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    day_name = days[day_num]
    
    selected_days = context.user_data.get('selected_days', [])
    
    if day_name in selected_days:
        selected_days.remove(day_name)
    else:
        selected_days.append(day_name)
    
    context.user_data['selected_days'] = selected_days
    
    # Actualiser le clavier
    new_keyboard = create_days_selection_keyboard(selected_days)
    await query.edit_message_text(
        "📅 **Trajet régulier**\n\n"
        "Sélectionnez les jours de la semaine pour votre trajet régulier :",
        reply_markup=new_keyboard,
        parse_mode="Markdown"
    )
    
    return REGULAR_DAYS_SELECTION

async def handle_regular_days_continue(update: Update, context: CallbackContext):
    """Passe à la sélection du calendrier interactif."""
    query = update.callback_query
    await query.answer()
    
    selected_days = context.user_data.get('selected_days', [])
    if not selected_days:
        await query.answer("Veuillez sélectionner au moins un jour.", show_alert=True)
        return REGULAR_DAYS_SELECTION
    
    # Initialiser le calendrier pour le mois actuel
    now = datetime.now()
    context.user_data['calendar_year'] = now.year
    context.user_data['calendar_month'] = now.month
    context.user_data['selected_calendar_dates'] = set()
    
    # Afficher le calendrier interactif
    calendar_keyboard = create_interactive_calendar(now.year, now.month, selected_days, set())
    
    await query.edit_message_text(
        f"📅 **Sélection des dates précises**\n\n"
        f"🗓️ Jours choisis: {', '.join(selected_days)}\n\n"
        "Cliquez sur les dates que vous voulez pour vos trajets :\n"
        "✅ = Sélectionné\n"
        "☑️ = Disponible\n"
        "❌ = Jour non sélectionné",
        reply_markup=calendar_keyboard
    )
    
    return REGULAR_CALENDAR_SELECTION

def create_interactive_calendar(year, month, selected_days, selected_dates):
    """Crée un calendrier interactif pour la sélection de dates."""
    import calendar as cal
    
    # Créer le calendrier du mois
    month_calendar = cal.monthcalendar(year, month)
    days_mapping = {"Lundi": 0, "Mardi": 1, "Mercredi": 2, "Jeudi": 3, 
                   "Vendredi": 4, "Samedi": 5, "Dimanche": 6}
    
    keyboard = []
    
    # En-tête avec mois et année
    month_name = cal.month_name[month]
    keyboard.append([
        InlineKeyboardButton("⬅️", callback_data=f"cal_nav:prev:{year}:{month}"),
        InlineKeyboardButton(f"{month_name} {year}", callback_data="cal_nav:ignore"),
        InlineKeyboardButton("➡️", callback_data=f"cal_nav:next:{year}:{month}")
    ])
    
    # Jours de la semaine - maintenant cliquables pour sélection rapide
    keyboard.append([
        InlineKeyboardButton("L", callback_data="cal_day:select:0"),  # Lundi
        InlineKeyboardButton("M", callback_data="cal_day:select:1"),  # Mardi
        InlineKeyboardButton("M", callback_data="cal_day:select:2"),  # Mercredi
        InlineKeyboardButton("J", callback_data="cal_day:select:3"),  # Jeudi
        InlineKeyboardButton("V", callback_data="cal_day:select:4"),  # Vendredi
        InlineKeyboardButton("S", callback_data="cal_day:select:5"),  # Samedi
        InlineKeyboardButton("D", callback_data="cal_day:select:6")   # Dimanche
    ])
    
    # Dates du mois - MODIFICATION: Toutes les dates sont maintenant cliquables indépendamment
    for week in month_calendar:
        week_buttons = []
        for day in week:
            if day == 0:
                # Jour vide
                week_buttons.append(InlineKeyboardButton(" ", callback_data="cal_nav:ignore"))
            else:
                # Vérifier si cette date est sélectionnée
                date_str = f"{year}-{month:02d}-{day:02d}"
                today = datetime.now().date()
                date_obj = datetime(year, month, day).date()
                
                if date_obj < today:
                    # Date passée - non cliquable
                    week_buttons.append(InlineKeyboardButton(f"❌{day}", callback_data="cal_nav:ignore"))
                elif date_str in selected_dates:
                    # Date sélectionnée - cliquable pour désélectionner
                    week_buttons.append(InlineKeyboardButton(f"✅{day}", callback_data=f"cal_date:toggle:{date_str}"))
                else:
                    # Date disponible - cliquable pour sélectionner
                    week_buttons.append(InlineKeyboardButton(f"☑️{day}", callback_data=f"cal_date:toggle:{date_str}"))
        
        keyboard.append(week_buttons)
    
    # Boutons d'action
    keyboard.append([
        InlineKeyboardButton("🗑️ Effacer tout", callback_data="cal_date:clear"),
        InlineKeyboardButton("✅ Confirmer", callback_data="cal_date:confirm")
    ])
    keyboard.append([
        InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_calendar_interaction(update: Update, context: CallbackContext):
    """Gère les interactions avec le calendrier interactif."""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(":")
    
    if data_parts[0] == "cal_nav":
        if data_parts[1] == "ignore":
            return REGULAR_CALENDAR_SELECTION
        elif data_parts[1] in ["prev", "next"]:
            # Navigation entre mois
            year = int(data_parts[2])
            month = int(data_parts[3])
            
            if data_parts[1] == "prev":
                if month == 1:
                    month = 12
                    year -= 1
                else:
                    month -= 1
            else:  # next
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
            
            context.user_data['calendar_year'] = year
            context.user_data['calendar_month'] = month
            
            selected_days = context.user_data.get('selected_days', [])
            selected_dates = context.user_data.get('selected_calendar_dates', set())
            
            calendar_keyboard = create_interactive_calendar(year, month, selected_days, selected_dates)
            
            await query.edit_message_text(
                f"📅 **Sélection des dates précises**\n\n"
                f"🗓️ Jours choisis: {', '.join(selected_days)}\n\n"
                "Cliquez sur les dates que vous voulez pour vos trajets :\n"
                "✅ = Sélectionné\n"
                "☑️ = Disponible\n"
                "❌ = Jour non sélectionné",
                reply_markup=calendar_keyboard
            )
            
    elif data_parts[0] == "cal_day":
        # Sélection rapide d'un jour de la semaine
        if data_parts[1] == "select":
            weekday_index = int(data_parts[2])
            weekday_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            selected_weekday = weekday_names[weekday_index]
            
            # Initialiser ou récupérer les données
            selected_days = context.user_data.get('selected_days', [])
            selected_dates = context.user_data.get('selected_calendar_dates', set())
            
            # Basculer la sélection de ce jour de la semaine
            if selected_weekday in selected_days:
                # Désélectionner ce jour
                selected_days.remove(selected_weekday)
                # Retirer toutes les dates de ce jour du calendrier
                year = context.user_data['calendar_year']
                month = context.user_data['calendar_month']
                dates_to_remove = []
                for date_str in selected_dates:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    if date_obj.weekday() == weekday_index and date_obj.year == year and date_obj.month == month:
                        dates_to_remove.append(date_str)
                for date_str in dates_to_remove:
                    selected_dates.remove(date_str)
            else:
                # Sélectionner ce jour
                selected_days.append(selected_weekday)
                # Ajouter toutes les dates futures de ce jour dans le mois actuel
                year = context.user_data['calendar_year']
                month = context.user_data['calendar_month']
                today = datetime.now().date()
                
                import calendar as cal
                month_calendar = cal.monthcalendar(year, month)
                for week in month_calendar:
                    for day in week:
                        if day != 0:
                            date_obj = datetime(year, month, day).date()
                            if date_obj >= today and date_obj.weekday() == weekday_index:
                                selected_dates.add(f"{year}-{month:02d}-{day:02d}")
            
            context.user_data['selected_days'] = selected_days
            context.user_data['selected_calendar_dates'] = selected_dates
            
            # Mettre à jour l'affichage du calendrier
            calendar_keyboard = create_interactive_calendar(
                context.user_data['calendar_year'],
                context.user_data['calendar_month'],
                selected_days,
                selected_dates
            )
            
            await query.edit_message_text(
                f"📅 **Trajet régulier - Sélection des dates**\n\n"
                f"🗓️ Jours sélectionnés: {', '.join(selected_days) if selected_days else 'Aucun'}\n"
                f"📍 Dates sélectionnées: {len(selected_dates)} date(s)\n\n"
                f"Cliquez directement sur les dates pour les sélectionner/désélectionner\n"
                f"Ou utilisez **L, M, M, J, V, S, D** pour sélectionner tous les jours de cette semaine\n\n"
                f"✅ = Sélectionné\n"
                f"☑️ = Disponible\n"
                f"❌ = Date passée",
                reply_markup=calendar_keyboard,
                parse_mode="Markdown"
            )
            
    elif data_parts[0] == "cal_date":
        if data_parts[1] == "toggle":
            # Basculer une date
            date_str = data_parts[2]
            selected_dates = context.user_data.get('selected_calendar_dates', set())
            
            if date_str in selected_dates:
                selected_dates.remove(date_str)
            else:
                selected_dates.add(date_str)
            
            context.user_data['selected_calendar_dates'] = selected_dates
            
            year = context.user_data['calendar_year']
            month = context.user_data['calendar_month']
            selected_days = context.user_data.get('selected_days', [])
            
            calendar_keyboard = create_interactive_calendar(year, month, selected_days, selected_dates)
            
            await query.edit_message_text(
                f"📅 **Sélection des dates précises**\n\n"
                f"🗓️ Jours choisis: {', '.join(selected_days)}\n\n"
                f"📊 **Dates sélectionnées:** {len(selected_dates)}\n\n"
                "Cliquez sur les dates que vous voulez pour vos trajets :\n"
                "✅ = Sélectionné\n"
                "☑️ = Disponible\n"
                "❌ = Jour non sélectionné",
                reply_markup=calendar_keyboard
            )
            
        elif data_parts[1] == "clear":
            # Effacer toutes les dates
            context.user_data['selected_calendar_dates'] = set()
            
            year = context.user_data['calendar_year']
            month = context.user_data['calendar_month']
            selected_days = context.user_data.get('selected_days', [])
            
            calendar_keyboard = create_interactive_calendar(year, month, selected_days, set())
            
            await query.edit_message_text(
                f"📅 **Sélection des dates précises**\n\n"
                f"🗓️ Jours choisis: {', '.join(selected_days)}\n\n"
                "Cliquez sur les dates que vous voulez pour vos trajets :\n"
                "✅ = Sélectionné\n"
                "☑️ = Disponible\n"
                "❌ = Jour non sélectionné",
                reply_markup=calendar_keyboard
            )
            
        elif data_parts[1] == "confirm":
            # Confirmer les dates sélectionnées
            selected_dates = context.user_data.get('selected_calendar_dates', set())
            
            if not selected_dates:
                await query.answer("Veuillez sélectionner au moins une date.", show_alert=True)
                return REGULAR_CALENDAR_SELECTION
            
            # Convertir en format lisible et continuer vers la sélection des villes
            dates_list = sorted(list(selected_dates))
            context.user_data['regular_dates'] = dates_list
            
            # Continuer vers la sélection de la ville de départ
            keyboard_dep = [
                [InlineKeyboardButton(city, callback_data=f"create_dep_city:{city}")] 
                for city in SWISS_CITIES_SUGGESTIONS[:5]
            ]
            keyboard_dep.append([InlineKeyboardButton("Autre ville...", callback_data="create_dep_other")])
            keyboard_dep.append([InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel")])
            
            dates_display = "\n".join([f"📅 {datetime.strptime(d, '%Y-%m-%d').strftime('%A %d %B %Y')}" for d in dates_list[:5]])
            if len(dates_list) > 5:
                dates_display += f"\n... et {len(dates_list) - 5} autres dates"
            
            await query.edit_message_text(
                f"✅ **Dates confirmées pour vos trajets réguliers**\n\n"
                f"{dates_display}\n\n"
                f"📊 **Total:** {len(dates_list)} trajet{'s' if len(dates_list) > 1 else ''}\n\n"
                "Maintenant, choisissez votre ville de départ :",
                reply_markup=InlineKeyboardMarkup(keyboard_dep)
            )
            return CREATE_DEPARTURE
    
    return REGULAR_CALENDAR_SELECTION

# --- HANDLERS pour les boutons après création de trajet ---
async def handle_show_my_trips(update: Update, context: CallbackContext):
    """Affiche la liste des trajets de l'utilisateur après création."""
    query = update.callback_query
    await query.answer()
    
    # Import dynamique pour éviter les imports circulaires
    from handlers.trip_handlers import list_my_trips
    
    # Appel de la vraie fonction de listage des trajets
    return await list_my_trips(update, context)

async def handle_main_menu(update: Update, context: CallbackContext):
    """Affiche le menu principal après création de trajet."""
    query = update.callback_query
    await query.answer()
    
    # Import dynamique pour éviter les imports circulaires
    from handlers.menu_handlers import start_command
    
    # Appel de la vraie fonction du menu principal
    return await start_command(update, context)

# ConversationHandler pour la création de trajet
create_trip_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('creer', start_create_trip),
        CommandHandler('creer_trajet', start_create_trip),  # Ajout pour le menu hamburger
        CallbackQueryHandler(start_create_trip, pattern='^creer_trajet$'),
        CallbackQueryHandler(start_create_trip, pattern='^menu:create$'),
        CallbackQueryHandler(start_create_trip, pattern='^main_menu:create_trip$')
    ],
    states={
        CREATE_TRIP_TYPE: [
            CallbackQueryHandler(handle_create_trip_type, pattern='^create_trip_type:(driver|passenger)$'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel')
        ],
        CREATE_TRIP_OPTIONS: [
            CallbackQueryHandler(handle_create_trip_options, pattern='^create_trip_option:'),
            CallbackQueryHandler(handle_create_trip_options, pattern='^create_trip_options:continue$'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel')
        ],
        CREATE_DEPARTURE: [
            CallbackQueryHandler(handle_create_departure_city_callback, pattern='^create_dep_city:'),
            CallbackQueryHandler(handle_create_departure_city_callback, pattern='^create_dep_other$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_departure_text),
            CallbackQueryHandler(handle_create_departure_loc_callback, pattern='^create_dep_loc:'),
            CallbackQueryHandler(handle_create_departure_loc_callback, pattern='^create_dep_retry_text$'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel')
        ],
        CREATE_ARRIVAL: [
            CallbackQueryHandler(handle_create_arrival_city_callback, pattern='^create_arr_city:'),
            CallbackQueryHandler(handle_create_arrival_city_callback, pattern='^create_arr_other$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_arrival_text),
            CallbackQueryHandler(handle_create_arrival_loc_callback, pattern='^create_arr_loc:'),
            CallbackQueryHandler(handle_create_arrival_loc_callback, pattern='^create_arr_retry_text$'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel$')
        ],
        CREATE_CALENDAR: [
            # IMPORTANT: Order matters! The most specific patterns should come first
            CallbackQueryHandler(handle_calendar_date_selection, pattern=r"^create_cal_date:\d+:\d+:\d+$"),
            CallbackQueryHandler(handle_calendar_navigation, pattern=r"^create_cal_month:\d+:\d+:(prev|next)$"),
            CallbackQueryHandler(handle_calendar_retry, pattern=r"^create_trip:calendar_retry$"),
            CallbackQueryHandler(handle_create_cancel, pattern=r"^create_trip:cancel$"),
            CallbackQueryHandler(handle_unexpected_calendar_callback)  # Catch-all for unexpected callbacks
        ],
        HOUR: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hour_input),
        ],
        CREATE_TIME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_time_input),
            CallbackQueryHandler(handle_hour_selection, pattern=r"^create_hour:\d+$"),
            CallbackQueryHandler(handle_flex_time_selection, pattern=r"^create_flex_time:(morning|afternoon|evening|tbd)$"),
            CallbackQueryHandler(handle_create_cancel, pattern="^create_trip:cancel$")
        ],
        CREATE_MINUTE: [
            CallbackQueryHandler(handle_minute_selection, pattern=r"^create_minute:\d+:\d+$"),
            CallbackQueryHandler(handle_hour_selection, pattern="^create_back_to_hour$"),
            CallbackQueryHandler(handle_create_cancel, pattern="^create_trip:cancel$")
        ],
        CREATE_CONFIRM_DATETIME: [
            CallbackQueryHandler(handle_create_date_confirmed, pattern="^datetime:confirm$"),
            CallbackQueryHandler(handle_calendar_retry, pattern="^datetime:change$"),
            CallbackQueryHandler(handle_create_cancel, pattern="^datetime:cancel$")
        ],
        CREATE_SEATS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_seats)
        ],
        CREATE_CONFIRM: [
            CallbackQueryHandler(handle_create_confirm, pattern='^create_confirm_yes$'),
            CallbackQueryHandler(handle_show_my_trips, pattern='^main_menu:my_trips$'),
            CallbackQueryHandler(handle_main_menu, pattern='^main_menu:start$'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel_confirm$')
        ],
        FLEX_HOUR: [
            CallbackQueryHandler(handle_flex_time_selection, pattern="^(create_flex_time:(morning|afternoon|evening|tbd)|time:\d{1,2}:\d{2}|flex_time:(morning|afternoon|evening|tbd|manual))$"),
        ],
        # Nouveaux états pour trajets réguliers
        REGULAR_DAYS_SELECTION: [
            CallbackQueryHandler(handle_regular_day_toggle, pattern='^regular_day_toggle:\d+$'),
            CallbackQueryHandler(handle_regular_days_continue, pattern='^regular_days_continue$'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel$')
        ],
        REGULAR_CALENDAR_SELECTION: [
            CallbackQueryHandler(handle_calendar_interaction, pattern='^cal_nav:'),
            CallbackQueryHandler(handle_calendar_interaction, pattern='^cal_date:'),
            CallbackQueryHandler(handle_calendar_interaction, pattern='^cal_day:'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel$')
        ],
        REGULAR_TIME_TYPE: [
            CallbackQueryHandler(handle_regular_time_type, pattern='^regular_time:(same|individual)$'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel$')
        ],
        # Nouveaux états pour trajets aller-retour
        RETURN_DATE: [
            # Utiliser les mêmes handlers que pour la date normale
            CallbackQueryHandler(handle_calendar_date_selection, pattern=r"^create_cal_date:\d+:\d+:\d+$"),
            CallbackQueryHandler(handle_calendar_navigation, pattern=r"^create_cal_month:\d+:\d+:(prev|next)$"),
            CallbackQueryHandler(handle_calendar_retry, pattern=r"^create_trip:calendar_retry$"),
            CallbackQueryHandler(handle_create_cancel, pattern=r"^create_trip:cancel$"),
            CallbackQueryHandler(handle_unexpected_calendar_callback)
        ],
        RETURN_TIME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_time_input),
            CallbackQueryHandler(handle_hour_selection, pattern=r"^create_hour:\d+$"),
            CallbackQueryHandler(handle_flex_time_selection, pattern=r"^create_flex_time:(morning|afternoon|evening|tbd)$"),
            CallbackQueryHandler(handle_create_cancel, pattern="^create_trip:cancel$")
        ],
        RETURN_CONFIRM_DATETIME: [
            CallbackQueryHandler(handle_return_date_confirmed, pattern="^datetime:confirm$"),
            CallbackQueryHandler(handle_calendar_retry, pattern="^datetime:change$"),
            CallbackQueryHandler(handle_create_cancel, pattern="^datetime:cancel$")
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel'),
        CommandHandler('cancel', handle_create_cancel),
        MessageHandler(filters.ALL & ~filters.Command(['chercher']), handle_unexpected_input)
    ],
    name="create_trip_conversation",
    persistent=True,
    allow_reentry=True,
    per_message=False,
    per_chat=False,
    per_user=True  # Chaque utilisateur a sa propre conversation
)

publish_trip_handler = CallbackQueryHandler(publish_created_trip, pattern=r"^publish_trip:\d+$")

# Handlers globaux pour les boutons après création de trajet
main_menu_handler = CallbackQueryHandler(handle_main_menu, pattern=r"^main_menu:start$")
my_trips_handler = CallbackQueryHandler(handle_show_my_trips, pattern=r"^main_menu:my_trips$")
