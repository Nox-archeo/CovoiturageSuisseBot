import os
import json
import logging
import traceback
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
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
from utils.validators import validate_date, validate_price, validate_seats
from utils.swiss_cities import find_locality, format_locality_result
from utils.date_picker import (
    start_date_selection, handle_calendar_navigation, 
    handle_day_selection, handle_time_selection, handle_minute_selection, handle_datetime_action,
    handle_flex_time_selection,
    CALENDAR_NAVIGATION_PATTERN, CALENDAR_DAY_SELECTION_PATTERN, 
    CALENDAR_CANCEL_PATTERN, TIME_SELECTION_PATTERN, TIME_BACK_PATTERN, TIME_CANCEL_PATTERN,
    MINUTE_SELECTION_PATTERN, MINUTE_BACK_PATTERN, MINUTE_CANCEL_PATTERN,
    FLEX_TIME_PATTERN
)
from utils.location_picker import (
    start_location_selection, handle_location_selection, handle_location_query,
    LOCATION_SELECTION_PATTERN
)
# from .trip_preferences import show_preferences_menu # If used
# from .profile_handlers import profile_menu # If used

# Configuration du logger
logger = logging.getLogger(__name__)

# États de conversation (IMPORTANT: définir avant toute utilisation)
(
    CHOOSING_TYPE,
    CHOOSING_DEPARTURE,
    CHOOSING_DESTINATION,
    ENTERING_DEPARTURE,
    ENTERING_ARRIVAL,
    DATE,
    SEATS,
    PRICE,
    CONFIRM,
    TRIP_TYPE,
    DEPARTURE,
    ARRIVAL,
    ADDING_STOP,
    MEETING_POINT,
    TRIP_OPTIONS
) = range(15)

def load_cities():
    """Charge les villes depuis swiss_localities.json"""
    try:
        # Utiliser la fonction de utils/swiss_cities.py pour charger les localités
        from utils.swiss_cities import load_localities
        
        localities = load_localities()
        if localities:
            logger.info(f"Chargé {len(localities)} localités")
            return list(localities.keys())
        else:
            logger.warning("Aucune localité trouvée, utilisation de la liste par défaut")
            return [
                "Zürich", "Genève", "Bâle", "Lausanne", "Berne", 
                "Lucerne", "Fribourg", "Neuchâtel", "Sion"
            ]
    except Exception as e:
        logger.error(f"Erreur chargement des localités: {e}")
        return [
            "Zürich", "Genève", "Bâle", "Lausanne", "Berne", 
            "Lucerne", "Fribourg", "Neuchâtel", "Sion"
        ]  # Liste par défaut

# Charger les villes au démarrage
SWISS_CITIES = load_cities()

async def create_trip(update: Update, context):
    """Processus de création de trajet amélioré - Étape 1: Choix du rôle"""
    # S'assurer que le mode est bien réglé sur "create" et pas "search"
    context.user_data.clear()  # Clear any previous data
    context.user_data['mode'] = 'create'
    logger.info("🔍 Mode réglé sur 'create' dans create_trip")
    
    keyboard = [
        [
            InlineKeyboardButton("🚗 Conducteur", callback_data="trip_type:driver"),
            InlineKeyboardButton("🧍 Passager", callback_data="trip_type:passenger")
        ],
        [
            InlineKeyboardButton("❌ Annuler", callback_data="trip_type:cancel")
        ]
    ]
    
    if update.message:
        await update.message.reply_text(
            "🚗 *Création d'un nouveau trajet*\n\n"
            "Étape 1️⃣ - Choisissez votre rôle pour ce trajet:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "🚗 *Création d'un nouveau trajet*\n\n"
            "Étape 1️⃣ - Choisissez votre rôle pour ce trajet:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    return TRIP_TYPE

async def add_stops(update: Update, context):
    """Ajoute des arrêts intermédiaires"""
    if 'stops' not in context.user_data:
        context.user_data['stops'] = []
    
    keyboard = [
        [InlineKeyboardButton("✅ Terminer les arrêts", callback_data="stops_done")],
        [InlineKeyboardButton("❌ Annuler", callback_data="stops_cancel")]
    ]
    
    await update.message.reply_text(
        f"🚏 Arrêts actuels: {', '.join(context.user_data['stops']) if context.user_data['stops'] else 'Aucun'}\n"
        "Entrez un nouvel arrêt ou terminez:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADDING_STOP

async def handle_preferences(update: Update, context):
    """Gestion des préférences du trajet"""
    keyboard = [
        [
            InlineKeyboardButton("🚭 Non-fumeur", callback_data="pref_no_smoking"),
            InlineKeyboardButton("🔊 Musique", callback_data="pref_music")
        ],
        [
            InlineKeyboardButton("🐱 Animaux", callback_data="pref_pets"),
            InlineKeyboardButton("💼 Bagages", callback_data="pref_luggage")
        ],
        [
            InlineKeyboardButton("👩 Entre femmes", callback_data="pref_women_only")
        ]
    ]
    await update.message.reply_text(
        "Définissez vos préférences pour ce trajet:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def search_trip(update: Update, context: CallbackContext):
    """Commence la recherche de trajet"""
    # Indiquer que nous sommes en mode recherche
    context.user_data.clear()  # Clear any previous data
    context.user_data['mode'] = 'search'
    logger.info("🔍 Mode réglé sur 'search' dans search_trip")
    
    # Créer un clavier avec les villes principales
    keyboard = []
    popular_cities = ["Fribourg", "Genève", "Lausanne", "Zürich", "Berne", "Bâle"]
    
    for city in popular_cities:
        keyboard.append([InlineKeyboardButton(city, callback_data=f"from_{city}")])
    
    keyboard.append([InlineKeyboardButton("🔍 Recherche avancée", callback_data="advanced_search")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🔍 Recherche de trajets\n\n"
            "1️⃣ Choisissez votre ville de départ:\n"
            "- Sélectionnez une ville dans la liste\n"
            "- Ou utilisez la recherche avancée",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🔍 Recherche de trajets\n\n"
            "1️⃣ Choisissez votre ville de départ:\n"
            "- Sélectionnez une ville dans la liste\n"
            "- Ou utilisez la recherche avancée",
            reply_markup=reply_markup
        )
    return ENTERING_DEPARTURE

async def list_my_trips(update: Update, context):
    """Affiche la liste des trajets de l'utilisateur"""
    user_id = update.effective_user.id
    db = get_db()
    
    # Récupérer les trajets où l'utilisateur est conducteur
    driver_trips = db.query(Trip).join(User).filter(User.telegram_id == user_id).all()
    
    # Récupérer les réservations de l'utilisateur
    passenger_bookings = db.query(Booking).join(User).filter(User.telegram_id == user_id).all()
    
    message = "🚗 Vos trajets:\n\n"
    
    if driver_trips:
        message += "En tant que conducteur:\n"
        for trip in driver_trips:
            message += f"• {trip.departure_city} → {trip.arrival_city} le {trip.departure_time}\n"
    
    if passenger_bookings:
        message += "\nEn tant que passager:\n"
        for booking in passenger_bookings:
            message += f"• {booking.trip.departure_city} → {booking.trip.arrival_city} le {booking.trip.departure_time}\n"
    
    if not driver_trips and not passenger_bookings:
        message = "Vous n'avez pas encore de trajets."
    
    keyboard = [
        [
            InlineKeyboardButton("🚗 Créer un trajet", callback_data="create_trip"),
            InlineKeyboardButton("🔍 Chercher un trajet", callback_data="search_trip")
        ]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def list_my_trips_menu(update: Update, context: CallbackContext):
    """Shows options for viewing user's trips."""
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("🚗 Mes trajets (Conducteur)", callback_data="trips:list_driver")],
        [InlineKeyboardButton("🧍 Mes réservations (Passager)", callback_data="trips:list_passenger")],
        [InlineKeyboardButton("⬅️ Retour au menu", callback_data="menu:back_to_menu")]
    ]
    text = "📋 *Mes Trajets*\n\nChoisissez une catégorie à afficher:"
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return # Or a state if this becomes a conversation

async def list_specific_trips(update: Update, context: CallbackContext, trip_role: str):
    """Helper to list trips based on role (driver/passenger)."""
    query = update.callback_query
    user_id = update.effective_user.id
    db = get_db()
    message_parts = []
    
    if trip_role == "driver":
        driver_trips = db.query(Trip).join(User, Trip.driver_id == User.id).filter(User.telegram_id == user_id).all()
        if driver_trips:
            message_parts.append("*En tant que conducteur:*")
            for trip in driver_trips:
                status = "Publié" if trip.is_published else "Brouillon"
                message_parts.append(f"• {trip.departure_city} → {trip.arrival_city} le {trip.departure_time.strftime('%d/%m/%Y %H:%M')} ({status}) - ID: {trip.id}")
                # Add buttons to manage/view trip
        else:
            message_parts.append("Vous n'avez aucun trajet en tant que conducteur.")
            
    elif trip_role == "passenger":
        passenger_bookings = db.query(Booking).join(User).filter(User.telegram_id == user_id).all()
        if passenger_bookings:
            message_parts.append("*En tant que passager (réservations):*")
            for booking in passenger_bookings:
                trip = booking.trip
                message_parts.append(f"• {trip.departure_city} → {trip.arrival_city} le {trip.departure_time.strftime('%d/%m/%Y %H:%M')} (Conducteur: {trip.driver.first_name if trip.driver else 'N/A'})")
                # Add buttons to view booking/trip
        else:
            message_parts.append("Vous n'avez aucune réservation en tant que passager.")
            
    if not message_parts:
        final_message = "Vous n'avez pas encore de trajets."
    else:
        final_message = "\n".join(message_parts)

    keyboard = [[InlineKeyboardButton("⬅️ Retour à Mes Trajets", callback_data="menu:my_trips")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]]

    if query:
        await query.answer()
        await query.edit_message_text(final_message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else: # Should not happen if called from button
        await update.message.reply_text(final_message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_trip_list_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    action = query.data.split(":")[1]

    if action == "list_driver":
        return await list_specific_trips(update, context, "driver")
    elif action == "list_passenger":
        return await list_specific_trips(update, context, "passenger")
    return # Or a state

# Remove old create_trip, handle_trip_type, show_trip_options if they are fully replaced by create_trip_handler.py
# ...

def register(application):
    # Handler for "Mes trajets" button in main menu
    application.add_handler(CallbackQueryHandler(list_my_trips_menu, pattern="^menu:my_trips$"))
    # Handlers for choices within "Mes trajets" menu
    application.add_handler(CallbackQueryHandler(handle_trip_list_choice, pattern="^trips:(list_driver|list_passenger)$"))
    
    # Add other handlers from this file, e.g., for viewing/editing specific trips if you build that
    logger.info("Trip (viewing/management) handlers registered.")

# ... (rest of trip_handlers.py, ensure SWISS_CITIES and load_cities are used if needed by other functions here)
# The states like CHOOSING_TYPE, DEPARTURE etc. should be removed if not used by a ConversationHandler in this file.
# If search_trip is still relevant here and not fully in search_trip_handler, it needs proper integration.
