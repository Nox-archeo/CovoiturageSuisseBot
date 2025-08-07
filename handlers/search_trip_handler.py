import logging
import traceback
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
from database.models import Trip, User, Booking
from database import get_db
from utils.swiss_cities import find_locality, format_locality_result, load_localities as load_all_localities
from utils.swiss_pricing import round_to_nearest_0_05, format_swiss_price

# Configuration du logger
logger = logging.getLogger(__name__)

(
    SEARCH_USER_TYPE,  # Nouvel état pour choisir si on cherche un conducteur ou un passager
    SEARCH_STARTING,
    SEARCH_DEPARTURE,
    SEARCH_ARRIVAL,
    SEARCH_DATE,
    SEARCH_RESULTS
) = range(6)

# Charger les villes au démarrage pour les suggestions
def load_cities_list():
    """Charge les villes depuis swiss_localities.json pour les suggestions."""
    try:
        localities = load_all_localities()
        if localities:
            logger.info(f"Chargé {len(localities)} localités pour search_trip_handler")
            return sorted(list(localities.keys()))
        else:
            logger.warning("Aucune localité trouvée dans search_trip_handler, utilisation de la liste par défaut")
            return sorted([
                "Zürich", "Genève", "Bâle", "Lausanne", "Berne", 
                "Lucerne", "Fribourg", "Neuchâtel", "Sion"
            ])
    except Exception as e:
        logger.error(f"Erreur chargement des localités dans search_trip_handler: {e}")
        return sorted([
            "Zürich", "Genève", "Bâle", "Lausanne", "Berne", 
            "Lucerne", "Fribourg", "Neuchâtel", "Sion"
        ])

POPULAR_CITIES = load_cities_list()

async def start_search_trip(update: Update, context: CallbackContext):
    """Lance le processus de recherche de trajet."""
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
            "Vous devez créer un profil avant de pouvoir rechercher un trajet."
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
        return ConversationHandler.END
    
    # Nettoyer les données précédentes
    context.user_data.clear()
    context.user_data['mode'] = 'search'
    logger.info("Mode réglé sur 'search' dans start_search_trip")
    
    # Demander d'abord si on est conducteur ou passager
    keyboard = [
        [InlineKeyboardButton("🚗 Je suis conducteur - Je cherche des passagers", callback_data="search_user_type:driver")],
        [InlineKeyboardButton("🧍 Je suis passager - Je cherche un conducteur", callback_data="search_user_type:passenger")],
        [InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "🔍 *Recherche de trajets*\n\n"
        "Que cherchez-vous?\n\n"
        "- Un *conducteur* si vous avez besoin d'être transporté\n"
        "- Des *passagers* si vous proposez un trajet en voiture"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return SEARCH_USER_TYPE

async def handle_search_user_type(update: Update, context: CallbackContext):
    """Gère la sélection du type d'utilisateur (conducteur ou passager)."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "search_cancel":
        await query.edit_message_text("❌ Recherche annulée.")
        context.user_data.clear()
        return ConversationHandler.END
    
    # Stocker le type d'utilisateur dans les données de contexte
    user_type = query.data.split(":")[1]  # "driver" ou "passenger"
    context.user_data['search_user_type'] = user_type
    
    # 🚨 FIX CRUCIAL: Rediriger vers la recherche de passagers pour les conducteurs
    if user_type == "driver":
        # Conducteur cherche des passagers - TERMINER ce ConversationHandler et déclencher l'entry point search_passengers
        logger.info(f"🎯 REDIRECT: Conducteur détecté - fin de search_trip + déclenchement search_passengers entry point")
        
        # Créer un nouveau callback qui déclenche l'entry point du ConversationHandler search_passengers
        await query.edit_message_text(
            "🔄 Redirection vers la recherche de passagers...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 Commencer la recherche", callback_data="search_passengers")
            ]])
        )
        
        # Terminer ce ConversationHandler pour permettre au search_passengers de démarrer
        return ConversationHandler.END
    
    # Sinon continuer avec la logique normale pour les passagers
    # Créer un clavier avec les villes principales pour l'étape suivante
    keyboard = []
    popular_cities = ["Fribourg", "Genève", "Lausanne", "Zürich", "Berne", "Bâle"]
    
    for city in popular_cities:
        keyboard.append([InlineKeyboardButton(city, callback_data=f"search_from:{city}")])
    
    keyboard.append([InlineKeyboardButton("🔍 Recherche avancée", callback_data="search_advanced")])
    keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Adaptation du message selon si on est conducteur ou passager
    user_type_text = "un conducteur" if context.user_data.get('search_user_type') == "passenger" else "des passagers"
    
    message_text = (
        f"🔍 *Recherche de {user_type_text}*\n\n"
        "1️⃣ Choisissez votre ville de départ:\n"
        "- Sélectionnez une ville dans la liste\n"
        "- Ou utilisez la recherche avancée"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return SEARCH_DEPARTURE

async def handle_search_departure_selection(update: Update, context: CallbackContext):
    """Gère la sélection de la ville de départ pour la recherche."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "search_advanced":
        await query.edit_message_text(
            "🏙️ *Recherche avancée*\n\n"
            "Entrez le nom de la ville ou le code postal de départ:",
            parse_mode="Markdown"
        )
        return SEARCH_DEPARTURE
    
    if query.data == "search_cancel":
        await query.edit_message_text("❌ Recherche annulée.")
        context.user_data.clear()
        return ConversationHandler.END
    
    if query.data.startswith("search_from:"):
        city = query.data.replace("search_from:", "")
        context.user_data['departure'] = city
        logger.info(f"Ville de départ (recherche) sélectionnée: {city}")
        
        # Afficher les choix de destination
        keyboard = []
        for city_name in POPULAR_CITIES[:6]:
            if city_name.lower() != context.user_data['departure'].lower():
                keyboard.append([InlineKeyboardButton(city_name, callback_data=f"search_to:{city_name}")])
        
        keyboard.append([InlineKeyboardButton("🔍 Autre destination", callback_data="search_other_destination")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")])
        
        # Adaptation du message selon si on est conducteur ou passager
        user_type_text = "un conducteur" if context.user_data.get('search_user_type') == "passenger" else "des passagers"
        
        await query.edit_message_text(
            f"🔍 *Recherche de {user_type_text}*\n\n"
            f"Départ depuis: {context.user_data['departure']}\n\n"
            "2️⃣ Choisissez votre destination:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return SEARCH_ARRIVAL
    
    return SEARCH_DEPARTURE

async def handle_search_departure_text(update: Update, context: CallbackContext):
    """Gère la saisie texte pour la recherche de la ville de départ."""
    user_input = update.message.text.strip()
    matches = find_locality(user_input)
    
    if matches:
        keyboard = []
        for match in matches[:5]: # Limiter les résultats
            display_text = format_locality_result(match)
            callback_data = f"search_dep_loc:{match['name']}|{match['zip']}"
            keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("Ce n'est pas listé / Réessayer", callback_data="search_dep_retry")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")])
        
        await update.message.reply_text(
            "Voici les localités correspondantes pour le départ. Choisissez:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "❌ Ville non trouvée. Veuillez réessayer ou annuler.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")]])
        )
    
    return SEARCH_DEPARTURE

async def handle_search_departure_loc_callback(update: Update, context: CallbackContext):
    """Gère le clic sur une localité spécifique pour le départ."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "search_dep_retry":
        await query.edit_message_text("Veuillez entrer le nom ou le code postal de la ville de départ:")
        return SEARCH_DEPARTURE
    
    if query.data.startswith("search_dep_loc:"):
        locality_part = query.data.split(":")[1]
        name, zip_code = locality_part.split('|')
        context.user_data['departure'] = {'name': name, 'zip': zip_code}
        departure_display = name
        logger.info(f"Ville de départ (recherche) confirmée: {name} ({zip_code})")
        
        # Afficher les choix de destination
        keyboard = []
        for city_name in POPULAR_CITIES[:6]:
            if city_name.lower() != name.lower():
                keyboard.append([InlineKeyboardButton(city_name, callback_data=f"search_to:{city_name}")])
        
        keyboard.append([InlineKeyboardButton("🔍 Autre destination", callback_data="search_other_destination")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")])
        
        # Adaptation du message selon si on est conducteur ou passager
        user_type_text = "un conducteur" if context.user_data.get('search_user_type') == "passenger" else "des passagers"
        
        await query.edit_message_text(
            f"🔍 *Recherche de {user_type_text}*\n\n"
            f"Départ depuis: {departure_display}\n\n"
            "2️⃣ Choisissez votre destination:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return SEARCH_ARRIVAL
    
    return SEARCH_DEPARTURE

async def handle_search_arrival_selection(update: Update, context: CallbackContext):
    """Gère la sélection de la ville d'arrivée pour la recherche."""
    query = update.callback_query
    await query.answer()
    
    # Gérer correctement le cas où departure peut être un string ou un dictionnaire
    departure = context.user_data.get('departure', 'N/A')
    if isinstance(departure, dict):
        departure_display = departure.get('name', 'N/A')
    else:
        departure_display = departure
    
    if query.data == "search_other_destination":
        # Adaptation du message selon si on est conducteur ou passager
        user_type_text = "un conducteur" if context.user_data.get('search_user_type') == "passenger" else "des passagers"
        
        await query.edit_message_text(
            f"🔍 *Recherche de {user_type_text}*\n\n"
            f"Départ depuis: {departure_display}\n\n"
            "Entrez le nom ou le code postal de la ville d'arrivée:",
            parse_mode="Markdown"
        )
        return SEARCH_ARRIVAL
    
    if query.data == "search_cancel":
        await query.edit_message_text("❌ Recherche annulée.")
        context.user_data.clear()
        return ConversationHandler.END
    
    if query.data.startswith("search_to:"):
        city = query.data.replace("search_to:", "")
        context.user_data['arrival'] = city
        logger.info(f"Ville d'arrivée (recherche) sélectionnée: {city}")
        
        # On peut directement chercher des trajets correspondants sans demander la date
        # (pour simplifier la recherche dans un premier temps)
        await perform_trip_search(update, context)
        return SEARCH_RESULTS
    
    return SEARCH_ARRIVAL

async def handle_search_arrival_text(update: Update, context: CallbackContext):
    """Gère la saisie texte pour la recherche de la ville d'arrivée."""
    user_input = update.message.text.strip()
    matches = find_locality(user_input)
    
    # Gérer correctement le cas où departure peut être un string ou un dictionnaire
    departure = context.user_data.get('departure', 'N/A')
    if isinstance(departure, dict):
        departure_display = departure.get('name', 'N/A')
    else:
        departure_display = departure
    
    if matches:
        keyboard = []
        for match in matches[:5]: # Limiter les résultats
            display_text = format_locality_result(match)
            callback_data = f"search_arr_loc:{match['name']}|{match['zip']}"
            keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("Ce n'est pas listé / Réessayer", callback_data="search_arr_retry")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")])
        
        # Adaptation du message selon si on est conducteur ou passager
        user_type_text = "un conducteur" if context.user_data.get('search_user_type') == "passenger" else "des passagers"
        
        await update.message.reply_text(
            f"🔍 *Recherche de {user_type_text}*\n\n"
            f"Départ: {departure_display}\n\n"
            "Voici les localités correspondantes pour l'arrivée. Choisissez:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        # Adaptation du message selon si on est conducteur ou passager
        user_type_text = "un conducteur" if context.user_data.get('search_user_type') == "passenger" else "des passagers"
        
        await update.message.reply_text(
            f"🔍 *Recherche de {user_type_text}*\n\n"
            f"Départ: {departure_display}\n\n"
            "❌ Ville d'arrivée non trouvée. Veuillez réessayer ou annuler.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")]]),
            parse_mode="Markdown"
        )
    
    return SEARCH_ARRIVAL

async def handle_search_arrival_loc_callback(update: Update, context: CallbackContext):
    """Gère le clic sur une localité spécifique pour l'arrivée."""
    query = update.callback_query
    await query.answer()
    
    # Gérer correctement le cas où departure peut être un string ou un dictionnaire
    departure = context.user_data.get('departure', 'N/A')
    if isinstance(departure, dict):
        departure_display = departure.get('name', 'N/A')
    else:
        departure_display = departure
    
    if query.data == "search_arr_retry":
        # Adaptation du message selon si on est conducteur ou passager
        user_type_text = "un conducteur" if context.user_data.get('search_user_type') == "passenger" else "des passagers"
        
        await query.edit_message_text(
            f"🔍 *Recherche de {user_type_text}*\n\n"
            f"Départ: {departure_display}\n\n"
            "Veuillez entrer le nom ou le code postal de la ville d'arrivée:",
            parse_mode="Markdown"
        )
        return SEARCH_ARRIVAL
    
    if query.data.startswith("search_arr_loc:"):
        locality_part = query.data.split(":")[1]
        name, zip_code = locality_part.split('|')
        context.user_data['arrival'] = {'name': name, 'zip': zip_code}
        logger.info(f"Ville d'arrivée (recherche) confirmée: {name} ({zip_code})")
        
        # On peut directement chercher des trajets correspondants sans demander la date
        # (pour simplifier la recherche dans un premier temps)
        await perform_trip_search(update, context)
        return SEARCH_RESULTS
    
    return SEARCH_ARRIVAL

async def perform_trip_search(update: Update, context: CallbackContext):
    """Cherche des trajets correspondants dans la base de données et affiche les résultats."""
    query = update.callback_query
    
    # Extraire les données de départ et arrivée
    departure = context.user_data.get('departure')
    arrival = context.user_data.get('arrival')
    
    # Formatage pour la recherche
    if isinstance(departure, dict):
        departure_str = departure['name']
    else:
        departure_str = departure
    
    if isinstance(arrival, dict):
        arrival_str = arrival['name']
    else:
        arrival_str = arrival
    
    logger.info(f"Recherche de trajets: {departure_str} → {arrival_str}")
    
    try:
        db = get_db()
        # Recherche de trajets correspondants à la ville de départ et d'arrivée
        matching_trips = db.query(Trip).filter(
            Trip.departure_city.like(f"%{departure_str}%"),
            Trip.arrival_city.like(f"%{arrival_str}%"),
            Trip.is_published == True,
            Trip.departure_time >= datetime.now()
        ).all()
        
        # Filtrer les trajets annulés côté Python pour éviter les erreurs de colonnes manquantes
        valid_trips = []
        for trip in matching_trips:
            # Vérifier l'annulation de manière sécurisée
            is_cancelled = getattr(trip, 'is_cancelled', False)
            if not is_cancelled:
                valid_trips.append(trip)
        
        matching_trips = valid_trips
        
        # Séparation des trajets en deux catégories : conducteur et passager
        driver_trips = []
        passenger_trips = []
        for trip in matching_trips:
            # Utiliser trip_role pour distinguer les types de trajets
            trip_role = getattr(trip, 'trip_role', 'driver')  # Par défaut 'driver' pour compatibilité
            if trip_role == 'passenger':
                passenger_trips.append(trip)
            else:
                driver_trips.append(trip)
        
        # Filtrer selon le type d'utilisateur recherché (si spécifié)
        search_user_type = context.user_data.get('search_user_type')
        if search_user_type == "passenger":
            # Si l'utilisateur est un passager, il cherche un conducteur
            filtered_trips = driver_trips
            passenger_trips = []  # Ne pas montrer les demandes de passagers
        elif search_user_type == "driver":
            # Si l'utilisateur est un conducteur, il cherche des passagers
            filtered_trips = passenger_trips
            driver_trips = []  # Ne pas montrer les offres de conducteurs
        else:
            # Si aucun type spécifié, montrer tous les trajets
            filtered_trips = matching_trips
        
        logger.info(f"Recherche réussie - {len(matching_trips)} trajets trouvés (Conducteurs: {len(driver_trips)}, Passagers: {len(passenger_trips)})")
        
        if matching_trips:
            # Afficher les trajets trouvés
            keyboard = []
            
            # Afficher les trajets de conducteurs (offres)
            if driver_trips:
                message_text = f"🔍 *Trajets disponibles avec conducteur ({len(driver_trips)})*:\n\n"
                
                for i, trip in enumerate(driver_trips[:5]):  # Limiter à 5 résultats
                    # Format flexible pour l'heure si nécessaire
                    display_time = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
                    if hasattr(trip, 'flexible_time') and trip.flexible_time:
                        display_time_slot = ""
                        hour = trip.departure_time.hour
                        if 6 <= hour < 12:
                            display_time_slot = "Dans la matinée"
                        elif 12 <= hour < 18:
                            display_time_slot = "L'après-midi"
                        elif 18 <= hour < 23:
                            display_time_slot = "En soirée"
                        else:
                            display_time_slot = "Heure à définir"
                        display_time = trip.departure_time.strftime("%d/%m/%Y") + f" - {display_time_slot}"
                    
                    # Affichage des places disponibles en fonction du champ existant
                    places_display = ""
                    try:
                        if hasattr(trip, 'available_seats') and trip.available_seats is not None:
                            places_display = f"💺 *Places*: {trip.available_seats}\n"
                        elif hasattr(trip, 'seats_available') and trip.seats_available is not None:
                            places_display = f"💺 *Places*: {trip.seats_available}\n"
                        else:
                            places_display = "💺 *Places*: Information non disponible\n"
                    except Exception as e:
                        logger.error(f"Erreur lors de l'affichage des places pour le trajet {trip.id}: {str(e)}")
                        places_display = "💺 *Places*: Information non disponible\n"
                    
                    # Affichage du prix avec gestion d'erreurs et arrondi suisse
                    price_display = ""
                    try:
                        if hasattr(trip, 'price_per_seat') and trip.price_per_seat is not None:
                            rounded_price = round_to_nearest_0_05(trip.price_per_seat)
                            price_display = f"💰 *Prix*: {format_swiss_price(rounded_price)} CHF\n\n"
                        else:
                            price_display = "💰 *Prix*: Information non disponible\n\n"
                    except Exception as e:
                        logger.error(f"Erreur lors de l'affichage du prix pour le trajet {trip.id}: {str(e)}")
                        price_display = "💰 *Prix*: Information non disponible\n\n"
                    
                    # Ajouter au message
                    message_text += f"🚗 *Trajet {i+1}*: {trip.departure_city} → {trip.arrival_city}\n"
                    message_text += f"📅 *Date*: {display_time}\n"
                    message_text += places_display
                    message_text += price_display
                    
                    # Ajouter un bouton pour voir les détails
                    keyboard.append([InlineKeyboardButton(
                        f"🚗 {trip.departure_city} → {trip.arrival_city} ({display_time})",
                        callback_data=f"search_view_trip:{trip.id}"
                    )])
            else:
                message_text = "🔍 *Aucun trajet avec conducteur disponible*\n\n"
            
            # Afficher les trajets de passagers (demandes)
            if passenger_trips:
                message_text += f"\n🧍 *Demandes de trajets ({len(passenger_trips)})*:\n\n"
                
                for i, trip in enumerate(passenger_trips[:5]):  # Limiter à 5 résultats
                    # Format flexible pour l'heure si nécessaire
                    display_time = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
                    if hasattr(trip, 'flexible_time') and trip.flexible_time:
                        display_time_slot = ""
                        hour = trip.departure_time.hour
                        if 6 <= hour < 12:
                            display_time_slot = "Dans la matinée"
                        elif 12 <= hour < 18:
                            display_time_slot = "L'après-midi"
                        elif 18 <= hour < 23:
                            display_time_slot = "En soirée"
                        else:
                            display_time_slot = "Heure à définir"
                        display_time = trip.departure_time.strftime("%d/%m/%Y") + f" - {display_time_slot}"
                    
                    # Ajouter au message
                    message_text += f"🧍 *Demande {i+1}*: {trip.departure_city} → {trip.arrival_city}\n"
                    message_text += f"📅 *Date*: {display_time}\n"
                    if hasattr(trip, 'seats_needed'):
                        message_text += f"👥 *Passagers*: {trip.seats_needed}\n\n"
                    else:
                        message_text += "\n"
                    
                    # Ajouter un bouton pour voir les détails
                    keyboard.append([InlineKeyboardButton(
                        f"🧍 {trip.departure_city} → {trip.arrival_city} ({display_time})",
                        callback_data=f"search_view_trip:{trip.id}"
                    )])
            
            # Ajouter des boutons de navigation
            keyboard.append([
                InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new"),
                InlineKeyboardButton("🔙 Menu principal", callback_data="search_back_to_menu")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            # Pas de trajets trouvés
            keyboard = [
                [InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")],
                [InlineKeyboardButton("🚗 Créer un trajet", callback_data="menu:create")],
                [InlineKeyboardButton("🔙 Menu principal", callback_data="search_back_to_menu")]
            ]
            
            # Adapter le message selon le type d'utilisateur recherché
            search_user_type = context.user_data.get('search_user_type')
            no_results_message = "❌ Aucun trajet ne correspond à votre recherche.\n\n"
            
            if search_user_type == "passenger":
                no_results_message = "❌ Aucun conducteur disponible pour cette destination.\n\n"
            elif search_user_type == "driver":
                no_results_message = "❌ Aucun passager en recherche pour cette destination.\n\n"
            
            await query.edit_message_text(
                no_results_message +
                f"🔍 *Recherche*: {departure_str} → {arrival_str}\n\n"
                "Vous pouvez essayer une nouvelle recherche ou créer un trajet.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de trajets: {str(e)}")
        traceback.print_exc()
        
        # Message d'erreur
        keyboard = [
            [InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")],
            [InlineKeyboardButton("🔙 Menu principal", callback_data="search_back_to_menu")]
        ]
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la recherche.\n"
            "Veuillez réessayer ou contacter l'administrateur.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return SEARCH_RESULTS


async def handle_search_results_buttons(update: Update, context: CallbackContext):
    """Gère les boutons dans les résultats de recherche."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "search_new":
        # Recommencer une nouvelle recherche
        return await start_search_trip(update, context)
    
    if query.data == "search_back_to_menu":
        # Rediriger vers le menu principal
        # Utiliser une fonction externe de menu_handlers pour revenir au menu principal
        from .menu_handlers import back_to_menu
        return await back_to_menu(update, context)
    
    if query.data.startswith("search_view_trip:"):
        trip_id = int(query.data.split(":")[1])
        await show_trip_details(update, context, trip_id)
    
    if query.data.startswith("search_book_trip:"):
        trip_id = int(query.data.split(":")[1])
        await book_trip(update, context, trip_id)
    
    if query.data.startswith("search_contact_driver:"):
        trip_id = int(query.data.split(":")[1])
        await contact_driver_from_search(update, context, trip_id)
    
    if query.data == "search_back_results":
        # Retourner aux résultats précédents
        last_trip_id = context.user_data.get('last_viewed_trip_id')
        if last_trip_id:
            await perform_trip_search(update, context)
        else:
            await query.edit_message_text(
                "⚠️ Impossible de revenir aux résultats précédents.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")
                ]])
            )
    
    return SEARCH_RESULTS

async def show_trip_details(update: Update, context: CallbackContext, trip_id):
    """Montre les détails d'un trajet spécifique."""
    query = update.callback_query
    
    try:
        db = get_db()
        trip = db.query(Trip).get(trip_id)
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")
                ]])
            )
            return SEARCH_RESULTS
        
        # Récupérer les informations du conducteur - Méthode plus sûre pour éviter l'erreur de colonne
        try:
            driver = db.query(User).filter(User.id == trip.driver_id).first()
            # 🔧 FIX: Utiliser full_name en priorité, puis username, puis fallback
            driver_name = driver.full_name if driver and driver.full_name else driver.username if driver and driver.username else "Conducteur anonyme"
        except Exception as driver_error:
            logger.error(f"Erreur lors de la récupération des informations du conducteur: {str(driver_error)}")
            driver_name = "Conducteur anonyme"
        
        # Formatage de la date
        display_time = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
        if hasattr(trip, 'flexible_time') and trip.flexible_time:
            display_time_slot = ""
            hour = trip.departure_time.hour
            if 6 <= hour < 12:
                display_time_slot = "Dans la matinée"
            elif 12 <= hour < 18:
                display_time_slot = "L'après-midi"
            elif 18 <= hour < 23:
                display_time_slot = "En soirée"
            else:
                display_time_slot = "Heure à définir"
            display_time = trip.departure_time.strftime("%d/%m/%Y") + f" - {display_time_slot}"
        
        # Construire le message de détails
        is_request = hasattr(trip, 'is_request') and trip.is_request
        
        if is_request:
            # C'est une demande de trajet (passager)
            message_text = (
                f"🧍 *Détails de la demande de trajet*\n\n"
                f"🏁 *Itinéraire*: {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 *Date*: {display_time}\n"
                f"👤 *Passager*: {driver_name}\n"
            )
            
            if hasattr(trip, 'seats_needed'):
                message_text += f"👥 *Nombre de passagers*: {trip.seats_needed}\n\n"
            
            # Boutons d'action pour une demande de passager
            keyboard = [
                [InlineKeyboardButton("📱 Contacter le passager", callback_data=f"search_contact_passenger:{trip.id}")],
                [InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")],
                [InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")]
            ]
        else:
            # C'est une offre de trajet (conducteur)
            try:
                # Déterminer le nombre de places disponibles avec gestion d'erreurs améliorée
                available_seats = 0
                try:
                    if hasattr(trip, 'available_seats') and trip.available_seats is not None:
                        available_seats = trip.available_seats
                    elif hasattr(trip, 'seats_available') and trip.seats_available is not None:
                        available_seats = trip.seats_available
                    else:
                        logger.warning(f"Ni available_seats ni seats_available disponibles pour le trajet {trip.id}")
                except Exception as seats_error:
                    logger.error(f"Erreur lors de l'accès aux places disponibles: {str(seats_error)}")
                
                # Déterminer le prix avec gestion d'erreurs
                price = 0
                try:
                    if hasattr(trip, 'price_per_seat') and trip.price_per_seat is not None:
                        price = trip.price_per_seat
                    else:
                        logger.warning(f"price_per_seat non disponible pour le trajet {trip.id}")
                except Exception as price_error:
                    logger.error(f"Erreur lors de l'accès au prix: {str(price_error)}")
                
                message_text = (
                    f"🚗 *Détails du trajet*\n\n"
                    f"🏁 *Itinéraire*: {trip.departure_city} → {trip.arrival_city}\n"
                    f"📅 *Date*: {display_time}\n"
                    f"👤 *Conducteur*: {driver_name}\n"
                    f"💺 *Places disponibles*: {available_seats}\n"
                    f"💰 *Prix*: {format_swiss_price(round_to_nearest_0_05(price))} CHF\n\n"
                )
            except Exception as e:
                logger.error(f"Erreur lors de l'accès aux détails du trajet: {str(e)}")
                message_text = (
                    f"🚗 *Détails du trajet*\n\n"
                    f"🏁 *Itinéraire*: {trip.departure_city} → {trip.arrival_city}\n"
                    f"📅 *Date*: {display_time}\n"
                    f"👤 *Conducteur*: {driver_name}\n"
                )
                # Ajouter plus d'informations si elles sont disponibles avec arrondi suisse
                try:
                    price_value = trip.price_per_seat if trip.price_per_seat is not None else 0
                    rounded_price = round_to_nearest_0_05(price_value)
                    message_text += f"💰 *Prix*: {format_swiss_price(rounded_price)} CHF\n\n"
                except:
                    message_text += "💰 *Prix*: Information non disponible\n\n"
            
            # Boutons d'action pour une offre de conducteur - Contact uniquement après réservation
            keyboard = [
                [InlineKeyboardButton("🎟️ Réserver", callback_data=f"search_book_trip:{trip.id}")],
                [InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")],
                [InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")]
            ]
        
        if trip.additional_info:
            message_text += f"ℹ️ *Informations supplémentaires*:\n{trip.additional_info}\n\n"
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Stocker l'ID du dernier trajet consulté pour pouvoir y revenir
        context.user_data['last_viewed_trip_id'] = trip_id
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des détails du trajet: {str(e)}")
        traceback.print_exc()
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de l'affichage des détails du trajet.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")
            ]])
        )
    
    return SEARCH_RESULTS

async def handle_search_cancel(update: Update, context: CallbackContext):
    """Annule la recherche et nettoie les données."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Recherche annulée.")
    else:
        await update.message.reply_text("❌ Recherche annulée.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def contact_driver_from_search(update: Update, context: CallbackContext, trip_id):
    """Gère la demande de contact avec le conducteur depuis les résultats de recherche."""
    query = update.callback_query
    
    try:
        db = get_db()
        trip = db.query(Trip).get(trip_id)
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results"),
                    InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")
                ]])
            )
            return SEARCH_RESULTS
        
        # 🔒 VÉRIFICATION CRITIQUE: Vérifier le statut de paiement avant révélation des informations conducteur
        user_telegram_id = update.effective_user.id
        user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
        
        if user:
            # Vérifier si l'utilisateur a une réservation payée pour ce trajet
            booking = db.query(Booking).filter_by(
                trip_id=trip_id,
                passenger_id=user.id
            ).first()
            
            # Autoriser le contact seulement si le paiement est effectué ou en cours
            payment_authorized = booking and booking.payment_status in ['paid', 'completed']
            
            if not payment_authorized:
                await query.edit_message_text(
                    "🔒 *Accès restreint*\n\n"
                    "Pour contacter le conducteur, vous devez d'abord:\n"
                    "1️⃣ Réserver une place sur ce trajet\n"
                    "2️⃣ Effectuer le paiement\n\n"
                    "Ceci protège la vie privée des conducteurs.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎫 Réserver ce trajet", callback_data=f"search_book_trip:{trip_id}")],
                        [InlineKeyboardButton("🔙 Retour aux détails", callback_data=f"search_view_trip:{trip_id}")],
                        [InlineKeyboardButton("❌ Annuler", callback_data="search_back_results")]
                    ]),
                    parse_mode="Markdown"
                )
                return SEARCH_RESULTS
        
        # Récupérer les informations du conducteur (seulement après paiement)
        driver = db.query(User).get(trip.driver_id)
        # 🔧 FIX: Utiliser full_name en priorité, puis username, puis fallback
        driver_name = driver.full_name if driver and driver.full_name else driver.username if driver and driver.username else "Conducteur anonyme"
        
        # Stocker l'ID du conducteur à contacter dans les données utilisateur
        context.user_data['contact_driver_id'] = trip.driver_id
        
        # 🔒 SÉCURITÉ: Utiliser trip_id au lieu de driver_id pour préserver la confidentialité
        keyboard = [
            [InlineKeyboardButton("📱 Contacter le conducteur", callback_data=f"search_contact_driver:{trip_id}")],
            [InlineKeyboardButton("🔙 Retour aux détails", callback_data=f"search_view_trip:{trip_id}")],
            [InlineKeyboardButton("❌ Annuler", callback_data="search_back_results")]
        ]
        
        # Utiliser les handlers de contact existants
        await query.edit_message_text(
            f"📱 *Contact avec le conducteur*\n\n"
            f"✅ Paiement confirmé - Accès autorisé\n\n"
            f"Vous allez contacter *{driver_name}* pour le trajet:\n"
            f"{trip.departure_city} → {trip.arrival_city}\n\n"
            f"Pour envoyer un message, cliquez sur le bouton ci-dessous:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la demande de contact: {str(e)}")
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la demande de contact.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")
            ]])
        )
    
    return SEARCH_RESULTS

async def book_trip(update: Update, context: CallbackContext):
    """Gère la réservation d'un trajet."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extraire l'ID du trajet depuis les données de callback
        trip_id = int(query.data.split(':')[1])
        seats = 1  # Par défaut, réserver 1 place
        
        db = get_db()
        trip = db.query(Trip).get(trip_id)
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")
                ]])
            )
            return SEARCH_RESULTS
        
        # Vérifier si l'utilisateur est le conducteur
        user_id = update.effective_user.id
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not db_user:
            await query.edit_message_text(
                "❌ Vous devez d'abord configurer votre profil pour réserver un trajet.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                ]])
            )
            return SEARCH_RESULTS
        
        if trip.driver_id == db_user.id:
            await query.edit_message_text(
                "❌ Vous ne pouvez pas réserver votre propre trajet.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                ]])
            )
            return SEARCH_RESULTS
        
        # Vérifier la disponibilité des places
        try:
            available_seats = 0
            try:
                if hasattr(trip, 'available_seats') and trip.available_seats is not None:
                    available_seats = trip.available_seats
                elif hasattr(trip, 'seats_available') and trip.seats_available is not None:
                    available_seats = trip.seats_available
                else:
                    available_seats = 0
                    logger.warning(f"Ni available_seats ni seats_available disponibles pour le trajet {trip.id}")
            except Exception as e:
                logger.error(f"Erreur lors de l'accès aux attributs de places disponibles: {str(e)}")
                available_seats = 0  # Valeur par défaut en cas d'erreur
            
            if available_seats < seats:
                await query.edit_message_text(
                    f"❌ Il n'y a pas assez de places disponibles. Places restantes : {available_seats}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                    ]])
                )
                return SEARCH_RESULTS
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des places disponibles: {str(e)}")
            await query.edit_message_text(
                "❌ Impossible de vérifier les places disponibles. Veuillez réessayer.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                ]])
            )
            return SEARCH_RESULTS
        
        # Vérifier si l'utilisateur a déjà réservé ce trajet
        existing_booking = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.passenger_id == db_user.id,
            Booking.status.in_(["pending", "confirmed"])
        ).first()
        
        if existing_booking:
            # L'utilisateur a déjà une réservation pour ce trajet
            await query.edit_message_text(
                f"ℹ️ Vous avez déjà réservé {existing_booking.seats} place(s) pour ce trajet.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Ajouter des places", callback_data=f"book_add_seats:{trip_id}")],
                    [InlineKeyboardButton("❌ Annuler ma réservation", callback_data=f"book_cancel:{trip_id}")],
                    [InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")]
                ])
            )
            return SEARCH_RESULTS
        
        # 🔧 FIX: Vérifier d'abord que trip.driver_id n'est pas None
        if not trip.driver_id:
            logger.error(f"Trajet {trip_id} n'a pas de conducteur assigné (driver_id est None)")
            await query.edit_message_text(
                "❌ Ce trajet n'a pas encore de conducteur assigné. "
                "Veuillez réessayer plus tard ou contacter le support.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                ]])
            )
            return SEARCH_RESULTS
        
        # Récupérer les informations du conducteur avec vérification supplémentaire
        driver = db.query(User).get(trip.driver_id)
        if not driver:
            logger.error(f"Conducteur avec ID {trip.driver_id} non trouvé pour le trajet {trip_id}")
            await query.edit_message_text(
                "❌ Informations du conducteur non trouvées. "
                "Veuillez réessayer plus tard ou contacter le support.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                ]])
            )
            return SEARCH_RESULTS
        
        # Vérifier que price_per_seat existe et n'est pas None avec arrondi suisse
        try:
            price_per_seat = trip.price_per_seat if hasattr(trip, 'price_per_seat') and trip.price_per_seat is not None else 0
            # Arrondir le prix par siège puis calculer le total
            rounded_price_per_seat = round_to_nearest_0_05(price_per_seat)
            total_price = rounded_price_per_seat * seats
            # Arrondir à nouveau le prix total (au cas où il y ait des centimes non-suisses)
            total_price = round_to_nearest_0_05(total_price)
        except Exception as e:
            logger.error(f"Erreur lors du calcul du prix: {str(e)}")
            rounded_price_per_seat = 0
            total_price = 0
        
        # Créer un récapitulatif de la réservation
        message_text = (
            f"🎟️ *Récapitulatif de votre réservation*\n\n"
            f"🏁 *Trajet* : {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 *Date* : {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"👤 *Conducteur* : {driver.full_name if driver.full_name else driver.username if driver.username else 'Conducteur anonyme'}\n"
            f"💺 *Places* : {seats}\n"
            f"💰 *Prix actuel par place* : {format_swiss_price(rounded_price_per_seat)} CHF\n"
            f"💳 *Total à payer* : {format_swiss_price(total_price)} CHF\n\n"
            f"💡 *Le prix par place diminuera si d'autres passagers rejoignent le trajet.*\n"
            f"Vous serez automatiquement remboursé de la différence.\n\n"
            f"Confirmez-vous cette réservation ?"
        )
        
        # Vérifier si le conducteur a un compte PayPal - MAINTENANT SÉCURISÉ
        has_paypal_account = driver and hasattr(driver, 'paypal_email') and driver.paypal_email is not None
        
        if has_paypal_account:
            # Le conducteur a un compte PayPal, proposer le paiement
            keyboard = [
                [InlineKeyboardButton("💳 Payer avec PayPal", callback_data=f"book_pay_paypal:{trip_id}:{seats}")],
                [InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")],
                [InlineKeyboardButton("❌ Annuler", callback_data="search_back_results")]
            ]
        else:
            # Le conducteur n'a pas de compte PayPal, informer l'utilisateur
            message_text += "\n\n⚠️ Le conducteur n'a pas encore configuré son compte PayPal. Vous pouvez quand même réserver, mais vous ne pourrez pas payer en ligne pour le moment."
            keyboard = [
                [InlineKeyboardButton("✅ Réserver sans paiement", callback_data=f"book_without_payment:{trip_id}:{seats}")],
                [InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")],
                [InlineKeyboardButton("❌ Annuler", callback_data="search_back_results")]
            ]
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la réservation: {str(e)}", exc_info=True)
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la réservation.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
            ]])
        )
    
    return SEARCH_RESULTS

async def pay_with_paypal(update: Update, context: CallbackContext):
    """Traite le paiement avec PayPal."""
    query = update.callback_query
    await query.answer()
    
    # Extraire les données du callback - gérer différents formats
    parts = query.data.split(":")
    
    if parts[0] == "pay_trip":
        # Format: pay_trip:trip_id
        trip_id = int(parts[1])
        # Récupérer les seats depuis user_data si disponible
        seats = context.user_data.get('seats', 1)
    else:
        # Format: book_pay_paypal:trip_id:seats
        trip_id = int(parts[1])
        seats = int(parts[2])
    
    try:
        # Utiliser PayPal via les handlers de paiement
        
        db = get_db()
        trip = db.query(Trip).get(trip_id)
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")
                ]])
            )
            return SEARCH_RESULTS
        
        # Obtenir l'utilisateur
        user_id = update.effective_user.id
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not db_user:
            await query.edit_message_text(
                "❌ Utilisateur non trouvé.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                ]])
            )
            return SEARCH_RESULTS
        
        # Créer une réservation en attente de paiement
        from database.models import Booking
        from datetime import datetime
        
        new_booking = Booking(
            trip_id=trip_id,
            passenger_id=db_user.id,
            status="pending_payment",
            seats=seats,
            booking_date=datetime.now(),
            amount=round_to_nearest_0_05(trip.price_per_seat * seats),
            is_paid=False
        )
        
        db.add(new_booking)
        db.commit()
        
        # Rediriger vers le système de paiement PayPal existant
        context.user_data['pending_booking_id'] = new_booking.id
        context.user_data['trip_id'] = trip_id
        context.user_data['seats'] = seats
        
        # Utiliser le système PayPal existant
        keyboard = [
            [InlineKeyboardButton("💳 Procéder au paiement PayPal", callback_data=f"pay_trip:{trip_id}")],
            [InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")]
        ]
        
        await query.edit_message_text(
            "💰 *Paiement avec PayPal*\n\n"
            "Votre réservation a été créée. Cliquez sur le bouton ci-dessous "
            "pour procéder au paiement via PayPal.\n\n"
            "Une fois le paiement effectué, votre réservation sera confirmée automatiquement.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du paiement PayPal: {str(e)}", exc_info=True)
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la préparation du paiement.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
            ]])
        )
    
    return SEARCH_RESULTS

async def book_without_payment(update: Update, context: CallbackContext):
    """Réserve un trajet sans paiement en ligne."""
    query = update.callback_query
    await query.answer()
    
    # Extraire les données du callback
    parts = query.data.split(":")
    trip_id = int(parts[1])
    seats = int(parts[2])
    
    try:
        db = get_db()
        trip = db.query(Trip).get(trip_id)
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")
                ]])
            )
            return SEARCH_RESULTS
        
        # Obtenir l'utilisateur
        user_id = update.effective_user.id
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not db_user:
            await query.edit_message_text(
                "❌ Utilisateur non trouvé.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                ]])
            )
            return SEARCH_RESULTS
        
        try:
            # Vérifier que le prix par siège est disponible
            price_per_seat = 0
            try:
                if hasattr(trip, 'price_per_seat') and trip.price_per_seat is not None:
                    price_per_seat = trip.price_per_seat
            except Exception as e:
                logger.error(f"Erreur lors de l'accès au prix par siège: {str(e)}")
            
            # Créer une réservation sans paiement avec arrondi suisse
            rounded_amount = round_to_nearest_0_05(price_per_seat * seats)
            new_booking = Booking(
                trip_id=trip_id,
                passenger_id=db_user.id,
                status="confirmed",
                seats=seats,
                booking_date=datetime.now(),
                amount=rounded_amount,
                is_paid=False
            )
            
            db.add(new_booking)
            
            # Mettre à jour le nombre de places disponibles avec gestion d'erreurs
            try:
                if hasattr(trip, 'available_seats') and trip.available_seats is not None:
                    trip.available_seats -= seats
                elif hasattr(trip, 'seats_available') and trip.seats_available is not None:
                    trip.seats_available -= seats
                else:
                    logger.warning(f"Impossible de mettre à jour le nombre de places pour le trajet {trip.id}")
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour des places disponibles: {str(e)}")
            
            db.commit()
        except Exception as e:
            logger.error(f"Erreur lors de la création de la réservation: {str(e)}", exc_info=True)
            db.rollback()
            await query.edit_message_text(
                "❌ Une erreur est survenue lors de la création de la réservation.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
                ]])
            )
            return SEARCH_RESULTS
        
        # Notification de réservation réussie
        try:
            # S'assurer que le prix est disponible pour le message de confirmation
            final_price = price_per_seat * seats if price_per_seat is not None else 0
            
            # Récupérer les informations du conducteur
            driver = db.query(User).get(trip.driver_id)
            # 🔧 FIX: Utiliser full_name en priorité, puis username, puis fallback
            driver_name = driver.full_name if driver and driver.full_name else driver.username if driver and driver.username else "Conducteur anonyme"
            
            # ⚠️ SÉCURITÉ: Ne pas révéler les contacts tant que le paiement n'est pas effectué
            # Récupérer les informations du passager  
            passenger_name = db_user.full_name if db_user.full_name else update.effective_user.username or update.effective_user.first_name or "Passager"
            
            # Envoyer confirmation SANS révéler les contacts
            await query.edit_message_text(
                "✅ *Réservation enregistrée !*\n\n"
                f"Vous avez pré-réservé {seats} place(s) pour le trajet :\n"
                f"{trip.departure_city} → {trip.arrival_city}\n"
                f"Date : {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                f"Montant à payer au conducteur : {final_price}.- CHF\n\n"
                f"� *Conducteur :* {driver_name}\n\n"
                f"⚠️ *IMPORTANT :* Les coordonnées de contact seront révélées "
                f"après confirmation du paiement par les deux parties.\n\n"
                "Le conducteur a été notifié de votre demande de réservation.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("� Confirmer avec paiement PayPal", callback_data=f"search_pay_now:{trip_id}:{seats}")],
                    [InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")],
                    [InlineKeyboardButton("🔙 Menu principal", callback_data="search_back_to_menu")]
                ]),
                parse_mode="Markdown"
            )
            
            # Envoyer les informations du passager au conducteur
            if driver and driver.telegram_id:
                try:
                    await context.bot.send_message(
                        chat_id=driver.telegram_id,
                        text=f"🎟️ *Nouvelle demande de réservation !*\n\n"
                             f"Un passager souhaite réserver {seats} place(s) pour votre trajet :\n"
                             f"{trip.departure_city} → {trip.arrival_city}\n"
                             f"Date : {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                             f"Montant potentiel : {final_price}.- CHF\n\n"
                             f"� *Passager :* {passenger_name}\n\n"
                             f"⚠️ *IMPORTANT :* Les coordonnées de contact seront révélées "
                             f"après confirmation du paiement par les deux parties.",
                        parse_mode="Markdown"
                    )
                    logger.info(f"Notification de réservation envoyée au conducteur {driver.telegram_id}")
                except Exception as notify_error:
                    logger.error(f"Erreur lors de la notification au conducteur: {str(notify_error)}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la confirmation: {str(e)}", exc_info=True)
            await query.edit_message_text(
                "✅ Réservation confirmée ! Vous pouvez contacter le conducteur pour plus de détails.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📱 Contacter le conducteur", callback_data=f"search_contact_driver:{trip_id}")],
                    [InlineKeyboardButton("🔙 Menu principal", callback_data="search_back_to_menu")]
                ])
            )
        
    except Exception as e:
        logger.error(f"Erreur lors de la réservation sans paiement: {str(e)}", exc_info=True)
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la réservation.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data=f"search_view_trip:{trip_id}")
            ]])
        )
    
    return SEARCH_RESULTS

async def prompt_driver_paypal_setup(update: Update, context: CallbackContext):
    """Invite un conducteur à configurer son compte PayPal."""
    query = update.callback_query
    await query.answer()
    
    # Extraire l'ID du conducteur du callback
    driver_id = int(query.data.split(":")[1])
    
    try:
        db = get_db()
        driver = db.query(User).get(driver_id)
        
        if not driver:
            await query.edit_message_text(
                "❌ Conducteur introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu principal", callback_data="search_back_to_menu")
                ]])
            )
            return ConversationHandler.END
        
        # Rediriger vers la configuration PayPal
        keyboard = [
            [InlineKeyboardButton("� Configurer PayPal", callback_data="setup_paypal")],
            [InlineKeyboardButton("🔙 Menu principal", callback_data="search_back_to_menu")]
        ]
        
        await query.edit_message_text(
            "💰 *Configuration PayPal*\n\n"
            "Pour recevoir les paiements de vos passagers, vous devez configurer votre email PayPal.\n\n"
            "Une fois configuré, vous pourrez :\n"
            "- Recevoir des paiements directement sur votre compte PayPal\n"
            "- Gérer vos revenus facilement\n"
            "- Bénéficier de la sécurité PayPal\n\n"
            "Cliquez sur le bouton ci-dessous pour commencer :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration PayPal: {str(e)}", exc_info=True)
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la configuration PayPal.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Menu principal", callback_data="search_back_to_menu")
            ]])
        )
    
    return ConversationHandler.END

# Définition du ConversationHandler pour la recherche de trajet
search_trip_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('chercher', start_search_trip),
        CommandHandler('chercher_trajet', start_search_trip),  # Ajout pour le menu hamburger
        CallbackQueryHandler(start_search_trip, pattern='^search_trip$'),
        CallbackQueryHandler(start_search_trip, pattern='^search_new$')
    ],
    states={
        SEARCH_USER_TYPE: [
            CallbackQueryHandler(handle_search_user_type, pattern='^search_user_type:(driver|passenger)$'),
            CallbackQueryHandler(handle_search_cancel, pattern='^search_cancel$')
        ],
        SEARCH_DEPARTURE: [
            CallbackQueryHandler(handle_search_departure_selection, pattern='^search_from:|^search_advanced$|^search_cancel$'),
            CallbackQueryHandler(handle_search_departure_loc_callback, pattern='^search_dep_loc:|^search_dep_retry$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_departure_text)
        ],
        SEARCH_ARRIVAL: [
            CallbackQueryHandler(handle_search_arrival_selection, pattern='^search_to:|^search_other_destination$|^search_cancel$'),
            CallbackQueryHandler(handle_search_arrival_loc_callback, pattern='^search_arr_loc:|^search_arr_retry$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_arrival_text)
        ],
        SEARCH_RESULTS: [
            CallbackQueryHandler(handle_search_results_buttons, pattern='^search_view_trip:|^search_new$|^search_back_to_menu$|^search_contact_driver:|^search_back_results$'),
            CallbackQueryHandler(book_trip, pattern='^search_book_trip:'),
            CallbackQueryHandler(pay_with_paypal, pattern='^book_pay_paypal:'),
            CallbackQueryHandler(pay_with_paypal, pattern='^pay_trip:'),  # Ajout du handler pour pay_trip
            CallbackQueryHandler(book_without_payment, pattern='^book_without_payment:')
        ]
    },
    fallbacks=[
        CommandHandler('cancel', handle_search_cancel),
        CallbackQueryHandler(handle_search_cancel, pattern='^search_cancel$')
    ],
    name="search_trip_conversation",  # Ajouté pour persistent=True
    persistent=True,
    allow_reentry=True,
    per_message=False  # Important : évite le warning PTBUserWarning
)

def register(application):
    application.add_handler(search_trip_conv_handler)
    logger.info("Handlers de recherche de trajet enregistrés.")
