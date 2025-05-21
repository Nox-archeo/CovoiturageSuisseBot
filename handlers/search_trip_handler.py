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

# Configuration du logger
logger = logging.getLogger(__name__)

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
        
        # Séparation des trajets en deux catégories : conducteur et passager
        driver_trips = []
        passenger_trips = []
        
        for trip in matching_trips:
            if hasattr(trip, 'is_request') and trip.is_request:
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
                    if hasattr(trip, 'available_seats') and trip.available_seats is not None:
                        places_display = f"💺 *Places*: {trip.available_seats}\n"
                    else:
                        places_display = f"💺 *Places*: {trip.seats_available}\n"
                    
                    # Ajouter au message
                    message_text += f"🚗 *Trajet {i+1}*: {trip.departure_city} → {trip.arrival_city}\n"
                    message_text += f"📅 *Date*: {display_time}\n"
                    message_text += places_display
                    message_text += f"💰 *Prix*: {trip.price_per_seat}.-\n\n"
                    
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
                [InlineKeyboardButton("🚗 Créer un trajet", callback_data="main_menu:create_trip")],
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
        
        # Récupérer les informations du conducteur
        driver = db.query(User).get(trip.driver_id)
        driver_name = driver.username if driver and driver.username else "Conducteur anonyme"
        
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
            message_text = (
                f"🚗 *Détails du trajet*\n\n"
                f"🏁 *Itinéraire*: {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 *Date*: {display_time}\n"
                f"👤 *Conducteur*: {driver_name}\n"
                f"💺 *Places disponibles*: {trip.seats_available}\n"
                f"💰 *Prix*: {trip.price_per_seat}.- CHF\n\n"
            )
            
            # Boutons d'action pour une offre de conducteur
            keyboard = [
                [InlineKeyboardButton("📱 Contacter le conducteur", callback_data=f"search_contact_driver:{trip.id}")],
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
        
        # Récupérer les informations du conducteur
        driver = db.query(User).get(trip.driver_id)
        driver_name = driver.username if driver and driver.username else "Conducteur anonyme"
        
        # Stocker l'ID du conducteur à contacter dans les données utilisateur
        context.user_data['contact_driver_id'] = trip.driver_id
        
        # Inviter l'utilisateur à entrer son message
        keyboard = [
            [InlineKeyboardButton("📱 Contacter le conducteur", callback_data=f"contact_driver_{trip.driver_id}")],
            [InlineKeyboardButton("🔙 Retour aux détails", callback_data=f"search_view_trip:{trip_id}")],
            [InlineKeyboardButton("❌ Annuler", callback_data="search_back_results")]
        ]
        
        # Utiliser les handlers de contact existants
        await query.edit_message_text(
            f"📱 *Contact avec le conducteur*\n\n"
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

# Définition du ConversationHandler pour la recherche de trajet
search_trip_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('chercher', start_search_trip),
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
            CallbackQueryHandler(handle_search_results_buttons, pattern='^search_view_trip:|^search_new$|^search_back_to_menu$|^search_contact_driver:|^search_back_results$')
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
