import os
import json
import logging
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
from utils.validators import validate_date, validate_price, validate_seats
from .trip_preferences import show_preferences_menu

# Configuration du logger
logger = logging.getLogger(__name__)

# États de conversation (IMPORTANT: définir avant toute utilisation)
(
    CHOOSING_TYPE,
    CHOOSING_DEPARTURE,
    CHOOSING_DESTINATION,
    ENTERING_DEPARTURE,
    ENTERING_ARRIVAL,
    DEPARTURE,
    ARRIVAL,
    DATE,
    SEATS,
    PRICE,
    CONFIRM,
    TRIP_TYPE,
    ADDING_STOP,
    MEETING_POINT
) = range(14)

def load_cities():
    """Charge le fichier cities.json"""
    try:
        cities_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'src', 'bot', 'data', 'cities.json'
        )
        with open(cities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [city['name'] for city in data['cities']]
    except Exception as e:
        logger.error(f"Erreur chargement cities.json: {e}")
        return ["Zürich", "Genève", "Bâle", "Lausanne", "Berne"]

SWISS_CITIES = load_cities()

async def create_trip_start(update: Update, context: CallbackContext):
    """Démarre le processus de création d'un trajet"""
    # Add debug logs
    print(f"DEBUG: create_trip_start called with update type: {type(update)}")
    if update.callback_query:
        print(f"DEBUG: Callback query data: {update.callback_query.data}")
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Régulier", callback_data="type_regular"),
            InlineKeyboardButton("1️⃣ Unique", callback_data="type_single")
        ],
        [InlineKeyboardButton("❌ Annuler", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            "Quel type de trajet souhaitez-vous créer ?",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            "Quel type de trajet souhaitez-vous créer ?",
            reply_markup=reply_markup
        )
    return DEPARTURE

async def ask_departure(update: Update, context: CallbackContext):
    """Demande la ville de départ"""
    query = update.callback_query
    await query.answer()
    
    trip_type = query.data.split('_')[1]
    context.user_data['trip_type'] = trip_type
    
    buttons = [[InlineKeyboardButton(city, callback_data=f"dep_{city}")] for city in SWISS_CITIES[:5]]
    buttons.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(
        "🚗 De quelle ville partez-vous ?",
        reply_markup=reply_markup
    )
    return ARRIVAL

async def ask_arrival(update: Update, context: CallbackContext):
    """Demande la ville d'arrivée"""
    query = update.callback_query
    await query.answer()
    
    departure = query.data.split('_')[1]
    context.user_data['departure'] = departure
    
    buttons = [[InlineKeyboardButton(city, callback_data=f"arr_{city}")] 
               for city in SWISS_CITIES[:5] if city != departure]
    buttons.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(
        f"🎯 Vers quelle ville allez-vous ?\nDépart: {departure}",
        reply_markup=reply_markup
    )
    return DATE

async def ask_date(update: Update, context: CallbackContext):
    """Demande la date du trajet"""
    query = update.callback_query
    await query.answer()
    
    arrival = query.data.split('_')[1]
    context.user_data['arrival'] = arrival
    
    today = datetime.now()
    dates = [(today.date().replace(day=today.day + i), f"date_{i}") for i in range(7)]
    buttons = [[InlineKeyboardButton(d[0].strftime("%d/%m/%Y"), callback_data=d[1])] for d in dates]
    buttons.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
    
    await query.edit_message_text(
        f"📅 Quand partez-vous ?\nDe: {context.user_data['departure']}\nVers: {arrival}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SEATS

async def ask_seats(update: Update, context: CallbackContext):
    """Demande le nombre de places"""
    query = update.callback_query
    await query.answer()
    
    day_offset = int(query.data.split('_')[1])
    selected_date = datetime.now().date().replace(day=datetime.now().day + day_offset)
    context.user_data['date'] = selected_date.strftime("%Y-%m-%d")
    
    buttons = [[InlineKeyboardButton(str(i), callback_data=f"seats_{i}")] for i in range(1, 5)]
    buttons.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
    
    await query.edit_message_text(
        "👥 Combien de places proposez-vous ?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return PRICE

async def ask_price(update: Update, context: CallbackContext):
    """Demande le prix par place"""
    query = update.callback_query
    await query.answer()
    
    seats = int(query.data.split('_')[1])
    context.user_data['seats'] = seats
    
    prices = [15, 20, 25, 30, 35]
    buttons = [[InlineKeyboardButton(f"{p} CHF", callback_data=f"price_{p}")] for p in prices]
    buttons.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
    
    await query.edit_message_text(
        "💰 Quel est le prix par place ?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CONFIRM

async def confirm_trip(update: Update, context: CallbackContext):
    """Confirme les détails du trajet"""
    query = update.callback_query
    await query.answer()
    
    price = int(query.data.split('_')[1])
    context.user_data['price'] = price
    
    trip_data = context.user_data
    confirmation_text = (
        "📋 Récapitulatif du trajet:\n"
        f"Type: {'Régulier' if trip_data['trip_type'] == 'regular' else 'Unique'}\n"
        f"De: {trip_data['departure']}\n"
        f"Vers: {trip_data['arrival']}\n"
        f"Date: {trip_data['date']}\n"
        f"Places: {trip_data['seats']}\n"
        f"Prix: {trip_data['price']} CHF\n\n"
        "Confirmez-vous ces informations ?"
    )
    
    buttons = [
        [
            InlineKeyboardButton("✅ Confirmer", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Annuler", callback_data="confirm_no")
        ]
    ]
    
    await query.edit_message_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CONFIRM

async def save_trip(update: Update, context: CallbackContext):
    """Sauvegarde le trajet dans la base de données"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_no":
        await query.edit_message_text("Création du trajet annulée.")
        return ConversationHandler.END
    
    try:
        trip_data = context.user_data
        trip = Trip(
            driver_id=update.effective_user.id,
            departure_city=trip_data['departure'],
            arrival_city=trip_data['arrival'],
            departure_time=trip_data['date'],
            available_seats=trip_data['seats'],
            price_per_seat=trip_data['price'],
            is_regular=trip_data['trip_type'] == 'regular'
        )
        
        # Sauvegarder dans la base de données
        session = get_db()
        session.add(trip)
        session.commit()
        
        await query.edit_message_text(
            "✅ Votre trajet a été créé avec succès!\n"
            "Les passagers intéressés pourront maintenant le réserver."
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du trajet: {str(e)}")
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la création du trajet.\n"
            "Veuillez réessayer plus tard."
        )
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    """Annule la création du trajet"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Création du trajet annulée.")
    context.user_data.clear()
    return ConversationHandler.END

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
    keyboard = []
    popular_cities = ["Fribourg", "Genève", "Lausanne", "Zürich", "Berne", "Bâle"]
    
    for city in popular_cities:
        keyboard.append([InlineKeyboardButton(city, callback_data=f"from_{city}")])
    
    keyboard.append([InlineKeyboardButton("🔍 Recherche avancée", callback_data="advanced_search")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
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

async def handle_trip_type(update: Update, context):
    """Gère le choix du type de trajet"""
    query = update.callback_query
    if query:
        await query.answer()
        
        choice = query.data.replace("trip_", "")
        context.user_data['trip_type'] = choice
        
        keyboard = []
        for city in SWISS_CITIES[:6]:
            keyboard.append([InlineKeyboardButton(city, callback_data=f"dep_{city}")])
        
        keyboard.append([InlineKeyboardButton("🔍 Autre ville", callback_data="other_city")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel_trip")])
        
        await query.edit_message_text(
            "🚗 Création d'un nouveau trajet\n\n"
            "1️⃣ Choisissez la ville de départ:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return DEPARTURE

async def handle_stop(update: Update, context):
    """Gère l'ajout d'un arrêt intermédiaire"""
    if 'stops' not in context.user_data:
        context.user_data['stops'] = []
    
    new_stop = update.message.text
    if new_stop in SWISS_CITIES:
        context.user_data['stops'].append(new_stop)
        keyboard = [
            [InlineKeyboardButton("✅ Terminer les arrêts", callback_data="stops_done")],
            [InlineKeyboardButton("➕ Ajouter un autre arrêt", callback_data="stops_add")],
            [InlineKeyboardButton("❌ Annuler", callback_data="stops_cancel")]
        ]
        await update.message.reply_text(
            f"Arrêt ajouté: {new_stop}\n"
            f"Arrêts actuels: {', '.join(context.user_data['stops'])}\n\n"
            "Voulez-vous ajouter un autre arrêt?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADDING_STOP
    else:
        await update.message.reply_text(
            "Cette ville n'est pas dans notre liste. Veuillez choisir une ville suisse valide."
        )
        return ADDING_STOP

async def add_meeting_point(update: Update, context):
    """Ajoute un point de rendez-vous précis"""
    keyboard = [
        [InlineKeyboardButton("📍 Partager ma position", callback_data="share_location")],
        [InlineKeyboardButton("✏️ Décrire le lieu", callback_data="describe_location")]
    ]
    await update.message.reply_text(
        "Où exactement retrouverez-vous les passagers?\n"
        "Choisissez une option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MEETING_POINT

def get_popular_destinations():
    """Retourne une liste des destinations populaires"""
    return [
        {"name": "Genève", "zip": "1200", "canton": "GE"},
        {"name": "Lausanne", "zip": "1000", "canton": "VD"},
        {"name": "Berne", "zip": "3000", "canton": "BE"},
        {"name": "Zürich", "zip": "8000", "canton": "ZH"},
        {"name": "Bâle", "zip": "4000", "canton": "BS"}
    ]

async def handle_departure(update: Update, context: CallbackContext):
    """Traite la ville de départ"""
    query = update.callback_query
    if query:
        await query.answer()
        if query.data == "advanced_search":
            await query.edit_message_text(
                "📍 Entrez le nom de votre ville de départ:\n"
                "Par exemple: Bulle, Neuchâtel, etc."
            )
            return ENTERING_DEPARTURE
        
        city = query.data.replace("from_", "")
        context.user_data['departure'] = city
        
        keyboard = []
        for dest in get_popular_destinations():
            if dest['name'] != city:
                keyboard.append([InlineKeyboardButton(dest['name'], callback_data=f"to_{dest['name']}")])
        
        keyboard.append([InlineKeyboardButton("🔍 Autre destination", callback_data="other_destination")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
        
        await query.edit_message_text(
            f"Départ: {city}\n\n"
            "2️⃣ Choisissez votre destination:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ENTERING_ARRIVAL
    else:
        # Recherche de ville par texte
        city = update.message.text
        if city.lower() not in [c.lower() for c in SWISS_CITIES]:
            closest_matches = get_closest_matches(city, SWISS_CITIES)
            keyboard = [[InlineKeyboardButton(c, callback_data=f"from_{c}")] for c in closest_matches]
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
            await update.message.reply_text(
                "Ville non trouvée. Voulez-vous dire:\n",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ENTERING_DEPARTURE
        
        context.user_data['departure'] = city
        keyboard = []
        for dest in get_popular_destinations():
            if dest['name'] != city:
                keyboard.append([InlineKeyboardButton(dest['name'], callback_data=f"to_{dest['name']}")])
        
        keyboard.append([InlineKeyboardButton("🔍 Autre destination", callback_data="other_destination")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
        
        await update.message.reply_text(
            f"Départ: {city}\n\n"
            "2️⃣ Choisissez votre destination:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ENTERING_ARRIVAL

async def handle_arrival(update: Update, context: CallbackContext):
    """Traite la ville d'arrivée"""
    query = update.callback_query
    if query:
        await query.answer()
        
        if query.data == "other_destination":
            await query.edit_message_text(
                "📍 Entrez le nom de votre ville d'arrivée:\n"
                "Par exemple: Bulle, Neuchâtel, etc."
            )
            return ENTERING_ARRIVAL
        
        city = query.data.replace("to_", "")
        context.user_data['arrival'] = city
    else:
        city = update.message.text
        if city.lower() not in [c.lower() for c in SWISS_CITIES]:
            closest_matches = get_closest_matches(city, SWISS_CITIES)
            keyboard = [[InlineKeyboardButton(c, callback_data=f"to_{c}")] for c in closest_matches]
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
            await update.message.reply_text(
                "Ville non trouvée. Voulez-vous dire:\n",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ENTERING_ARRIVAL
        
        context.user_data['arrival'] = city
    
    # Afficher les trajets disponibles
    session = get_db()
    trips = session.query(Trip).filter(
        Trip.departure_city == context.user_data['departure'],
        Trip.arrival_city == context.user_data['arrival']
    ).all()
    
    if trips:
        message = "🔍 Trajets trouvés:\n\n"
        keyboard = []
        for trip in trips:
            message += f"• {trip.departure_city} → {trip.arrival_city}\n"
            message += f"  📅 {trip.departure_time}\n"
            message += f"  💺 {trip.available_seats} places\n"
            message += f"  💰 {trip.price_per_seat} CHF\n\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"Réserver ({trip.price_per_seat} CHF)", 
                    callback_data=f"book_{trip.id}"
                )
            ])
    else:
        message = "❌ Aucun trajet trouvé pour cet itinéraire.\n"
        keyboard = [
            [
                InlineKeyboardButton("🔄 Nouvelle recherche", callback_data="search_trip"),
                InlineKeyboardButton("🚗 Créer un trajet", callback_data="create_trip")
            ]
        ]
    
    keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return ConversationHandler.END

def get_closest_matches(city, cities_list, max_matches=3):
    """Trouve les villes les plus proches dans la liste"""
    return [c for c in cities_list if city.lower() in c.lower()][:max_matches]

def register(application):
    """Enregistre les handlers pour les trajets"""
    # Handler principal pour la création de trajet
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('creer', create_trip_start),
            CallbackQueryHandler(create_trip_start, pattern='^create_trip$')
        ],
        states={
            DEPARTURE: [
                CallbackQueryHandler(ask_departure, pattern='^type_'),
            ],
            ARRIVAL: [
                CallbackQueryHandler(ask_arrival, pattern='^dep_'),
            ],
            DATE: [
                CallbackQueryHandler(ask_date, pattern='^arr_'),
            ],
            SEATS: [
                CallbackQueryHandler(ask_seats, pattern='^date_'),
            ],
            PRICE: [
                CallbackQueryHandler(ask_price, pattern='^seats_'),
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_trip, pattern='^price_'),
                CallbackQueryHandler(save_trip, pattern='^confirm_'),
            ],
            ADDING_STOP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stop),
                CallbackQueryHandler(handle_stop, pattern='^stops_'),
            ],
            MEETING_POINT: [
                CallbackQueryHandler(add_meeting_point, pattern='^(share|describe)_location$'),
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')],
    )
    
    # Handler pour la recherche de trajet
    search_handler = ConversationHandler(
        entry_points=[
            CommandHandler('chercher', search_trip),
            CallbackQueryHandler(search_trip, pattern='^search_trip$')
        ],
        states={
            ENTERING_DEPARTURE: [
                CallbackQueryHandler(handle_departure, pattern='^from_'),
                CallbackQueryHandler(handle_departure, pattern='^advanced_search$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_departure),
            ],
            ENTERING_ARRIVAL: [
                CallbackQueryHandler(handle_arrival, pattern='^to_'),
                CallbackQueryHandler(handle_arrival, pattern='^other_destination$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_arrival),
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern='^cancel$'),
            CommandHandler('cancel', cancel)
        ],
    )

    # Ajouter tous les handlers
    application.add_handler(conv_handler)
    application.add_handler(search_handler)
    application.add_handler(CommandHandler("mes_trajets", list_my_trips))
    
    # Ajout d'un handler global pour les callbacks qui ne seraient pas capturés par les ConversationHandler
    application.add_handler(CallbackQueryHandler(cancel, pattern='^cancel_trip$'))
```
</copilot-edited-file>
