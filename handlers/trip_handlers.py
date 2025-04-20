from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from database.models import Trip
from utils.validators import validate_date, validate_price, validate_seats
from .trip_preferences import show_preferences_menu
from utils.swiss_cities import find_locality, is_valid_locality, format_locality_result

DEPARTURE, ARRIVAL, DATE, SEATS, PRICE, CONFIRM, TRIP_TYPE, ADDING_STOP, MEETING_POINT = range(9)
CHOOSING_SEARCH, ENTERING_DEPARTURE, ENTERING_ARRIVAL, CHOOSING_DATE = range(4)

SWISS_CITIES = [
    "Zürich", "Genève", "Bâle", "Lausanne", "Berne", "Winterthour", 
    "Lucerne", "Saint-Gall", "Lugano", "Bienne", "Thoune", "Köniz",
    "La Chaux-de-Fonds", "Fribourg", "Schaffhouse", "Vernier", "Sion",
    "Uster", "Neuchâtel"
]

async def create_trip(update: Update, context):
    """Processus de création de trajet amélioré"""
    keyboard = [
        [
            InlineKeyboardButton("🚗 Trajet simple", callback_data="trip_oneway"),
            InlineKeyboardButton("🔄 Aller-retour", callback_data="trip_roundtrip")
        ],
        [
            InlineKeyboardButton("👩 Entre femmes uniquement", callback_data="trip_women_only"),
            InlineKeyboardButton("⚡ Réservation instantanée", callback_data="trip_instant")
        ]
    ]
    
    await update.message.reply_text(
        "🚗 Création d'un nouveau trajet\n"
        "Choisissez le type de trajet:",
        reply_markup=InlineKeyboardMarkup(keyboard)
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
    # Créer un clavier avec les villes principales
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

async def handle_departure(update: Update, context):
    """Traite la ville de départ"""
    try:
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            if query.data == "other_city":
                await query.edit_message_text(
                    "🏙️ Entrez le nom de la ville ou le code postal:\n"
                    "Exemple: Bulle, 1630, Fribourg, etc."
                )
                return DEPARTURE
            city_info = query.data.replace("dep_", "").split('|')
            if len(city_info) == 2:
                context.user_data['departure'] = {
                    'name': city_info[0],
                    'zip': city_info[1]
                }
        else:
            user_input = update.message.text.strip()
            logger.info(f"Searching locality: {user_input}")
            
            matches = find_locality(user_input)
            logger.info(f"Found matches: {matches}")
            
            if matches:
                keyboard = []
                for match in matches:
                    display_text = format_locality_result(match)
                    callback_data = f"dep_{match['name']}|{match['zip']}"
                    keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
                
                keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel_trip")])
                
                await update.message.reply_text(
                    "Choisissez une ville:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DEPARTURE
            else:
                await update.message.reply_text(
                    "❌ Ville non trouvée.\n"
                    "Veuillez entrer un nom de ville ou un code postal valide."
                )
                return DEPARTURE

        # Si on a une ville valide, passer à l'étape suivante
        if 'departure' in context.user_data:
            departure = context.user_data['departure']
            keyboard = []
            for city in get_popular_destinations():
                if city['name'] != departure['name']:
                    display_text = format_locality_result(city)
                    callback_data = f"arr_{city['name']}|{city['zip']}"
                    keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
            
            keyboard.append([InlineKeyboardButton("🔍 Autre ville", callback_data="other_arrival")])
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel_trip")])
            
            message_text = (
                f"Départ depuis : {departure['name']} ({departure['zip']})\n\n"
                "Choisissez la ville d'arrivée :"
            )
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    text=message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return ARRIVAL

    except Exception as e:
        logger.error(f"Error in handle_departure: {str(e)}")
        if update.message:
            await update.message.reply_text(
                "Une erreur est survenue. Veuillez réessayer avec /creer"
            )
        return ConversationHandler.END

async def arrival(update: Update, context):
    """Gère la ville d'arrivée"""
    context.user_data['arrival'] = update.message.text
    await update.message.reply_text(
        "À quelle date et heure? (format: JJ/MM/AAAA HH:MM)"
    )
    return DATE

async def handle_arrival(update: Update, context):
    """Traite la ville d'arrivée"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "other_arrival":
            await query.edit_message_text(
                "🏙️ Entrez la ville d'arrivée:\n"
                "Par exemple: Bulle, Bienne, etc."
            )
            return ARRIVAL
        city_info = query.data.replace("arr_", "").split('|')
        if len(city_info) == 2:
            context.user_data['arrival'] = {
                'name': city_info[0],
                'zip': city_info[1]
            }
    else:
        # Recherche par nom ou NPA
        query_text = update.message.text.strip()
        matches = find_locality(query_text)
        
        if matches:
            keyboard = []
            for match in matches:
                display_text = format_locality_result(match)
                callback_data = f"arr_{match['name']}|{match['zip']}"
                keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
            
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel_trip")])
            await update.message.reply_text(
                "Sélectionnez la localité :",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ARRIVAL
        else:
            await update.message.reply_text(
                "❌ Localité non trouvée.\n"
                "Veuillez entrer un nom de ville ou un code postal (NPA) valide."
            )
            return ARRIVAL

    # Si on a une ville d'arrivée valide, passer à la date
    if 'arrival' in context.user_data:
        departure = context.user_data['departure']
        arrival = context.user_data['arrival']
        
        message_text = (
            "🚗 Nouveau trajet\n\n"
            f"De: {departure['name']} ({departure['zip']})\n"
            f"À: {arrival['name']} ({arrival['zip']})\n\n"
            "📅 Entrez la date et l'heure du départ\n"
            "Format: JJ/MM/AAAA HH:MM\n"
            "Exemple: 25/04/2024 14:30"
        )
        
        if update.callback_query:
            await query.edit_message_text(text=message_text)
        else:
            await update.message.reply_text(text=message_text)
        return DATE

async def date(update: Update, context):
    """Gère la date et l'heure"""
    date_str = update.message.text
    if not validate_date(date_str):
        await update.message.reply_text("Format invalide. Utilisez JJ/MM/AAAA HH:MM")
        return DATE
    
    context.user_data['date'] = date_str
    await update.message.reply_text("Combien de places disponibles?")
    return SEATS

async def seats(update: Update, context):
    """Gère le nombre de places"""
    seats = update.message.text
    if not validate_seats(seats):
        await update.message.reply_text("Nombre de places invalide (1-8)")
        return SEATS
    
    context.user_data['seats'] = seats
    await update.message.reply_text("Quel est le prix par place (en CHF)?")
    return PRICE

async def price(update: Update, context):
    """Gère le prix"""
    price = update.message.text
    if not validate_price(price):
        await update.message.reply_text("Prix invalide (1-1000 CHF)")
        return PRICE
    
    context.user_data['price'] = price
    # Afficher le résumé
    keyboard = [[
        InlineKeyboardButton("Confirmer", callback_data="confirm_trip"),
        InlineKeyboardButton("Annuler", callback_data="cancel_trip")
    ]]
    await update.message.reply_text(
        "Résumé du trajet:\n"
        f"De: {context.user_data['departure']}\n"
        f"À: {context.user_data['arrival']}\n"
        f"Date: {context.user_data['date']}\n"
        f"Places: {context.user_data['seats']}\n"
        f"Prix: {context.user_data['price']} CHF\n\n"
        "Confirmez-vous ces informations?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM

async def confirm(update: Update, context):
    """Confirme la création du trajet"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_trip":
        # Sauvegarder le trajet dans la base de données
        # ...
        await query.message.edit_text("Trajet créé avec succès! 🚗")
    else:
        await query.message.edit_text("Création du trajet annulée.")
    
    return ConversationHandler.END

async def cancel(update: Update, context):
    """Annule la création du trajet"""
    await update.message.reply_text("Création du trajet annulée.")
    return ConversationHandler.END

async def handle_departure(update: Update, context):
    """Traite la ville de départ"""
    query = update.callback_query
    
    if query and query.data == "advanced_search":
        await query.message.reply_text(
            "📍 Entrez le nom de votre ville de départ:\n"
            "Par exemple: Bulle, Neuchâtel, etc."
        )
        return ENTERING_DEPARTURE
    
    if query:
        city = query.data.replace("from_", "")
        context.user_data['departure'] = city
        await query.answer()  # Acquitter le callback
    else:
        city = update.message.text
        if city.lower() not in [c.lower() for c in SWISS_CITIES]:
            closest_matches = get_closest_matches(city, SWISS_CITIES)
            keyboard = [[InlineKeyboardButton(c, callback_data=f"from_{c}")] for c in closest_matches]
            await update.message.reply_text(
                "Ville non trouvée. Voulez-vous dire:\n",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ENTERING_DEPARTURE
        context.user_data['departure'] = city

    # Afficher le choix de la destination
    keyboard = []
    for city in SWISS_CITIES[:6]:
        if city.lower() != context.user_data['departure'].lower():
            keyboard.append([InlineKeyboardButton(city, callback_data=f"to_{city}")])
    keyboard.append([InlineKeyboardButton("🔍 Autre destination", callback_data="other_destination")])
    
    await query.message.edit_text(
        f"Départ: {context.user_data['departure']}\n\n"
        "2️⃣ Choisissez votre destination:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ENTERING_ARRIVAL

async def handle_arrival(update: Update, context):
    """Traite la ville d'arrivée"""
    query = update.callback_query
    if query:
        city = query.data.replace("to_", "")
        context.user_data['arrival'] = city
    else:
        city = update.message.text
        if city not in SWISS_CITIES:
            await update.message.reply_text(
                "Cette ville n'est pas dans notre liste. Veuillez choisir une ville suisse:"
            )
            return ENTERING_ARRIVAL
        context.user_data['arrival'] = city

    # Afficher les trajets disponibles
    await update.message.reply_text(
        f"Recherche des trajets de {context.user_data['departure']} à {context.user_data['arrival']}...\n"
        "Cette fonctionnalité sera bientôt disponible!"
    )
    return ConversationHandler.END

def get_closest_matches(city, cities_list, max_matches=3):
    """Trouve les villes les plus proches dans la liste"""
    # Implémentation simple, à améliorer avec fuzzy matching
    return [c for c in cities_list if city.lower() in c.lower()][:max_matches]

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
        await query.answer()  # Important: toujours répondre au callback
        
        choice = query.data.replace("trip_", "")
        context.user_data['trip_type'] = choice
        
        # Afficher les villes de départ disponibles
        keyboard = []
        # Ajouter les villes principales
        for city in SWISS_CITIES[:6]:  # Prendre les 6 premières villes
            keyboard.append([InlineKeyboardButton(city, callback_data=f"dep_{city}")])
        
        keyboard.append([InlineKeyboardButton("🔍 Autre ville", callback_data="other_city")])
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel_trip")])
        
        await query.edit_message_text(
            "🚗 Création d'un nouveau trajet\n\n"
            "1️⃣ Choisissez la ville de départ:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return DEPARTURE
    else:
        # Premier affichage du menu de création
        keyboard = [
            [InlineKeyboardButton("🚗 Trajet simple", callback_data="trip_simple")],
            [InlineKeyboardButton("🔄 Trajet régulier", callback_data="trip_regular")],
            [InlineKeyboardButton("❌ Annuler", callback_data="cancel_trip")]
        ]
        
        await update.message.reply_text(
            "🚗 Création d'un nouveau trajet\n\n"
            "Quel type de trajet souhaitez-vous créer?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TRIP_TYPE

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

async def finish_stops(update: Update, context):
    """Termine l'ajout des arrêts"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "stops_done":
        keyboard = [[
            InlineKeyboardButton("Confirmer", callback_data="confirm_trip"),
            InlineKeyboardButton("Annuler", callback_data="cancel_trip")
        ]]
        await query.message.edit_text(
            "Résumé du trajet:\n"
            f"De: {context.user_data['departure']}\n"
            f"À: {context.user_data['arrival']}\n"
            f"Arrêts: {', '.join(context.user_data['stops'])}\n"
            f"Date: {context.user_data['date']}\n"
            f"Places: {context.user_data['seats']}\n"
            f"Prix: {context.user_data['price']} CHF\n\n"
            "Confirmez-vous ces informations?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRM
    elif query.data == "stops_add":
        await query.message.edit_text("Entrez le nom de la ville pour l'arrêt suivant:")
        return ADDING_STOP
    else:  # stops_cancel
        return await cancel(update, context)

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

async def handle_trip_details(update: Update, context):
    """Gère les détails supplémentaires du trajet"""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Trajet régulier", callback_data="recurring"),
            InlineKeyboardButton("↩️ Aller-retour", callback_data="round_trip")
        ],
        [
            InlineKeyboardButton("⏰ Délai réservation", callback_data="booking_deadline"),
            InlineKeyboardButton("💺 Sièges spécifiques", callback_data="seat_selection")
        ]
    ]
    await update.message.reply_text(
        "Options supplémentaires:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_other_city(update: Update, context):
    """Gère le choix d'une ville non listée"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏙️ Entrez le nom de la ville:\n"
        "Par exemple: Bulle, Bienne, etc."
    )
    return DEPARTURE

async def handle_date(update: Update, context):
    """Gère l'entrée de la date"""
    try:
        date_str = update.message.text
        if not validate_date(date_str):
            await update.message.reply_text(
                "❌ Format invalide! Utilisez le format: JJ/MM/AAAA HH:MM\n"
                "Par exemple: 25/04/2024 14:30"
            )
            return DATE
        
        context.user_data['date'] = date_str
        await update.message.reply_text(
            "Combien de places disponibles? (1-8)"
        )
        return SEATS

    except Exception as e:
        print(f"Error in handle_date: {e}")
        await update.message.reply_text("Une erreur est survenue. Utilisez /creer pour recommencer.")
        return ConversationHandler.END

async def handle_seats(update: Update, context):
    """Gère l'entrée du nombre de places"""
    try:
        seats = update.message.text
        if not validate_seats(seats):
            await update.message.reply_text("❌ Nombre invalide! Choisissez entre 1 et 8 places.")
            return SEATS
        
        context.user_data['seats'] = seats
        await update.message.reply_text(
            "Quel est le prix par place en CHF?"
        )
        return PRICE

    except Exception as e:
        print(f"Error in handle_seats: {e}")
        await update.message.reply_text("Une erreur est survenue.")
        return ConversationHandler.END

async def handle_price(update: Update, context):
    """Gère l'entrée du prix"""
    try:
        price = update.message.text
        if not validate_price(price):
            await update.message.reply_text("❌ Prix invalide! Le prix doit être entre 1 et 1000 CHF.")
            return PRICE
        
        context.user_data['price'] = price
        
        # Afficher le résumé
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmer", callback_data="confirm_trip"),
                InlineKeyboardButton("❌ Annuler", callback_data="cancel_trip")
            ]
        ]
        
        await update.message.reply_text(
            "📋 Résumé du trajet:\n\n"
            f"🚗 De: {context.user_data['departure']}\n"
            f"🏁 À: {context.user_data['arrival']}\n"
            f"📅 Date: {context.user_data['date']}\n"
            f"💺 Places: {context.user_data['seats']}\n"
            f"💰 Prix: {context.user_data['price']} CHF\n\n"
            "Tout est correct?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRM

    except Exception as e:
        print(f"Error in handle_price: {e}")
        await update.message.reply_text("Une erreur est survenue.")
        return ConversationHandler.END

def get_popular_destinations():
    """Retourne une liste des destinations populaires"""
    # À implémenter : récupérer les destinations les plus fréquentes
    return [
        {"name": "Genève", "zip": "1200", "canton": "GE"},
        {"name": "Lausanne", "zip": "1000", "canton": "VD"},
        {"name": "Berne", "zip": "3000", "canton": "BE"},
        {"name": "Zürich", "zip": "8000", "canton": "ZH"},
        {"name": "Bâle", "zip": "4000", "canton": "BS"}
    ]

def register(application):
    """Enregistre les handlers pour les trajets"""
    # Handler principal pour la création de trajets
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('creer', handle_trip_type),
            CallbackQueryHandler(handle_trip_type, pattern='^create_trip$')
        ],
        states={
            TRIP_TYPE: [
                CallbackQueryHandler(handle_trip_type, pattern='^trip_'),
                CallbackQueryHandler(cancel, pattern='^cancel_trip$')
            ],
            DEPARTURE: [
                CallbackQueryHandler(handle_departure, pattern='^dep_'),
                CallbackQueryHandler(handle_other_city, pattern='^other_city$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_departure),
                CallbackQueryHandler(cancel, pattern='^cancel_trip$')
            ],
            ARRIVAL: [
                CallbackQueryHandler(handle_arrival, pattern='^arr_'),
                CallbackQueryHandler(handle_other_city, pattern='^other_arrival$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_arrival),
                CallbackQueryHandler(cancel, pattern='^cancel_trip$')
            ],
            DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date),
                CallbackQueryHandler(cancel, pattern='^cancel_trip$')
            ],
            SEATS: {
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_seats),
                CallbackQueryHandler(cancel, pattern='^cancel_trip$')
            },
            PRICE: {
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price),
                CallbackQueryHandler(cancel, pattern='^cancel_trip$')
            },
            CONFIRM: {
                CallbackQueryHandler(confirm, pattern='^confirm_trip$'),
                CallbackQueryHandler(cancel, pattern='^cancel_trip$')
            }
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)

    # Handler pour la recherche
    search_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('chercher', search_trip),
            CallbackQueryHandler(search_trip, pattern='^search_trip$')
        ],
        states={
            ENTERING_DEPARTURE: {
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_departure),
                CallbackQueryHandler(handle_departure, pattern='^from_')
            },
            ENTERING_ARRIVAL: {
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_arrival),
                CallbackQueryHandler(handle_arrival, pattern='^to_')
            }
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="search_trip_conversation",
        per_message=True
    )
    
    # Ajouter les handlers
    application.add_handler(search_conv_handler)
    application.add_handler(CommandHandler("chercher", search_trip))
    application.add_handler(CommandHandler("mes_trajets", list_my_trips))
