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
    HOUR  # État pour la saisie de l'heure après la date
) = range(14)

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
        
        await update.message.reply_text(
            f"📅 Date et heure sélectionnées: {selected_datetime.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Récapitulatif:\n"
            f"De: {departure_display}\n"
            f"À: {arrival_display}\n\n"
            "Étape 6️⃣ - Combien de places disponibles? (1-8)"
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
    minute = int(query.data.split(":")[1])
    hour = context.user_data.get('selected_hour', 0)
    selected_date = context.user_data.get('selected_date', datetime.now())
    selected_datetime = selected_date.replace(hour=hour, minute=minute)
    context.user_data['selected_datetime'] = selected_datetime
    await query.edit_message_text(
        f"Heure sélectionnée: {hour:02d}:{minute:02d}\n"
        f"Date et heure finale: {selected_datetime.strftime('%d/%m/%Y à %H:%M')}"
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
    context.user_data.clear()
    context.user_data['mode'] = 'create'
    context.user_data['current_state'] = CREATE_TRIP_TYPE # For fallback
    logger.info("Mode réglé sur 'create' dans start_create_trip")
    
    keyboard = [
        [
            InlineKeyboardButton("🚗 Conducteur", callback_data="create_trip_type:driver"),
            InlineKeyboardButton("🧍 Passager", callback_data="create_trip_type:passenger")
        ],
        [InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel_initial")]
    ]
    
    message_text = "🚗 *Création d'un nouveau trajet*\n\nÉtape 1️⃣ - Choisissez votre rôle pour ce trajet:"
    
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
    return CREATE_TRIP_TYPE

async def handle_create_trip_type(update: Update, context: CallbackContext):
    """Gère le choix du type de trajet (conducteur/passager)."""
    query = update.callback_query
    await query.answer()
    
    try:
        # query.data will be "create_trip_type:driver" or "create_trip_type:passenger"
        choice = query.data.split(":")[1] 
        logger.info(f"✅ Callback reçu dans handle_create_trip_type: {query.data}, choix: {choice}")
            
        context.user_data['trip_type'] = choice
        logger.info(f"Type de trajet (création) enregistré: {choice}")
        
        context.user_data['current_state'] = CREATE_TRIP_OPTIONS
        return await show_create_trip_options(update, context) # show_create_trip_options should return CREATE_TRIP_OPTIONS
    except Exception as e:
        logger.error(f"Erreur dans handle_create_trip_type: {e}")
        await query.message.reply_text("Une erreur s'est produite. Veuillez réessayer.")
        return ConversationHandler.END

async def show_create_trip_options(update: Update, context: CallbackContext):
    """Affiche les options supplémentaires pour la création de trajet."""
    logger.info(f"Entrée dans show_create_trip_options avec update type: {type(update)}")
    query = update.callback_query if hasattr(update, 'callback_query') else None
    
    if 'trip_options' not in context.user_data:
        context.user_data['trip_options'] = {}
    
    keyboard_options = [
        [InlineKeyboardButton(f"{'✅' if context.user_data['trip_options'].get('simple', False) else '☑️'} Trajet simple", callback_data="create_trip_option:simple")],
        [
            InlineKeyboardButton(f"{'✅' if context.user_data['trip_options'].get('regular', False) else '☑️'} Trajet régulier", callback_data="create_trip_option:regular"),
            InlineKeyboardButton(f"{'✅' if context.user_data['trip_options'].get('round_trip', False) else '☑️'} Aller-retour", callback_data="create_trip_option:round_trip")
        ]
        # Potentially "women_only" option here
    ]
    keyboard_options.append([
        InlineKeyboardButton("▶️ Continuer", callback_data="create_trip_options:continue"),
        InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel_options")
    ])
    
    role_text = "conducteur" if context.user_data.get('trip_type') == "driver" else "passager"
    message_text = (
        f"🚗 *Création d'un nouveau trajet* ({role_text})\n\n"
        f"Étape 2️⃣ - Options supplémentaires (optionnel):\n"
        f"Cliquez sur une option pour l'activer/désactiver."
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
        context.user_data['trip_options'][option] = not context.user_data['trip_options'].get(option, False)
        return await show_create_trip_options(update, context) # Refresh options view

    elif query.data == "create_trip_options:continue":
        # Transition to departure city selection
        context.user_data['current_state'] = CREATE_DEPARTURE
        # ... (code to ask for departure city)
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
        
        # Afficher le calendrier de sélection de date
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

            # Afficher le calendrier de sélection de date
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
    
    departure = context.user_data.get('departure', {})
    arrival = context.user_data.get('arrival', {})
    departure_display = departure.get('name', str(departure)) if departure else 'N/A'
    arrival_display = arrival.get('name', str(arrival)) if arrival else 'N/A'
    date_display = context.user_data['date']

    message_text = (
        f"Récapitulatif partiel:\n"
        f"De: {departure_display}\n"
        f"À: {arrival_display}\n"
        f"Date: {date_display}\n\n"
        "Étape 6️⃣ - Combien de places disponibles? (1-8)"
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
    logger.info(f"Nombre de sièges (création): {seats_text}")
    
    await update.message.reply_text("Étape 7️⃣ - Quel est le prix par place en CHF?")
    return CREATE_PRICE

async def handle_create_price(update: Update, context: CallbackContext):
    """Gère l'entrée du prix."""
    price_text = update.message.text
    if not validate_price(price_text):
        await update.message.reply_text("❌ Prix invalide. Entrez un montant entre 0 et 1000 CHF.")
        return CREATE_PRICE
        
    context.user_data['price'] = float(price_text)
    logger.info(f"Prix (création): {price_text}")
    
    # Afficher le résumé pour confirmation
    dep = context.user_data.get('departure', {})
    arr = context.user_data.get('arrival', {})
    dep_display = dep.get('name', dep) if isinstance(dep, dict) else dep
    arr_display = arr.get('name', arr) if isinstance(arr, dict) else arr
    
    summary = (
        "📋 *Résumé du trajet à créer*:\n\n"
        f"Rôle: {context.user_data.get('trip_type', 'N/A')}\n"
        f"Options: {context.user_data.get('trip_options', {})}\n"
        f"De: {dep_display}\n"
        f"À: {arr_display}\n"
        f"Date: {context.user_data.get('date', 'N/A')}\n"
        f"Places: {context.user_data.get('seats', 'N/A')}\n"
        f"Prix: {context.user_data.get('price', 'N/A')} CHF\n\n"
        "Confirmez-vous la création de ce trajet?"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Confirmer", callback_data="create_confirm_yes")],
        [InlineKeyboardButton("❌ Annuler", callback_data="create_trip:cancel_confirm")]
    ]
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CREATE_CONFIRM

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

            new_trip = Trip(
                driver_id=db_user.id,
                departure_city=departure_data.get('name', str(departure_data)),
                departure_zip=departure_data.get('zip'),
                departure_canton=departure_data.get('canton'),
                arrival_city=arrival_data.get('name', str(arrival_data)),
                arrival_zip=arrival_data.get('zip'),
                arrival_canton=arrival_data.get('canton'),
                departure_time=context.user_data.get('datetime_obj'),
                available_seats=context.user_data.get('seats'),
                price_per_seat=context.user_data.get('price'),
                trip_type=context.user_data.get('trip_type'),
                options=json.dumps(context.user_data.get('trip_options', {})),
                is_published=False
            )
            db.add(new_trip)
            db.commit()
            db.refresh(new_trip)
            logger.info(f"Nouveau trajet ID {new_trip.id} sauvegardé en BDD.")

            keyboard_after_save = [
                [InlineKeyboardButton("🚀 Publier ce trajet", callback_data=f"publish_trip:{new_trip.id}")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
            ]
            await query.edit_message_text(
                f"🎉 Trajet sauvegardé comme brouillon !\n"
                f"🌍 De: {new_trip.departure_city}\n"
                f"🏁 À: {new_trip.arrival_city}\n"
                f"🗓️ Le: {new_trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                "Vous pouvez le publier maintenant ou plus tard depuis 'Mes trajets'.",
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
            
        _, year, month, day = parts
        year, month, day = int(year), int(month), int(day)
        
        # Créer et stocker la date
        selected_date = datetime(year, month, day)
        context.user_data['selected_date'] = selected_date
        logger.info(f"[CAL DATE] Date sélectionnée: {selected_date}")
        
        # Demander l'heure
        await query.edit_message_text(
            f"🗓️ Date sélectionnée: {selected_date.strftime('%d/%m/%Y')}\n"
            f"Veuillez entrer l'heure du trajet (exemple: 13:30):",
            reply_markup=None
        )
        
        logger.info("[CAL DATE] Transition vers l'état HOUR")
        return HOUR
    
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

# ConversationHandler pour la création de trajet
create_trip_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('creer', start_create_trip),
        CallbackQueryHandler(start_create_trip, pattern='^creer_trajet$')
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
            CallbackQueryHandler(handle_create_cancel, pattern="^create_trip:cancel$")
        ],
        CREATE_MINUTE: [
            CallbackQueryHandler(handle_minute_selection, pattern=r"^minute:\d+$"),
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
        CREATE_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_price)
        ],
        CREATE_CONFIRM: [
            CallbackQueryHandler(handle_create_confirm, pattern='^create_confirm_yes$'),
            CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel_confirm$')
        ],
        FLEX_HOUR: [
            CallbackQueryHandler(handle_flex_time_selection, pattern="^(time:\d{1,2}:\d{2}|flex_time:(morning|afternoon|evening|tbd|manual))$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_create_cancel, pattern='^create_trip:cancel'),
        CommandHandler('cancel', handle_create_cancel),
        MessageHandler(filters.ALL, handle_unexpected_input)
    ],
    name="create_trip_conversation",
    persistent=True,
    allow_reentry=True,
    per_message=False
)

publish_trip_handler = CallbackQueryHandler(publish_created_trip, pattern=r"^publish_trip:\d+$")
