import logging
import json # Ajout de l'import json
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
    handle_flex_time_selection,
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
    CREATE_DATE, # Ce nom d'état pourrait être redondant si date_picker gère tout
    CREATE_SEATS,
    CREATE_PRICE,
    CREATE_CONFIRM,
    CREATE_CALENDAR, 
    CREATE_TIME,     
    CREATE_MINUTE,   
    CREATE_CONFIRM_DATETIME 
) = range(12)

# Charger les villes au démarrage
def load_cities_list():
    """Charge les villes depuis swiss_localities.json pour les suggestions."""
    try:
        localities = load_all_localities() # Utilise la fonction de utils.swiss_cities
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
        return sorted([
            "Zürich", "Genève", "Bâle", "Lausanne", "Berne", 
            "Lucerne", "Fribourg", "Neuchâtel", "Sion"
        ])

SWISS_CITIES_SUGGESTIONS = load_cities_list()


async def start_create_trip(update: Update, context: CallbackContext):
    """Lance le processus de création de trajet."""
    context.user_data.clear()
    context.user_data['mode'] = 'create'
    context.user_data['current_state'] = CREATE_TRIP_TYPE
    logger.info("Mode réglé sur 'create' dans start_create_trip")
    
    keyboard = [
        [
            InlineKeyboardButton("🚗 Conducteur", callback_data="create_trip_type:driver"),
            InlineKeyboardButton("🧍 Passager", callback_data="create_trip_type:passenger")
        ],
        [InlineKeyboardButton("❌ Annuler", callback_data="create_cancel")]
    ]
    
    message_text = "👋 Bienvenue dans la création de trajet !\n\n🚗 Étape 1️⃣ - Choisissez votre rôle pour ce trajet:"
    
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
        choice = query.data.split(":")[1]
        logger.info(f"✅ Callback reçu dans handle_create_trip_type: {query.data}, choix: {choice}")
        
        # if choice == "cancel": # Déjà géré par le fallback create_cancel
        #     await query.edit_message_text("❌ Création de trajet annulée.")
        #     context.user_data.clear()
        #     return ConversationHandler.END
            
        context.user_data['trip_type'] = choice
        logger.info(f"Type de trajet (création) enregistré: {choice}")
        
        context.user_data['current_state'] = CREATE_TRIP_OPTIONS
        return await show_create_trip_options(update, context)
    except Exception as e:
        logger.error(f"Erreur dans handle_create_trip_type: {e}")
        await query.message.reply_text("Une erreur s'est produite. Veuillez réessayer.")
        context.user_data.clear()
        return ConversationHandler.END

async def show_create_trip_options(update: Update, context: CallbackContext):
    """Affiche les options supplémentaires pour la création de trajet."""
    logger.info(f"Entrée dans show_create_trip_options avec update type: {type(update)}")
    query = update.callback_query if hasattr(update, 'callback_query') else None
    
    if query:
        logger.info(f"Query data: {query.data}")
    else:
        logger.warning("Aucune query disponible dans show_create_trip_options")

    if 'trip_options' not in context.user_data:
        context.user_data['trip_options'] = {}
    
    # trip_type = context.user_data.get('trip_type', '') # Non utilisé directement ici
    # is_woman = False # Placeholder, à remplacer par une vraie vérification si pertinent
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if context.user_data['trip_options'].get('simple', False) else '☑️'} Trajet simple", 
                callback_data="create_trip_option:simple"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if context.user_data['trip_options'].get('regular', False) else '☑️'} Trajet régulier", 
                callback_data="create_trip_option:regular"
            ),
            InlineKeyboardButton(
                f"{'✅' if context.user_data['trip_options'].get('round_trip', False) else '☑️'} Aller-retour", 
                callback_data="create_trip_option:round_trip"
            )
        ]
        # if is_woman: # Logique pour "Entre femmes" à affiner
        #     keyboard.append([
        #         InlineKeyboardButton(
        #             f"{'✅' if context.user_data['trip_options'].get('women_only', False) else '☑️'} 🚺 Entre femmes uniquement", 
        #             callback_data="create_trip_option:women_only"
        #         )
        #     ])
    ]
    keyboard.append([
        InlineKeyboardButton("▶️ Continuer", callback_data="create_trip_options:continue"),
        InlineKeyboardButton("❌ Annuler", callback_data="create_cancel")
    ])
    
    role = context.user_data.get('trip_type', 'conducteur')
    role_text = "🚗 conducteur" if role == "driver" else "🧍 passager"
    
    message_text = (
        f"📝 *Création d'un nouveau trajet* ({role_text})\n\n"
        f"⚙️ Étape 2️⃣ - Options supplémentaires (optionnel):\n"
        f"Cliquez sur une option pour l'activer/désactiver."
    )
    
    if query:
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else: 
        await update.effective_message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    return CREATE_TRIP_OPTIONS

async def handle_create_trip_options(update: Update, context: CallbackContext):
    """Gère la sélection des options de trajet."""
    query = update.callback_query
    await query.answer()
    
    action_part = query.data.split(":")[1] # e.g. "simple", "regular", "continue", "cancel"
    
    if action_part == "continue":
        context.user_data['current_state'] = CREATE_DEPARTURE
        keyboard_dep = [
            [InlineKeyboardButton(f"📍 {city}", callback_data=f"create_dep_city:{city}")] for city in SWISS_CITIES_SUGGESTIONS[:3] # Moins de suggestions initiales
        ]
        keyboard_dep.append([InlineKeyboardButton("🏙️ Autre ville...", callback_data="create_dep_other")])
        keyboard_dep.append([InlineKeyboardButton("❌ Annuler", callback_data="create_cancel")])
        await query.edit_message_text("🌍 Étape 3️⃣ - Choisissez votre ville de départ:", reply_markup=InlineKeyboardMarkup(keyboard_dep))
        return CREATE_DEPARTURE
        
    # elif action_part == "cancel": # Géré par le fallback create_cancel
    #     await query.edit_message_text("❌ Création de trajet annulée.")
    #     context.user_data.clear()
    #     return ConversationHandler.END
        
    else: # C'est une option à activer/désactiver (simple, regular, round_trip, women_only)
        option_key = action_part
        context.user_data.setdefault('trip_options', {})
        context.user_data['trip_options'][option_key] = not context.user_data['trip_options'].get(option_key, False)
        logger.info(f"Option '{option_key}' mise à jour: {context.user_data['trip_options'][option_key]}")
        return await show_create_trip_options(update, context) # Rafraîchir la vue des options

async def handle_create_departure_city_callback(update: Update, context: CallbackContext):
    """Gère le clic sur un bouton de ville de départ suggérée ou 'Autre ville'."""
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    if callback_data == "create_dep_other":
        await query.edit_message_text("⌨️ Veuillez entrer le nom de votre ville de départ:")
        return CREATE_DEPARTURE 
    elif callback_data.startswith("create_dep_city:"):
        city_name = callback_data.split(":")[1]
        # Tenter de trouver la localité exacte pour stocker plus d'infos si possible
        exact_match = find_locality(city_name)
        if exact_match and len(exact_match) == 1:
            context.user_data['departure'] = exact_match[0] # Stocker l'objet localité
        else:
            context.user_data['departure'] = {"name": city_name} # Fallback si pas de match exact ou multiple
        logger.info(f"Ville de départ (création) sélectionnée: {context.user_data['departure']}")
        context.user_data['current_state'] = CREATE_ARRIVAL
        
        keyboard_arr = [
            [InlineKeyboardButton(f"🏁 {city}", callback_data=f"create_arr_city:{city}")] for city in SWISS_CITIES_SUGGESTIONS[:3]
        ]
        keyboard_arr.append([InlineKeyboardButton("🏙️ Autre ville...", callback_data="create_arr_other")])
        keyboard_arr.append([InlineKeyboardButton("❌ Annuler", callback_data="create_cancel")])
        departure_display = context.user_data['departure'].get('name', city_name)
        await query.edit_message_text(f"🌍 Partant de {departure_display}.\nÉtape 4️⃣ - Choisissez votre ville d'arrivée:", reply_markup=InlineKeyboardMarkup(keyboard_arr))
        return CREATE_ARRIVAL
    return CREATE_DEPARTURE

async def handle_create_departure_text(update: Update, context: CallbackContext):
    """Gère la saisie texte pour la ville de départ."""
    user_input = update.message.text.strip()
    matches = find_locality(user_input)

    if matches:
        if len(matches) == 1:
            context.user_data['departure'] = matches[0]
            logger.info(f"Ville de départ (création) trouvée: {matches[0]['name']}")
            context.user_data['current_state'] = CREATE_ARRIVAL
            keyboard_arr = [
                [InlineKeyboardButton(f"🏁 {city}", callback_data=f"create_arr_city:{city}")] for city in SWISS_CITIES_SUGGESTIONS[:3]
            ]
            keyboard_arr.append([InlineKeyboardButton("🏙️ Autre ville...", callback_data="create_arr_other")])
            keyboard_arr.append([InlineKeyboardButton("❌ Annuler", callback_data="create_cancel")])
            departure_display = context.user_data['departure']['name']
            await update.message.reply_text(f"🌍 Partant de {departure_display}.\nÉtape 4️⃣ - Choisissez votre ville d'arrivée:", reply_markup=InlineKeyboardMarkup(keyboard_arr))
            return CREATE_ARRIVAL
        else:
            keyboard = [[InlineKeyboardButton(format_locality_result(loc), callback_data=f"create_dep_loc:{loc['zip']}_{loc['name']}")] for loc in matches[:5]]
            keyboard.append([InlineKeyboardButton("✏️ Réessayer la saisie", callback_data="create_dep_retry_text")])
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="create_cancel")])
            await update.message.reply_text("🤔 Plusieurs correspondances trouvées. Veuillez préciser:", reply_markup=InlineKeyboardMarkup(keyboard))
            return CREATE_DEPARTURE
    else:
        await update.message.reply_text("😕 Ville non trouvée. Veuillez vérifier l'orthographe ou essayer une autre ville suisse.")
        return CREATE_DEPARTURE

async def handle_create_departure_loc_callback(update: Update, context: CallbackContext):
    """Gère le clic sur une localité spécifique après recherche texte."""
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    if callback_data == "create_dep_retry_text":
        await query.edit_message_text("⌨️ Veuillez entrer à nouveau le nom de votre ville de départ:")
        return CREATE_DEPARTURE
    elif callback_data.startswith("create_dep_loc:"):
        loc_identifier = callback_data.split(":", 1)[1]
        # Retrouver la localité (nécessite une logique pour parser l'identifiant et retrouver l'objet)
        # Pour simplifier, on suppose que l'identifiant est suffisant ou qu'on peut le retrouver.
        # Idéalement, find_locality serait utilisé ici avec l'identifiant si possible.
        # Pour l'exemple, on prend le nom de l'identifiant.
        loc_name_part = loc_identifier.split('_', 1)[1] if '_' in loc_identifier else loc_identifier
        exact_match = find_locality(loc_name_part) # Tentative de retrouver l'objet complet
        if exact_match and len(exact_match) == 1 : # Idéalement on aurait l'objet direct
             context.user_data['departure'] = exact_match[0]
        else: # Fallback
            context.user_data['departure'] = {"name": loc_name_part}

        logger.info(f"Ville de départ (création) confirmée: {context.user_data['departure']}")
        context.user_data['current_state'] = CREATE_ARRIVAL
        keyboard_arr = [
            [InlineKeyboardButton(f"🏁 {city}", callback_data=f"create_arr_city:{city}")] for city in SWISS_CITIES_SUGGESTIONS[:3]
        ]
        keyboard_arr.append([InlineKeyboardButton("🏙️ Autre ville...", callback_data="create_arr_other")])
        keyboard_arr.append([InlineKeyboardButton("❌ Annuler", callback_data="create_cancel")])
        departure_display = context.user_data['departure'].get('name', loc_name_part)
        await query.edit_message_text(f"🌍 Partant de {departure_display}.\nÉtape 4️⃣ - Choisissez votre ville d'arrivée:", reply_markup=InlineKeyboardMarkup(keyboard_arr))
        return CREATE_ARRIVAL
    return CREATE_DEPARTURE

async def handle_create_arrival_city_callback(update: Update, context: CallbackContext):
    """Gère le clic sur un bouton de ville d'arrivée suggérée ou 'Autre ville'."""
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    departure_display = context.user_data.get('departure', {}).get('name', context.user_data.get('departure', 'N/A'))

    if callback_data == "create_arr_other":
        await query.edit_message_text(f"⌨️ Partant de {departure_display}.\nVeuillez entrer le nom de votre ville d'arrivée:")
        return CREATE_ARRIVAL
    elif callback_data.startswith("create_arr_city:"):
        city_name = callback_data.split(":")[1]
        exact_match = find_locality(city_name)
        if exact_match and len(exact_match) == 1:
            context.user_data['arrival'] = exact_match[0]
        else:
            context.user_data['arrival'] = {"name": city_name}
        logger.info(f"Ville d'arrivée (création) sélectionnée: {context.user_data['arrival']}")
        
        # Transition vers la sélection de la date/heure
        context.user_data['current_state'] = CREATE_CALENDAR # Prochain état géré par date_picker
        arrival_display = context.user_data['arrival'].get('name', city_name)
        prompt_message = (
            f"🌍 De: {departure_display}\n"
            f"🏁 À: {arrival_display}\n\n"
            "🗓️ Étape 5️⃣ - Choisissez la date et l'heure du trajet:"
        )
        return await start_date_selection(
            update, context, prompt_message,
            next_state_after_confirm=CREATE_SEATS, # État après confirmation de date/heure
            calendar_state=CREATE_CALENDAR,
            time_state=CREATE_TIME,
            minute_state=CREATE_MINUTE,
            confirm_dt_state=CREATE_CONFIRM_DATETIME,
            action_prefix="create_cal" # Préfixe pour les callbacks du date_picker
        )
    return CREATE_ARRIVAL

async def handle_create_arrival_text(update: Update, context: CallbackContext):
    """Gère la saisie texte pour la ville d'arrivée."""
    user_input = update.message.text.strip()
    matches = find_locality(user_input)
    departure_display = context.user_data.get('departure', {}).get('name', context.user_data.get('departure', 'N/A'))

    if matches:
        if len(matches) == 1:
            context.user_data['arrival'] = matches[0]
            logger.info(f"Ville d'arrivée (création) trouvée: {matches[0]['name']}")
            context.user_data['current_state'] = CREATE_CALENDAR
            arrival_display = context.user_data['arrival']['name']
            prompt_message = (
                f"🌍 De: {departure_display}\n"
                f"🏁 À: {arrival_display}\n\n"
                "🗓️ Étape 5️⃣ - Choisissez la date et l'heure du trajet:"
            )
            # Note: start_date_selection attend un 'update' qui a soit .callback_query soit .message
            # Ici, update.message est disponible.
            return await start_date_selection(
                update, context, prompt_message,
                next_state_after_confirm=CREATE_SEATS,
                calendar_state=CREATE_CALENDAR, time_state=CREATE_TIME, 
                minute_state=CREATE_MINUTE, confirm_dt_state=CREATE_CONFIRM_DATETIME,
                action_prefix="create_cal"
            )
        else:
            keyboard = [[InlineKeyboardButton(format_locality_result(loc), callback_data=f"create_arr_loc:{loc['zip']}_{loc['name']}")] for loc in matches[:5]]
            keyboard.append([InlineKeyboardButton("✏️ Réessayer la saisie", callback_data="create_arr_retry_text")])
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="create_cancel")])
            await update.message.reply_text(f"🤔 Partant de {departure_display}.\nPlusieurs correspondances pour l'arrivée. Veuillez préciser:", reply_markup=InlineKeyboardMarkup(keyboard))
            return CREATE_ARRIVAL
    else:
        await update.message.reply_text(f"😕 Ville d'arrivée non trouvée pour {departure_display}.\nVeuillez vérifier l'orthographe ou essayer une autre ville suisse.")
        return CREATE_ARRIVAL

async def handle_create_arrival_loc_callback(update: Update, context: CallbackContext):
    """Gère le clic sur une localité spécifique pour l'arrivée après recherche texte."""
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    departure_display = context.user_data.get('departure', {}).get('name', context.user_data.get('departure', 'N/A'))

    if callback_data == "create_arr_retry_text":
        await query.edit_message_text(f"⌨️ Partant de {departure_display}.\nVeuillez entrer à nouveau le nom de votre ville d'arrivée:")
        return CREATE_ARRIVAL
    elif callback_data.startswith("create_arr_loc:"):
        loc_identifier = callback_data.split(":", 1)[1]
        loc_name_part = loc_identifier.split('_', 1)[1] if '_' in loc_identifier else loc_identifier
        exact_match = find_locality(loc_name_part)
        if exact_match and len(exact_match) == 1:
            context.user_data['arrival'] = exact_match[0]
        else:
            context.user_data['arrival'] = {"name": loc_name_part}

        logger.info(f"Ville d'arrivée (création) confirmée: {context.user_data['arrival']}")
        context.user_data['current_state'] = CREATE_CALENDAR
        arrival_display = context.user_data['arrival'].get('name', loc_name_part)
        prompt_message = (
            f"🌍 De: {departure_display}\n"
            f"🏁 À: {arrival_display}\n\n"
            "🗓️ Étape 5️⃣ - Choisissez la date et l'heure du trajet:"
        )
        return await start_date_selection(
            update, context, prompt_message,
            next_state_after_confirm=CREATE_SEATS,
            calendar_state=CREATE_CALENDAR, time_state=CREATE_TIME,
            minute_state=CREATE_MINUTE, confirm_dt_state=CREATE_CONFIRM_DATETIME,
            action_prefix="create_cal"
        )
    return CREATE_ARRIVAL

async def handle_create_date_confirmed(update: Update, context: CallbackContext):
    """Appelé après confirmation de la date et heure par le date_picker."""
    selected_dt = context.user_data.get('selected_datetime')
    if not selected_dt:
        logger.error("selected_datetime non trouvé dans context.user_data après date_picker.")
        # Gérer l'erreur, peut-être redemander la date ou annuler.
        await update.effective_message.reply_text("😕 Oups ! Une erreur s'est produite avec la date. Veuillez réessayer.")
        # Optionnel: revenir à une étape précédente ou annuler
        return await handle_create_cancel(update, context)


    context.user_data['date'] = selected_dt.strftime('%d/%m/%Y %H:%M')
    context.user_data['datetime_obj'] = selected_dt # Stocker l'objet datetime pour la BDD
    
    dep = context.user_data.get('departure', {})
    arr = context.user_data.get('arrival', {})
    departure_display = dep.get('name', dep if isinstance(dep, str) else 'N/A')
    arrival_display = arr.get('name', arr if isinstance(arr, str) else 'N/A')
    date_display = context.user_data['date']

    message_text = (
        f"Récapitulatif partiel:\n"
        f"🌍 De: {departure_display}\n"
        f"🏁 À: {arrival_display}\n"
        f"🗓️ Date: {date_display}\n\n"
        "💺 Étape 6️⃣ - Combien de places disponibles? (ex: 2)"
    )
    if update.callback_query: # Si on vient d'un callback (ex: confirmation du date_picker)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message_text, parse_mode="Markdown")
    else: # Si on vient d'un message (moins probable ici)
        await update.message.reply_text(message_text, parse_mode="Markdown")
        
    context.user_data['current_state'] = CREATE_SEATS
    return CREATE_SEATS

async def handle_create_seats(update: Update, context: CallbackContext):
    """Gère l'entrée du nombre de sièges."""
    seats_text = update.message.text
    if not validate_seats(seats_text):
        await update.message.reply_text("⚠️ Nombre de places invalide. Veuillez entrer un chiffre (ex: 1, 2, 3).")
        return CREATE_SEATS
    
    context.user_data['seats'] = int(seats_text)
    logger.info(f"Nombre de sièges (création): {seats_text}")
    context.user_data['current_state'] = CREATE_PRICE
    
    await update.message.reply_text("💰 Étape 7️⃣ - Quel est le prix par place en CHF? (ex: 10.50)")
    return CREATE_PRICE

async def handle_create_price(update: Update, context: CallbackContext):
    """Gère l'entrée du prix."""
    price_text = update.message.text
    if not validate_price(price_text):
        await update.message.reply_text("⚠️ Prix invalide. Veuillez entrer un montant (ex: 5, 12.50).")
        return CREATE_PRICE
        
    context.user_data['price'] = float(price_text)
    logger.info(f"Prix (création): {price_text}")
    context.user_data['current_state'] = CREATE_CONFIRM
    
    dep = context.user_data.get('departure', {})
    arr = context.user_data.get('arrival', {})
    dep_display = dep.get('name', dep if isinstance(dep, str) else 'N/A')
    arr_display = arr.get('name', arr if isinstance(arr, str) else 'N/A')
    
    trip_options_display = ", ".join([k for k, v in context.user_data.get('trip_options', {}).items() if v])
    if not trip_options_display: trip_options_display = "Aucune"

    summary = (
        "📋 *Récapitulatif du trajet à créer*:\n\n"
        f"👤 Rôle: {context.user_data.get('trip_type', 'N/A').replace('driver', '🚗 Conducteur').replace('passenger', '🧍 Passager')}\n"
        f"⚙️ Options: {trip_options_display}\n"
        f"🌍 De: {dep_display}\n"
        f"🏁 À: {arr_display}\n"
        f"🗓️ Date: {context.user_data.get('date', 'N/A')}\n"
        f"💺 Places: {context.user_data.get('seats', 'N/A')}\n"
        f"💰 Prix: {context.user_data.get('price', 'N/A')} CHF\n\n"
        "Confirmez-vous la création de ce trajet?"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Oui, confirmer", callback_data="create_confirm_yes")],
        [InlineKeyboardButton("❌ Non, annuler", callback_data="create_cancel")]
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
            # Récupérer ou créer l'utilisateur de la BDD
            db_user = db.query(User).filter(User.telegram_id == user_id).first()
            if not db_user:
                # Cette situation devrait être gérée par /start ou un middleware
                logger.error(f"Utilisateur non trouvé dans la BDD: {user_id}")
                await query.edit_message_text("❌ Erreur: Utilisateur non trouvé. Veuillez d'abord utiliser /start.")
                context.user_data.clear()
                return ConversationHandler.END

            departure_data = context.user_data.get('departure', {})
            arrival_data = context.user_data.get('arrival', {})

            new_trip = Trip(
                driver_id=db_user.id, # Assurez-vous que c'est l'ID de l'utilisateur BDD
                departure_city=departure_data.get('name', str(departure_data)),
                departure_zip=departure_data.get('zip'),
                departure_canton=departure_data.get('canton'),
                arrival_city=arrival_data.get('name', str(arrival_data)),
                arrival_zip=arrival_data.get('zip'),
                arrival_canton=arrival_data.get('canton'),
                departure_time=context.user_data.get('datetime_obj'), # Utiliser l'objet datetime
                available_seats=context.user_data.get('seats'),
                price_per_seat=context.user_data.get('price'),
                trip_type=context.user_data.get('trip_type'),
                options=json.dumps(context.user_data.get('trip_options', {})), # Sérialiser les options en JSON
                is_published=False # Le trajet est créé comme brouillon
            )
            db.add(new_trip)
            db.commit()
            db.refresh(new_trip)
            logger.info(f"Nouveau trajet ID {new_trip.id} sauvegardé en BDD.")

            keyboard_after_save = [
                [InlineKeyboardButton("🚀 Publier ce trajet", callback_data=f"publish_trip:{new_trip.id}")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")] # Assurez-vous que ce callback est géré
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
    else: # create_cancel
        await query.edit_message_text("❌ Création de trajet annulée.")

    context.user_data.clear()
    return ConversationHandler.END

async def handle_create_cancel(update: Update, context: CallbackContext):
    """Annule la conversation de création de trajet."""
    message_text = "❌ Création de trajet annulée."
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(message_text)
        except Exception as e: # Peut échouer si le message original a été supprimé ou trop ancien
            logger.warning(f"Impossible d'éditer le message lors de l'annulation: {e}")
            await update.effective_message.reply_text(message_text) # Envoyer un nouveau message en fallback
    else:
        await update.message.reply_text(message_text)
        
    context.user_data.clear()
    return ConversationHandler.END

async def handle_unexpected_input(update: Update, context: CallbackContext):
    """Fonction de fallback pour gérer les entrées inattendues dans la conversation."""
    current_s = context.user_data.get('current_state', "un état inconnu")
    logger.warning(f"Entrée inattendue reçue dans create_trip (état: {current_s}): {update.effective_message.text if update.effective_message else update.callback_query.data}")
    
    message = "😕 Je n'ai pas compris. Veuillez utiliser les boutons ou suivre les instructions. Vous pouvez taper /cancel pour annuler."
    
    if update.callback_query:
        await update.callback_query.answer("Action non comprise.", show_alert=True)
        # Ne pas éditer le message pour ne pas perdre le contexte des boutons précédents
    elif update.message:
        await update.message.reply_text(message)
    
    return context.user_data.get('current_state') # Rester dans l'état actuel

# Handler pour le bouton de publication (en dehors de la conversation)
async def publish_created_trip(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    trip_id = int(query.data.split(":")[1])
    
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        await query.edit_message_text("❌ Trajet non trouvé.")
        return
    
    # Optionnel: Vérifier si l'utilisateur est le conducteur du trajet
    # current_user_db_id = context.user_data.get('db_user_id') # Nécessite de stocker l'ID BDD de l'utilisateur
    # if not current_user_db_id or trip.driver_id != current_user_db_id:
    #     await query.edit_message_text("❌ Vous n'êtes pas autorisé à publier ce trajet.")
    #     return

    trip.is_published = True
    db.commit()
    logger.info(f"Trajet ID {trip_id} publié.")
    
    keyboard_published = [
        # Mettre à jour les callbacks pour qu'ils soient gérés par menu_handlers
        [InlineKeyboardButton("📋 Mes trajets", callback_data="menu:my_trips")], 
        [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]
    ]
    await query.edit_message_text(
        f"✅ Trajet {trip.departure_city} → {trip.arrival_city} publié avec succès!",
        reply_markup=InlineKeyboardMarkup(keyboard_published)
    )
    # Pas de `return ConversationHandler.END` ici car ce n'est pas dans une conversation

# Définition du ConversationHandler pour la création de trajet
create_trip_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('creer', start_create_trip),
        # Le pattern pour le bouton "Créer un trajet" du menu principal doit correspondre ici
        CallbackQueryHandler(start_create_trip, pattern='^menu:create_trip$') 
    ],
    states={
        CREATE_TRIP_TYPE: [
            CallbackQueryHandler(handle_create_trip_type, pattern='^create_trip_type:(driver|passenger)$'),
        ],
        CREATE_TRIP_OPTIONS: [
            CallbackQueryHandler(handle_create_trip_options, pattern='^create_trip_option:'), # Gère les clics sur les options
            CallbackQueryHandler(handle_create_trip_options, pattern='^create_trip_options:continue$'), # Gère le bouton "Continuer"
        ],
        CREATE_DEPARTURE: [
            CallbackQueryHandler(handle_create_departure_city_callback, pattern='^create_dep_city:'),
            CallbackQueryHandler(handle_create_departure_city_callback, pattern='^create_dep_other$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_departure_text),
            CallbackQueryHandler(handle_create_departure_loc_callback, pattern='^create_dep_loc:'),
            CallbackQueryHandler(handle_create_departure_loc_callback, pattern='^create_dep_retry_text$'),
        ],
        CREATE_ARRIVAL: [
            CallbackQueryHandler(handle_create_arrival_city_callback, pattern='^create_arr_city:'),
            CallbackQueryHandler(handle_create_arrival_city_callback, pattern='^create_arr_other$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_arrival_text),
            CallbackQueryHandler(handle_create_arrival_loc_callback, pattern='^create_arr_loc:'),
            CallbackQueryHandler(handle_create_arrival_loc_callback, pattern='^create_arr_retry_text$'),
        ],
        # États gérés par date_picker.py. Les patterns doivent être exacts.
        CREATE_CALENDAR: [ 
            CallbackQueryHandler(handle_calendar_navigation, pattern=f"^{CALENDAR_NAVIGATION_PATTERN}$"),
            CallbackQueryHandler(handle_day_selection, pattern=f"^{CALENDAR_DAY_SELECTION_PATTERN}$"),
            CallbackQueryHandler(handle_create_cancel, pattern=f"^{CALENDAR_CANCEL_PATTERN}$") 
        ],
        CREATE_TIME: [ 
            CallbackQueryHandler(handle_time_selection, pattern=f"^{TIME_SELECTION_PATTERN}$"),
            CallbackQueryHandler(handle_flex_time_selection, pattern=f"^{FLEX_TIME_PATTERN}$"),
            CallbackQueryHandler(lambda u,c: start_date_selection(u,c, "📅 Sélectionnez la date et l'heure du trajet:", next_state_after_confirm=CREATE_SEATS, calendar_state=CREATE_CALENDAR, time_state=CREATE_TIME, minute_state=CREATE_MINUTE, confirm_dt_state=CREATE_CONFIRM_DATETIME, action_prefix="create_cal"), pattern=f"^{TIME_BACK_PATTERN}$"),
            CallbackQueryHandler(handle_create_cancel, pattern=f"^{TIME_CANCEL_PATTERN}$")
        ],
        CREATE_MINUTE: [ 
            CallbackQueryHandler(handle_minute_selection, pattern=f"^{MINUTE_SELECTION_PATTERN}$"),
            CallbackQueryHandler(lambda u,c: handle_day_selection(u,c,bypass_date_check=True), pattern=f"^{MINUTE_BACK_PATTERN}$"), 
            CallbackQueryHandler(handle_create_cancel, pattern=f"^{MINUTE_CANCEL_PATTERN}$")
        ],
        CREATE_CONFIRM_DATETIME: [ 
             CallbackQueryHandler(handle_create_date_confirmed, pattern=f"^{DATETIME_ACTION_PATTERN.replace('(confirm|change|cancel)', 'confirm')}$"),
             CallbackQueryHandler(lambda u,c: start_date_selection(u,c, "📅 Sélectionnez la date et l'heure du trajet:", next_state_after_confirm=CREATE_SEATS, calendar_state=CREATE_CALENDAR, time_state=CREATE_TIME, minute_state=CREATE_MINUTE, confirm_dt_state=CREATE_CONFIRM_DATETIME, action_prefix="create_cal"), pattern=f"^{DATETIME_ACTION_PATTERN.replace('(confirm|change|cancel)', 'change')}$"),
             CallbackQueryHandler(handle_create_cancel, pattern=f"^{DATETIME_ACTION_PATTERN.replace('(confirm|change|cancel)', 'cancel')}$")
        ],
        CREATE_SEATS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_seats),
        ],
        CREATE_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_price),
        ],
        CREATE_CONFIRM: [
            CallbackQueryHandler(handle_create_confirm, pattern='^create_confirm_yes$'),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_create_cancel, pattern='^create_cancel$'), # Doit être assez générique pour attraper tous les cancels de cette conv
        CommandHandler('cancel', handle_create_cancel),
        MessageHandler(filters.ALL, handle_unexpected_input)
    ],
    name="create_trip_conversation",
    persistent=False,
    allow_reentry=True,
    # priority=10 # Priorité plus élevée si nécessaire pour éviter les conflits
)

publish_trip_handler = CallbackQueryHandler(publish_created_trip, pattern=r"^publish_trip:\d+$")

def register(application):
    logger.info("🔄 Enregistrement des handlers de création de trajet...")
    try:
        application.add_handler(create_trip_conv_handler)
        application.add_handler(publish_trip_handler) # Handler pour le bouton "Publier"
        logger.info("✅ Handlers de création de trajet enregistrés.")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'enregistrement des handlers de création de trajet: {e}", exc_info=True)

async def create_trip(update: Update, context: CallbackContext):
    """Point d'entrée pour la commande /creer - Appelle start_create_trip"""
    return await start_create_trip(update, context)

