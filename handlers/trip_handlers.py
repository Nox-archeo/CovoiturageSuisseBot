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
    filters,
    ContextTypes
)
from telegram.constants import ParseMode
from database.models import Trip, User, Booking
from database import get_db
from database.db_manager import SessionLocal
from utils.validators import validate_date, validate_price, validate_seats
from utils.swiss_cities import find_locality, format_locality_result, load_localities
from utils.swiss_pricing import round_to_nearest_0_05, format_swiss_price
from utils.date_picker import (
    start_date_selection, handle_calendar_navigation, 
    handle_day_selection, handle_time_selection, handle_minute_selection, handle_datetime_action,
    handle_flex_time_selection,
    CALENDAR_NAVIGATION_PATTERN, CALENDAR_DAY_SELECTION_PATTERN, 
    CALENDAR_CANCEL_PATTERN, TIME_SELECTION_PATTERN, TIME_BACK_PATTERN, TIME_CANCEL_PATTERN,
    MINUTE_SELECTION_PATTERN, MINUTE_BACK_PATTERN, MINUTE_CANCEL_PATTERN,
    FLEX_TIME_PATTERN, DATETIME_ACTION_PATTERN
)
from utils.location_picker import (
    start_location_selection, handle_location_selection, handle_location_query,
    LOCATION_SELECTION_PATTERN
)

# Configuration du logger
logger = logging.getLogger(__name__)

# --- UTILS GPS pour calcul automatique du prix ---
def load_city_coords():
    """Charge les coordonnées des villes depuis le fichier cities.json"""
    cities_coords_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'src', 'bot', 'data', 'cities.json'
    )
    try:
        with open(cities_coords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return { (c['name'], c.get('npa')): (c.get('lat'), c.get('lon')) for c in data['cities'] if 'lat' in c and 'lon' in c }
    except Exception as e:
        logger.warning(f"Impossible de charger les coordonnées des villes: {e}")
        return {}

CITY_COORDS = load_city_coords()

def get_coords(city_name, zip_code=None):
    """Récupère les coordonnées d'une ville"""
    if not CITY_COORDS:
        return None, None
    
    # Essayer d'abord avec le nom et le zip
    if zip_code:
        coords = CITY_COORDS.get((city_name, zip_code))
        if coords:
            return coords
    
    # Sinon, chercher par nom seulement
    for (name, npa), coords in CITY_COORDS.items():
        if name == city_name:
            return coords
    
    return None, None

def parse_city_name(full_city_name):
    """Parse une ville au format 'Nom (ZIP)' ou 'Nom'"""
    if '(' in full_city_name and ')' in full_city_name:
        # Format: "Lausanne (1000)"
        name_part = full_city_name.split('(')[0].strip()
        zip_part = full_city_name.split('(')[1].split(')')[0].strip()
        return name_part, zip_part
    else:
        # Format: "Lausanne"
        return full_city_name.strip(), None

def compute_price_auto(departure_city, arrival_city):
    """Calcule automatiquement le prix basé sur la distance"""
    try:
        # Parse les noms de villes
        dep_name, dep_zip = parse_city_name(departure_city)
        arr_name, arr_zip = parse_city_name(arrival_city)
        
        # Récupérer les coordonnées
        lat1, lon1 = get_coords(dep_name, dep_zip)
        lat2, lon2 = get_coords(arr_name, arr_zip)
        
        if not all([lat1, lon1, lat2, lon2]):
            logger.warning(f"Coordonnées introuvables pour {departure_city} -> {arrival_city}")
            return None, None
        
        # Utiliser la vraie distance routière via OpenRouteService
        from utils.route_distance import get_route_distance_with_fallback
        dist_km, is_route_distance = get_route_distance_with_fallback((lat1, lon1), (lat2, lon2), departure_city, arrival_city)
        
        if dist_km is None:
            logger.error("Impossible de calculer la distance (même avec fallback)")
            return None, None
        
        # Log pour debug
        distance_type = "routière" if is_route_distance else "à vol d'oiseau (fallback)"
        logger.info(f"Distance {distance_type} calculée: {dist_km} km")
        
        # Calcul du prix avec barème progressif suisse et arrondi 0.05 CHF
        from utils.swiss_pricing import calculate_trip_price_swiss
        price = calculate_trip_price_swiss(dist_km)
        
        return price, round(dist_km, 1)
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul de prix: {e}")
        return None, None

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
    ADDING_STOP,
    EDIT_FIELD,
    EDIT_VALUE,
    # États pour la modification avec interface complète
    EDIT_DEPARTURE_LOCATION,
    EDIT_ARRIVAL_LOCATION,
    EDIT_DATE_CALENDAR,
    EDIT_TIME,
    EDIT_MINUTE,
    EDIT_CONFIRM_DATETIME,
    EDIT_SEATS_INPUT
) = range(20)

async def start_trip(update: Update, context: CallbackContext):
    """Point d'entrée pour démarrer un nouveau trajet"""
    keyboard = [
        [
            InlineKeyboardButton("🚗 Conducteur", callback_data="trip_type:driver"),
            InlineKeyboardButton("🎒 Passager", callback_data="trip_type:passenger")
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
        ],
        [InlineKeyboardButton("✅ Terminer", callback_data="pref_done")]
    ]
    
    await update.callback_query.message.edit_text(
        "🔧 Préférences du trajet\n\n"
        "Sélectionnez vos préférences (optionnel):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM

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

async def show_driver_trips_by_time(update: Update, context: CallbackContext):
    """Affiche le menu de choix entre trajets à venir et trajets passés pour les conducteurs"""
    query = update.callback_query
    await query.answer()
    
    message = (
        "🚗 *Mes trajets (Conducteur)*\n\n"
        "Que souhaitez-vous consulter ?"
    )
    
    keyboard = [
        [InlineKeyboardButton("📅 À venir", callback_data="trips:show_driver_upcoming")],
        [InlineKeyboardButton("🕓 Passés", callback_data="trips:show_driver_past")],
        [InlineKeyboardButton("🔙 Retour", callback_data="trips:menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_show_trips_by_time(update: Update, context: CallbackContext):
    """Affiche les trajets selon le type (à venir ou passés) avec boutons individuels"""
    query = update.callback_query
    await query.answer()
    
    trip_type = query.data.split(":")[1]  # upcoming ou past
    is_upcoming = "upcoming" in trip_type
    
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await query.edit_message_text(
            "⚠️ Utilisateur non trouvé.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")
            ]])
        )
        return
    
    # Filtre selon le type de trajets demandé
    if is_upcoming:
        trips = db.query(Trip).filter(
            Trip.driver_id == user.id,
            Trip.is_published == True,
            Trip.status != 'completed',  # Garde les trajets jusqu'à confirmation complète
            Trip.is_cancelled == False
        ).order_by(Trip.departure_time).all()
        title = "🚗 *Mes trajets à venir*"
        back_button_data = "trips:show_driver"
    else:
        trips = db.query(Trip).filter(
            Trip.driver_id == user.id,
            Trip.is_published == True,
            Trip.departure_time <= datetime.now()
        ).order_by(Trip.departure_time.desc()).all()
        title = "🚗 *Mes trajets passés*"
        back_button_data = "trips:show_driver"
    
    if not trips:
        no_trips_msg = "Aucun trajet à venir." if is_upcoming else "Aucun trajet passé."
        await query.edit_message_text(
            f"{title}\n\n{no_trips_msg}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Créer un trajet", callback_data="menu:create")],
                [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    # Afficher le titre principal
    await query.edit_message_text(title, parse_mode="Markdown")
    
    # Envoyer chaque trajet individuellement avec ses boutons
    for trip in trips:
        try:
            # Vérification supplémentaire pour exclure les trajets annulés
            if getattr(trip, 'is_cancelled', False):
                continue
                
            departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
            
            # Compter les réservations actives
            booking_count = db.query(Booking).filter(
                Booking.trip_id == trip.id, 
                Booking.status.in_(["pending", "confirmed"])
            ).count()
            
            trip_text = (
                f"📍 **{trip.departure_city}** → **{trip.arrival_city}**\n"
                f"📅 {departure_date}\n"
                f"💰 {format_swiss_price(round_to_nearest_0_05(trip.price_per_seat))} CHF/place\n"
                f"💺 {booking_count}/{trip.seats_available} réservations"
            )
            
            # Boutons selon le type de trajet
            buttons = []
            if is_upcoming:
                # Trajets à venir : Modifier (si pas de réservations), Supprimer, Signaler
                if booking_count == 0:
                    buttons.append(InlineKeyboardButton("✏️ Modifier", callback_data=f"trip:edit:{trip.id}"))
                
                # NOUVEAU: Bouton pour contacter les passagers (si il y en a)
                if booking_count > 0:
                    buttons.append(InlineKeyboardButton("� Contacter passagers", callback_data=f"contact_passengers:{trip.id}"))
                
                buttons.append(InlineKeyboardButton("�🗑 Supprimer", callback_data=f"trip:delete:{trip.id}"))
                buttons.append(InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip.id}"))
            else:
                # Trajets passés : Contacter (si il y a eu des passagers), Supprimer, Signaler
                if booking_count > 0:
                    buttons.append(InlineKeyboardButton("💬 Voir passagers", callback_data=f"contact_passengers:{trip.id}"))
                buttons.append(InlineKeyboardButton("🗑 Supprimer", callback_data=f"trip:delete:{trip.id}"))
                buttons.append(InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip.id}"))
            
            # Organiser les boutons en lignes (maximum 2 par ligne)
            keyboard = []
            for i in range(0, len(buttons), 2):
                row = buttons[i:i+2]
                keyboard.append(row)
            
            # Envoyer le trajet avec ses boutons
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=trip_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du trajet {trip.id}: {e}")
            continue
    
    # Envoyer les boutons de navigation à la fin
    navigation_keyboard = [
        [InlineKeyboardButton("➕ Créer un trajet", callback_data="menu:create")],
        [InlineKeyboardButton("🔙 Retour", callback_data=back_button_data)]
    ]
    
    # IMPORTANT: Ajouter un return pour éviter l'affichage du message d'erreur
    return

async def list_my_trips(update: Update, context: CallbackContext):
    """
    Fonction unifiée pour afficher les trajets de l'utilisateur.
    Utilisée par tous les boutons "Mes trajets" du bot pour une expérience cohérente.
    """
    try:
        # Gérer l'update (peut venir d'un callback ou d'un message)
        if hasattr(update, 'callback_query') and update.callback_query:
            query = update.callback_query
            await query.answer()
        else:
            query = None
            
        user_id = update.effective_user.id
        
        # Utiliser SessionLocal comme context manager pour éviter DetachedInstanceError
        with SessionLocal() as db:
            # Trouver l'utilisateur
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                logger.error(f"Utilisateur non trouvé pour telegram_id={user_id}")
                error_msg = "⚠️ Utilisateur non trouvé. Veuillez utiliser /start."
                keyboard = [[InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]]
                
                if query:
                    await query.edit_message_text(error_msg, reply_markup=InlineKeyboardMarkup(keyboard))
                else:
                    await update.message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(keyboard))
                return

            # Récupérer tous les trajets à venir non annulés du conducteur
            trips_query = db.query(Trip).filter(
                Trip.driver_id == user.id,
                Trip.is_published == True,
                Trip.status != 'completed',  # Garde jusqu'à confirmation
                Trip.is_cancelled == False
            ).order_by(Trip.departure_time).all()
            
            # Extraire toutes les données nécessaires avant de fermer la session
            trips_data = []
            for trip in trips_query:
                # Compter les réservations actives
                booking_count = db.query(Booking).filter(
                    Booking.trip_id == trip.id, 
                    Booking.status.in_(["pending", "confirmed"])
                ).count()
                
                trip_data = {
                    'id': trip.id,
                    'departure_city': trip.departure_city,
                    'arrival_city': trip.arrival_city,
                    'departure_time': trip.departure_time,
                    'price_per_seat': trip.price_per_seat,
                    'seats_available': trip.seats_available,
                    'recurring': trip.recurring,
                    'group_id': trip.group_id,
                    'is_cancelled': getattr(trip, 'is_cancelled', False),
                    'booking_count': booking_count
                }
                trips_data.append(trip_data)
        
        logger.info(f"[MES TRAJETS] {len(trips_data)} trajets trouvés pour user_id={user_id}")
        
        # Regrouper les trajets réguliers par group_id
        trip_groups = {}
        individual_trips = []
        
        logger.info(f"[DEBUG] Début du groupement, {len(trips_data)} trajets trouvés")
        
        for trip_data in trips_data:
            logger.info(f"[DEBUG] Trip {trip_data['id']}: recurring={trip_data['recurring']}, group_id='{trip_data['group_id']}', cancelled={trip_data['is_cancelled']}")
            logger.info(f"[DEBUG] Trip {trip_data['id']}: recurring type={type(trip_data['recurring'])}, group_id type={type(trip_data['group_id'])}")
            logger.info(f"[DEBUG] Trip {trip_data['id']}: recurring bool={bool(trip_data['recurring'])}, group_id bool={bool(trip_data['group_id'])}")
            
            if trip_data['is_cancelled']:
                logger.info(f"[DEBUG] Trip {trip_data['id']} ignoré car annulé")
                continue
                
            if trip_data['recurring'] and trip_data['group_id']:
                # Trajet régulier - le regrouper
                logger.info(f"[DEBUG] Trip {trip_data['id']} ajouté au groupe {trip_data['group_id']}")
                if trip_data['group_id'] not in trip_groups:
                    trip_groups[trip_data['group_id']] = []
                trip_groups[trip_data['group_id']].append(trip_data)
            else:
                # Trajet individuel
                logger.info(f"[DEBUG] Trip {trip_data['id']} ajouté aux trajets individuels (recurring={trip_data['recurring']}, group_id='{trip_data['group_id']}')")
                individual_trips.append(trip_data)
        
        logger.info(f"[DEBUG] Résultat groupement: {len(trip_groups)} groupes, {len(individual_trips)} individuels")
        
        active_blocks = []
        
        # Afficher les groupes de trajets réguliers
        for group_id, group_trips in trip_groups.items():
            if len(group_trips) > 0:
                # Trier les trajets par date
                group_trips.sort(key=lambda x: x['departure_time'])
                first_trip = group_trips[0]
                
                # Compter le total des réservations dans le groupe
                total_bookings = 0
                total_seats = 0
                for trip_data in group_trips:
                    total_bookings += trip_data['booking_count']
                    total_seats += trip_data['seats_available']
                
                # Format amélioré avec première date et nombre de trajets
                first_date = first_trip['departure_time'].strftime("%d/%m/%Y à %H:%M")
                
                trip_str = (
                    f"📍 {first_trip['departure_city']} → {first_trip['arrival_city']}\n"
                    f"📅 {first_date}\n"
                    f"🗓️ Trajet régulier sur {len(group_trips)} dates\n"
                    f"💰 {format_swiss_price(round_to_nearest_0_05(first_trip['price_per_seat']))}/place\n"
                    f"💺 {total_bookings}/{total_seats} réservations totales"
                )
                
                keyboard_row = [
                    InlineKeyboardButton("👁️ Voir les dates", callback_data=f"regular_group:view_dates:{group_id}"),
                    InlineKeyboardButton("✏️ Modifier", callback_data=f"regular_group:edit:{group_id}"),
                    InlineKeyboardButton("🗑 Supprimer", callback_data=f"regular_group:delete:{group_id}")
                ]
                # Ajouter le bouton signaler sur une deuxième ligne pour les groupes réguliers
                keyboard_row_2 = [
                    InlineKeyboardButton("🚩 Signaler", callback_data=f"regular_group:report:{group_id}")
                ]
                active_blocks.append({
                    "text": trip_str, 
                    "keyboard_row": keyboard_row,
                    "keyboard_row_2": keyboard_row_2
                })
        
        # Afficher les trajets individuels
        for trip_data in individual_trips:
            try:
                departure_date = trip_data['departure_time'].strftime("%d/%m/%Y à %H:%M") if trip_data['departure_time'] else "?"
                booking_count = trip_data['booking_count']
                
                trip_str = (
                    f"📍 {trip_data['departure_city']} → {trip_data['arrival_city']}\n"
                    f"📅 {departure_date}\n"
                    f"💰 {format_swiss_price(round_to_nearest_0_05(trip_data['price_per_seat']))}/place\n"
                    f"💺 {booking_count}/{trip_data['seats_available']} réservations\n"
                )
                
                # Boutons d'action pour trajets individuels
                if booking_count == 0:
                    # Trajet sans réservation - boutons d'édition
                    keyboard_row = [
                        InlineKeyboardButton("✏️ Modifier", callback_data=f"trip:edit:{trip_data['id']}"),
                        InlineKeyboardButton("🗑 Supprimer", callback_data=f"trip:delete:{trip_data['id']}"),
                        InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip_data['id']}")
                    ]
                    active_blocks.append({"text": trip_str, "keyboard_row": keyboard_row})
                else:
                    # Trajet avec réservations - boutons de gestion passagers
                    keyboard_row_1 = [
                        InlineKeyboardButton("💬 Contacter passagers", callback_data=f"driver:contact_passengers:{trip_data['id']}"),
                        InlineKeyboardButton("📍 Définir point RDV", callback_data=f"driver:set_meeting:{trip_data['id']}")
                    ]
                    keyboard_row_2 = [
                        InlineKeyboardButton("✅ Confirmer trajet effectué", callback_data=f"confirm_trip_driver:{trip_data['id']}"),
                        InlineKeyboardButton("👥 Voir passagers", callback_data=f"driver:view_passengers:{trip_data['id']}")
                    ]
                    keyboard_row_3 = [
                        InlineKeyboardButton("ℹ️ Détails du trajet", callback_data=f"driver:trip_details:{trip_data['id']}"),
                        InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip_data['id']}")
                    ]
                    active_blocks.append({
                        "text": trip_str, 
                        "keyboard_row": keyboard_row_1,
                        "keyboard_row_2": keyboard_row_2,
                        "keyboard_row_3": keyboard_row_3
                    })
                
            except Exception as e:
                logger.error(f"[MES TRAJETS] Erreur sur le trajet {trip_data.get('id', '?')}: {e}")
                continue

        # Construction du message
        if not active_blocks:
            message = "🚗 *Mes trajets à venir*\n\nAucun trajet prévu pour le moment."
            keyboard = [
                [InlineKeyboardButton("➕ Créer un trajet", callback_data="menu:create")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
            ]
            
            # Affichage du message pour le cas "aucun trajet"
            if query:
                await query.edit_message_text(
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        else:
            # Afficher d'abord le titre principal
            title_message = "🚗 *Mes trajets à venir*"
            
            if query:
                await query.edit_message_text(
                    text=title_message,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    text=title_message,
                    parse_mode="Markdown"
                )
            
            # Envoyer chaque trajet individuellement avec ses boutons
            trip_number = 1
            for block in active_blocks:
                try:
                    # Message du trajet avec numérotation
                    trip_message = f"**Trajet {trip_number}:**\n{block['text']}"
                    
                    # Construire le clavier pour ce trajet spécifique
                    trip_keyboard = []
                    if 'keyboard_row' in block and block['keyboard_row']:
                        trip_keyboard.append(block['keyboard_row'])
                    # Ajouter la deuxième ligne de boutons s'il y en a une
                    if 'keyboard_row_2' in block and block['keyboard_row_2']:
                        trip_keyboard.append(block['keyboard_row_2'])
                    # Ajouter la troisième ligne de boutons s'il y en a une
                    if 'keyboard_row_3' in block and block['keyboard_row_3']:
                        trip_keyboard.append(block['keyboard_row_3'])
                    
                    # Envoyer le message du trajet avec ses boutons
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=trip_message,
                        reply_markup=InlineKeyboardMarkup(trip_keyboard),
                        parse_mode="Markdown"
                    )
                    
                    trip_number += 1
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi du trajet {trip_number}: {e}")
                    continue
            
            # Envoyer les boutons de navigation à la fin
            navigation_keyboard = [
                [InlineKeyboardButton("➕ Créer un trajet", callback_data="menu:create")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
            ]
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="─────────────────────",
                reply_markup=InlineKeyboardMarkup(navigation_keyboard)
            )
            
    except Exception as e:
        logger.error(f"Erreur dans list_my_trips: {str(e)}")
        error_msg = "⚠️ Erreur lors de l'affichage de vos trajets."
        keyboard = [[InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]]
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_trip_view(update: Update, context: CallbackContext):
    """Handler simple pour afficher les détails d'un trajet (si besoin)"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(":")[2])
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_past")
                ]])
            )
            return
        
        # Afficher les détails du trajet
        departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
        booking_count = db.query(Booking).filter(
            Booking.trip_id == trip.id, 
            Booking.status.in_(["pending", "confirmed", "completed"])
        ).count()
        
        message = (
            f"🚗 *Détails du trajet*\n\n"
            f"📍 Départ : {trip.departure_city}\n"
            f"🎯 Arrivée : {trip.arrival_city}\n"
            f"📅 Date : {departure_date}\n"
            f"💰 Prix : {format_swiss_price(round_to_nearest_0_05(trip.price_per_seat))} CHF/place\n"
            f"💺 Réservations : {booking_count}/{trip.seats_available}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🗑 Supprimer", callback_data=f"trip:delete:{trip.id}")],
            [InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip.id}")],
            [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_past")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des détails: {e}")
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de l'affichage des détails.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_past")
            ]])
        )

async def list_my_trips_menu(update: Update, context: CallbackContext):
    """Affiche le menu de choix entre trajets conducteur et passager, ou redirige directement selon le profil actuel"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        message = (
            "❌ *Profil requis*\n\n"
            "Vous devez créer un profil avant de pouvoir voir vos trajets."
        )
        keyboard = [
            [InlineKeyboardButton("✅ Créer mon profil", callback_data="menu:create_profile")],
            [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
        ]
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        return ConversationHandler.END
    
    # Déterminer le profil actuel de l'utilisateur
    has_driver_profile = user.is_driver and user.paypal_email
    has_passenger_profile = True  # Tous les utilisateurs peuvent être passagers
    
    # Si l'utilisateur n'a qu'un profil passager, rediriger directement vers la gestion des trajets passagers
    if has_passenger_profile and not has_driver_profile:
        return await show_passenger_trip_management(update, context)
    
    # Si l'utilisateur n'a qu'un profil conducteur, rediriger vers les trajets conducteur
    elif has_driver_profile and not has_passenger_profile:
        return await show_driver_trips_by_time(update, context)
    
    # Si l'utilisateur a les deux profils, afficher le menu de choix
    else:
        message = (
            "📋 *Mes trajets*\n\n"
            "Que souhaitez-vous consulter ?"
        )
        keyboard = [
            [InlineKeyboardButton("🚗 Mes trajets (Conducteur)", callback_data="trips:show_driver")],
            [InlineKeyboardButton("🎒 Mes demandes (Passager)", callback_data="passenger_trip_management")],
            [InlineKeyboardButton("� Retour au profil", callback_data="profile:back_to_profile")],
            [InlineKeyboardButton("�🔙 Retour au menu", callback_data="menu:back_to_main")]
        ]
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    
    return ConversationHandler.END

async def list_passenger_trips(update: Update, context: CallbackContext):
    """Affiche les demandes de trajet et réservations de l'utilisateur en tant que passager"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await query.edit_message_text(
                "❌ *Profil requis*\n\n"
                "Vous devez créer un profil avant de pouvoir voir vos trajets.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Créer mon profil", callback_data="menu:create_profile")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # 1. Récupérer les DEMANDES de trajet créées par l'utilisateur
        trip_requests = db.query(Trip).filter(
            Trip.creator_id == user.id,
            Trip.trip_role == "passenger",
            Trip.status != 'completed',  # Garde jusqu'à confirmation
            Trip.is_cancelled == False
        ).order_by(Trip.departure_time).all()
        
        # 2. Récupérer les RÉSERVATIONS sur trajets d'autres conducteurs
        bookings = db.query(Booking).filter(
            Booking.passenger_id == user.id,
            Booking.status.in_(["pending", "confirmed"])
        ).join(Trip).filter(
            Trip.status != 'completed'  # Garde jusqu'à confirmation
        ).order_by(Trip.departure_time).all()
        
        # Construire le message
        total_items = len(trip_requests) + len(bookings)
        
        if total_items == 0:
            message = "🎒 *Mes trajets passager*\n\nAucune demande ou réservation à venir."
            keyboard = [
                [InlineKeyboardButton("� Créer une demande", callback_data="trip_type:passenger")],
                [InlineKeyboardButton("�🔍 Chercher un trajet", callback_data="menu:search")],
                [InlineKeyboardButton("🔙 Retour", callback_data="trips:menu")]
            ]
        else:
            message = f"🎒 *Mes trajets passager*\n\n"
            keyboard = []
            
            # Afficher les demandes de trajet
            if trip_requests:
                message += f"📋 **{len(trip_requests)} demande(s) de trajet créée(s):**\n\n"
                for request in trip_requests:
                    departure_date = request.departure_time.strftime("%d/%m/%Y à %H:%M")
                    request_text = (
                        f"🔍 **Recherche:** {request.departure_city} → {request.arrival_city}\n"
                        f"📅 {departure_date}\n"
                        f"👥 {request.seats_available} place(s) recherchée(s)\n"
                        f"📝 {request.additional_info or 'Aucune information'}\n\n"
                    )
                    message += request_text
            
            # Afficher les réservations
            if bookings:
                message += f"🎫 **{len(bookings)} réservation(s) confirmée(s):**\n\n"
                for booking in bookings:
                    trip = booking.trip
                    departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
                    
                    reservation_text = (
                        f"✅ **Réservé:** {trip.departure_city} → {trip.arrival_city}\n"
                        f"📅 {departure_date}\n"
                        f"💺 {booking.seats} place(s) réservée(s)\n"
                        f"💰 {booking.amount:.2f} CHF\n"
                        f"🔄 Statut: {'Confirmé' if booking.status == 'confirmed' else 'En attente'}\n\n"
                    )
                    message += reservation_text
            
            # Boutons de navigation
            keyboard = [
                [InlineKeyboardButton("👥 Créer une demande", callback_data="trip_type:passenger")],
                [InlineKeyboardButton("🔍 Chercher un trajet", callback_data="menu:search")],
                [InlineKeyboardButton("🔙 Retour", callback_data="trips:menu")]
            ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur dans list_passenger_trips: {str(e)}")
        await query.edit_message_text(
            "⚠️ Erreur lors de l'affichage de vos réservations.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="trips:menu")
            ]])
        )

# =============================================================================
# HANDLERS POUR MODIFICATION DE TRAJET
# =============================================================================

async def handle_trip_edit(update: Update, context: CallbackContext):
    """Affiche le menu de modification d'un trajet"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(":")[2])
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
                ]])
            )
            return
        
        # Vérifier s'il y a des réservations
        booking_count = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.status.in_(["pending", "confirmed"])
        ).count()
        
        if booking_count > 0:
            await query.edit_message_text(
                f"❌ *Modification impossible*\n\n"
                f"Ce trajet a déjà {booking_count} réservation(s).\n"
                f"Vous ne pouvez plus le modifier.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        # Stocker l'ID du trajet dans le contexte
        context.user_data['editing_trip_id'] = trip_id
        
        # Nettoyer les données temporaires d'une session précédente
        context.user_data.pop('selected_date', None)
        context.user_data.pop('selected_hour', None)
        context.user_data.pop('selected_minute', None)
        context.user_data.pop('new_datetime', None)
        context.user_data.pop('mode', None)  # Remettre à zéro le mode
        
        # Afficher le trajet et le menu de modification
        departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
        
        message = (
            f"✏️ *Modification du trajet*\n\n"
            f"📍 **{trip.departure_city}** → **{trip.arrival_city}**\n"
            f"📅 {departure_date}\n"
            f"💰 {format_swiss_price(round_to_nearest_0_05(trip.price_per_seat))} CHF/place\n"
            f"💺 {trip.seats_available} places disponibles\n\n"
            f"Que souhaitez-vous modifier ?"
        )
        
        keyboard = [
            [InlineKeyboardButton("📍 Ville de départ", callback_data=f"edit_field:departure_city:{trip_id}")],
            [InlineKeyboardButton("🎯 Ville d'arrivée", callback_data=f"edit_field:arrival_city:{trip_id}")],
            [InlineKeyboardButton("📅 Date et heure", callback_data=f"edit_field:departure_time:{trip_id}")],
            [InlineKeyboardButton(" Nombre de places", callback_data=f"edit_field:seats_available:{trip_id}")],
            [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du menu de modification: {e}")
        await query.edit_message_text(
            "❌ Une erreur est survenue.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
            ]])
        )

async def handle_edit_field(update: Update, context: CallbackContext):
    """Gère la sélection d'un champ à modifier avec interface appropriée"""
    query = update.callback_query
    await query.answer()
    
    try:
        data_parts = query.data.split(":")
        field_name = data_parts[1]
        trip_id = int(data_parts[2])
        
        # Nettoyer d'abord toutes les données temporaires pour repartir proprement
        context.user_data.pop('selected_date', None)
        context.user_data.pop('selected_hour', None)
        context.user_data.pop('selected_minute', None)
        context.user_data.pop('new_datetime', None)
        
        # Définir les nouvelles données
        context.user_data['editing_trip_id'] = trip_id
        context.user_data['editing_field'] = field_name
        context.user_data['mode'] = 'edit'  # Important pour les utils
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
                ]])
            )
            return
        
        # Redirection selon le champ à modifier
        if field_name == 'departure_city':
            # Utiliser l'interface de sélection de ville
            popular_cities = ["Fribourg", "Genève", "Lausanne", "Zürich", "Berne", "Bâle"]
            keyboard = []
            
            for city in popular_cities:
                keyboard.append([InlineKeyboardButton(city, callback_data=f"edit_departure_select:{city}")])
            
            keyboard.append([InlineKeyboardButton("🔍 Recherche avancée", callback_data="edit_departure_search")])
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")])
            
            await query.edit_message_text(
                f"📍 *Modification du départ*\n\n"
                f"Départ actuel : **{trip.departure_city}**\n\n"
                f"Choisissez la nouvelle ville de départ :",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return EDIT_DEPARTURE_LOCATION
            
        elif field_name == 'arrival_city':
            # Utiliser l'interface de sélection de ville
            popular_cities = ["Fribourg", "Genève", "Lausanne", "Zürich", "Berne", "Bâle"]
            keyboard = []
            
            for city in popular_cities:
                keyboard.append([InlineKeyboardButton(city, callback_data=f"edit_arrival_select:{city}")])
            
            keyboard.append([InlineKeyboardButton("🔍 Recherche avancée", callback_data="edit_arrival_search")])
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")])
            
            await query.edit_message_text(
                f"🎯 *Modification de l'arrivée*\n\n"
                f"Arrivée actuelle : **{trip.arrival_city}**\n\n"
                f"Choisissez la nouvelle ville d'arrivée :",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return EDIT_ARRIVAL_LOCATION
            
        elif field_name == 'departure_time':
            # Utiliser l'interface de calendrier
            current_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
            
            # Sauvegarder l'info pour le callback du calendrier
            context.user_data['editing_trip_id'] = trip_id
            context.user_data['editing_field'] = field_name
            context.user_data['mode'] = 'edit'
            
            # Lancer le sélecteur de date avec des callbacks standards
            from utils.date_picker import get_calendar_keyboard
            now = datetime.now()
            
            await query.edit_message_text(
                f"📅 *Modification de la date et heure*\n\n"
                f"Date/heure actuelle : **{current_date}**\n\n"
                f"Sélectionnez la nouvelle date :",
                reply_markup=get_calendar_keyboard(now.year, now.month),
                parse_mode="Markdown"
            )
            
            return EDIT_DATE_CALENDAR
            
        elif field_name == 'seats_available':
            # Interface simple pour les places
            keyboard = []
            for i in range(1, 9):  # 1 à 8 places
                keyboard.append([InlineKeyboardButton(f"{i} place{'s' if i > 1 else ''}", callback_data=f"edit_seats_select:{i}")])
            
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")])
            
            await query.edit_message_text(
                f"💺 *Modification du nombre de places*\n\n"
                f"Places actuelles : **{trip.seats_available}**\n\n"
                f"Choisissez le nouveau nombre de places :",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return EDIT_SEATS_INPUT
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection du champ: {e}")
        await query.edit_message_text(
            "❌ Une erreur est survenue.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
            ]])
        )

async def handle_edit_departure_select(update: Update, context: CallbackContext):
    """Gère la sélection directe d'une ville de départ depuis les suggestions"""
    query = update.callback_query
    await query.answer()
    
    try:
        city_name = query.data.split(":")[1]
        trip_id = context.user_data.get('editing_trip_id')
        
        if not trip_id:
            await query.edit_message_text("❌ Session expirée.")
            return
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet introuvable.")
            return
        
        # Mettre à jour la ville de départ
        old_city = trip.departure_city
        trip.departure_city = city_name
        
        # Recalculer automatiquement le prix avec arrondi suisse
        new_price, distance = compute_price_auto(city_name, trip.arrival_city)
        price_message = ""
        if new_price is not None:
            old_price = trip.price_per_seat
            trip.price_per_seat = new_price
            price_message = f"\n💰 Prix recalculé : {format_swiss_price(round_to_nearest_0_05(old_price))} CHF → **{format_swiss_price(new_price)} CHF** ({distance} km)"
        
        db.commit()
        
        keyboard = [[
            InlineKeyboardButton("🔙 Retour aux trajets", callback_data="trips:show_driver_upcoming"),
            InlineKeyboardButton("✏️ Modifier encore", callback_data=f"trip:edit:{trip_id}")
        ]]
        
        await query.edit_message_text(
            f"✅ *Ville de départ modifiée*\n\n"
            f"Ancien départ : {old_city}\n"
            f"Nouveau départ : **{city_name}**{price_message}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la modification du départ: {e}")
        await query.edit_message_text("❌ Une erreur est survenue.")

async def handle_edit_departure_search(update: Update, context: CallbackContext):
    """Lance la recherche avancée pour la ville de départ"""
    query = update.callback_query
    await query.answer()
    
    trip_id = context.user_data.get('editing_trip_id')
    
    await query.edit_message_text(
        f"🔍 *Recherche de ville de départ*\n\n"
        f"Veuillez entrer le nom de la ville ou son code postal :",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")
        ]]),
        parse_mode="Markdown"
    )
    
    return EDIT_DEPARTURE_LOCATION

async def handle_edit_departure_text(update: Update, context: CallbackContext):
    """Gère la saisie texte pour la recherche de ville de départ"""
    user_input = update.message.text.strip()
    trip_id = context.user_data.get('editing_trip_id')
    
    try:
        # Utiliser la même logique que create_trip_handler
        matches = find_locality(user_input)
        
        if matches:
            keyboard = []
            for match in matches[:5]:  # Limite à 5 résultats
                display_text = f"{match['name']} ({match['zip']})"
                callback_data = f"edit_departure_loc:{match['zip']}|{match['name']}"
                keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
            
            keyboard.append([InlineKeyboardButton("🔄 Réessayer", callback_data="edit_departure_search")])
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")])
            
            await update.message.reply_text(
                "📍 Voici les localités trouvées. Choisissez votre nouvelle ville de départ :",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                "❌ Ville non trouvée. Veuillez réessayer avec un autre nom ou code postal.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Réessayer", callback_data="edit_departure_search"),
                    InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")
                ]])
            )
        
        return EDIT_DEPARTURE_LOCATION
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de ville: {e}")
        await update.message.reply_text(
            "❌ Une erreur est survenue lors de la recherche.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")
            ]])
        )
        return EDIT_DEPARTURE_LOCATION

async def handle_edit_departure_loc_callback(update: Update, context: CallbackContext):
    """Gère la sélection d'une localité spécifique après recherche"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Format: edit_departure_loc:zip|name
        loc_data = query.data.split(":", 1)[1]  # Récupère tout après le premier ':'
        zip_code, city_name = loc_data.split("|", 1)
        
        trip_id = context.user_data.get('editing_trip_id')
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet introuvable.")
            return
        
        # Mettre à jour la ville de départ
        old_city = trip.departure_city
        new_departure_city = f"{city_name} ({zip_code})"
        trip.departure_city = new_departure_city
        
        # Recalculer automatiquement le prix avec arrondi suisse
        new_price, distance = compute_price_auto(new_departure_city, trip.arrival_city)
        price_message = ""
        if new_price is not None:
            old_price = trip.price_per_seat
            trip.price_per_seat = new_price
            price_message = f"\n💰 Prix recalculé : {format_swiss_price(round_to_nearest_0_05(old_price))} CHF → **{format_swiss_price(new_price)} CHF** ({distance} km)"
        
        db.commit()
        
        keyboard = [[
            InlineKeyboardButton("🔙 Retour aux trajets", callback_data="trips:show_driver_upcoming"),
            InlineKeyboardButton("✏️ Modifier encore", callback_data=f"trip:edit:{trip_id}")
        ]]
        
        await query.edit_message_text(
            f"✅ *Ville de départ modifiée*\n\n"
            f"Ancien départ : {old_city}\n"
            f"Nouveau départ : **{city_name} ({zip_code})**{price_message}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de localité: {e}")
        await query.edit_message_text("❌ Une erreur est survenue.")

async def handle_edit_arrival_select(update: Update, context: CallbackContext):
    """Gère la sélection directe d'une ville d'arrivée depuis les suggestions"""
    query = update.callback_query
    await query.answer()
    
    try:
        city_name = query.data.split(":")[1]
        trip_id = context.user_data.get('editing_trip_id')
        
        if not trip_id:
            await query.edit_message_text("❌ Session expirée.")
            return
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet introuvable.")
            return
        
        # Mettre à jour la ville d'arrivée
        old_city = trip.arrival_city
        trip.arrival_city = city_name
        
        # Recalculer automatiquement le prix avec arrondi suisse
        new_price, distance = compute_price_auto(trip.departure_city, city_name)
        price_message = ""
        if new_price is not None:
            old_price = trip.price_per_seat
            trip.price_per_seat = new_price
            price_message = f"\n💰 Prix recalculé : {format_swiss_price(round_to_nearest_0_05(old_price))} CHF → **{format_swiss_price(new_price)} CHF** ({distance} km)"
        
        db.commit()
        
        keyboard = [[
            InlineKeyboardButton("🔙 Retour aux trajets", callback_data="trips:show_driver_upcoming"),
            InlineKeyboardButton("✏️ Modifier encore", callback_data=f"trip:edit:{trip_id}")
        ]]
        
        await query.edit_message_text(
            f"✅ *Ville d'arrivée modifiée*\n\n"
            f"Ancienne arrivée : {old_city}\n"
            f"Nouvelle arrivée : **{city_name}**{price_message}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la modification de l'arrivée: {e}")
        await query.edit_message_text("❌ Une erreur est survenue.")

async def handle_edit_arrival_search(update: Update, context: CallbackContext):
    """Lance la recherche avancée pour la ville d'arrivée"""
    query = update.callback_query
    await query.answer()
    
    trip_id = context.user_data.get('editing_trip_id')
    
    await query.edit_message_text(
        f"🔍 *Recherche de ville d'arrivée*\n\n"
        f"Veuillez entrer le nom de la ville ou son code postal :",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")
        ]]),
        parse_mode="Markdown"
    )
    
    return EDIT_ARRIVAL_LOCATION

async def handle_edit_arrival_text(update: Update, context: CallbackContext):
    """Gère la saisie texte pour la recherche de ville d'arrivée"""
    user_input = update.message.text.strip()
    trip_id = context.user_data.get('editing_trip_id')
    
    try:
        matches = find_locality(user_input)
        
        if matches:
            keyboard = []
            for match in matches[:5]:  # Limite à 5 résultats
                display_text = f"{match['name']} ({match['zip']})"
                callback_data = f"edit_arrival_loc:{match['zip']}|{match['name']}"
                keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
            
            keyboard.append([InlineKeyboardButton("🔄 Réessayer", callback_data="edit_arrival_search")])
            keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")])
            
            await update.message.reply_text(
                "📍 Voici les localités trouvées. Choisissez votre nouvelle ville d'arrivée :",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                "❌ Ville non trouvée. Veuillez réessayer avec un autre nom ou code postal.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Réessayer", callback_data="edit_arrival_search"),
                    InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")
                ]])
            )
        
        return EDIT_ARRIVAL_LOCATION
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de ville: {e}")
        await update.message.reply_text(
            "❌ Une erreur est survenue lors de la recherche.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Annuler", callback_data=f"trip:edit:{trip_id}")
            ]])
        )
        return EDIT_ARRIVAL_LOCATION

async def handle_edit_arrival_loc_callback(update: Update, context: CallbackContext):
    """Gère la sélection d'une localité spécifique pour l'arrivée après recherche"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Format: edit_arrival_loc:zip|name
        loc_data = query.data.split(":", 1)[1]  # Récupère tout après le premier ':'
        zip_code, city_name = loc_data.split("|", 1)
        
        trip_id = context.user_data.get('editing_trip_id')
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet introuvable.")
            return
        
        # Mettre à jour la ville d'arrivée
        old_city = trip.arrival_city
        new_arrival_city = f"{city_name} ({zip_code})"
        trip.arrival_city = new_arrival_city
        
        # Recalculer automatiquement le prix avec arrondi suisse
        new_price, distance = compute_price_auto(trip.departure_city, new_arrival_city)
        price_message = ""
        if new_price is not None:
            old_price = trip.price_per_seat
            trip.price_per_seat = new_price
            price_message = f"\n💰 Prix recalculé : {format_swiss_price(round_to_nearest_0_05(old_price))} CHF → **{format_swiss_price(new_price)} CHF** ({distance} km)"
        
        db.commit()
        
        keyboard = [[
            InlineKeyboardButton("🔙 Retour aux trajets", callback_data="trips:show_driver_upcoming"),
            InlineKeyboardButton("✏️ Modifier encore", callback_data=f"trip:edit:{trip_id}")
        ]]
        
        await query.edit_message_text(
            f"✅ *Ville d'arrivée modifiée*\n\n"
            f"Ancienne arrivée : {old_city}\n"
            f"Nouvelle arrivée : **{city_name} ({zip_code})**{price_message}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de localité: {e}")
        await query.edit_message_text("❌ Une erreur est survenue.")

async def handle_edit_seats_select(update: Update, context: CallbackContext):
    """Gère la sélection du nombre de places"""
    query = update.callback_query
    await query.answer()
    
    try:
        seats_count = int(query.data.split(":")[1])
        trip_id = context.user_data.get('editing_trip_id')
        
        if not trip_id:
            await query.edit_message_text("❌ Session expirée.")
            return
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet introuvable.")
            return
        
        # Vérifier qu'on ne réduit pas en dessous des réservations existantes
        from database.models import Booking
        confirmed_bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id, 
            Booking.status == 'confirmed'
        ).count()
        
        if seats_count < confirmed_bookings:
            await query.edit_message_text(
                f"❌ *Impossible de réduire les places*\n\n"
                f"Vous avez {confirmed_bookings} réservation{'s' if confirmed_bookings > 1 else ''} confirmée{'s' if confirmed_bookings > 1 else ''}.\n"
                f"Vous ne pouvez pas réduire à {seats_count} place{'s' if seats_count > 1 else ''}.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        # Mettre à jour le nombre de places
        old_seats = trip.seats_available
        trip.seats_available = seats_count
        db.commit()
        
        keyboard = [[
            InlineKeyboardButton("🔙 Retour aux trajets", callback_data="trips:show_driver_upcoming"),
            InlineKeyboardButton("✏️ Modifier encore", callback_data=f"trip:edit:{trip_id}")
        ]]
        
        await query.edit_message_text(
            f"✅ *Nombre de places modifié*\n\n"
            f"Anciennes places : {old_seats}\n"
            f"Nouvelles places : **{seats_count}**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la modification des places: {e}")
        await query.edit_message_text("❌ Une erreur est survenue.")

async def handle_edit_calendar_navigation(update: Update, context: CallbackContext):
    """Gère la navigation dans le calendrier pour l'édition"""
    query = update.callback_query
    await query.answer()
    
    # Vérifier que nous sommes en mode édition
    if context.user_data.get('mode') != 'edit':
        return  # Ne pas traiter si pas en mode édition
    
    try:
        from utils.date_picker import handle_calendar_navigation
        # Delegate to the date_picker utility
        return await handle_calendar_navigation(update, context)
    except Exception as e:
        logger.error(f"Erreur navigation calendrier édition: {e}")
        trip_id = context.user_data.get('editing_trip_id')
        if trip_id:
            await query.edit_message_text(
                "❌ Erreur avec le calendrier.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                ]])
            )

async def handle_edit_day_selection(update: Update, context: CallbackContext):
    """Gère la sélection d'un jour dans le calendrier pour l'édition"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"DEBUG: handle_edit_day_selection called with data: {query.data}")
    logger.info(f"DEBUG: User mode: {context.user_data.get('mode')}")
    
    # Vérifier que nous sommes en mode édition
    if context.user_data.get('mode') != 'edit':
        logger.warning("Not in edit mode, ignoring")
        return  # Ne pas traiter si pas en mode édition
    
    try:
        # Extraire la date sélectionnée du callback_data
        logger.info(f"DEBUG: Parsing callback data: {query.data}")
        parts = query.data.split(':')
        logger.info(f"DEBUG: Parts: {parts}")
        
        if len(parts) != 5:
            logger.error(f"Invalid callback data format: {query.data}")
            return EDIT_DATE_CALENDAR
            
        _, _, year, month, day = parts
        selected_date = datetime(int(year), int(month), int(day))
        
        logger.info(f"DEBUG: Selected date: {selected_date}")
        
        # Sauvegarder la date dans le contexte
        context.user_data['selected_date'] = selected_date
        
        # Importer la fonction pour générer le clavier d'heure
        from utils.date_picker import get_time_keyboard
        
        # Afficher le sélecteur d'heure pour l'édition
        await query.edit_message_text(
            f"🕒 Sélectionnez l'heure pour le {selected_date.strftime('%d %B %Y')}:",
            reply_markup=get_time_keyboard(selected_date)
        )
        
        logger.info("DEBUG: Returning EDIT_TIME")
        return EDIT_TIME
        
    except Exception as e:
        logger.error(f"Erreur sélection jour édition: {e}")
        trip_id = context.user_data.get('editing_trip_id')
        if trip_id:
            await query.edit_message_text(
                "❌ Erreur avec le calendrier.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                ]])
            )
        return EDIT_DATE_CALENDAR

async def handle_edit_time_selection(update: Update, context: CallbackContext):
    """Gère la sélection de l'heure pour l'édition"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"DEBUG: handle_edit_time_selection called with data: {query.data}")
    logger.info(f"DEBUG: User mode: {context.user_data.get('mode')}")
    
    # Vérifier que nous sommes en mode édition
    if context.user_data.get('mode') != 'edit':
        logger.warning("Not in edit mode, ignoring")
        return  # Ne pas traiter si pas en mode édition
    
    try:
        # Vérifier s'il s'agit d'une option d'horaire flexible
        if query.data.startswith("flex_time:"):
            logger.info("DEBUG: Handling flex time")
            from utils.date_picker import handle_flex_time_selection
            return await handle_flex_time_selection(update, context)
        
        # Gérer la sélection d'heure
        if query.data.startswith("time:") and len(query.data.split(':')) == 2:
            # Sélection de l'heure uniquement (format: time:HH)
            _, hour = query.data.split(':')
            hour = int(hour)
            
            # Stocker temporairement l'heure sélectionnée
            context.user_data['selected_hour'] = hour
            
            # Récupérer la date sélectionnée
            selected_date = context.user_data.get('selected_date')
            if not selected_date:
                logger.error("Date non trouvée dans le contexte")
                await query.edit_message_text(
                    "❌ Erreur: La date n'a pas été définie. Veuillez réessayer."
                )
                return EDIT_DATE_CALENDAR
            
            # Importer la fonction pour générer le clavier de minutes
            from utils.date_picker import get_minute_keyboard
            
            # Afficher le sélecteur de minutes
            await query.edit_message_text(
                f"⏱️ Sélectionnez les minutes pour {selected_date.strftime('%d %B %Y')} à {hour:02d}h :",
                reply_markup=get_minute_keyboard(hour)
            )
            return EDIT_MINUTE
            
        elif query.data.startswith("time:") and len(query.data.split(':')) == 3:
            # Ancien format pour compatibilité - extraire l'heure et les minutes (format: time:HH:MM)
            _, hour, minute = query.data.split(':')
            hour, minute = int(hour), int(minute)
            
            # Récupérer la date sélectionnée
            selected_date = context.user_data.get('selected_date')
            if not selected_date:
                logger.error("Date non trouvée dans le contexte")
                await query.edit_message_text(
                    "❌ Erreur: La date n'a pas été définie. Veuillez réessayer."
                )
                return EDIT_DATE_CALENDAR
            
            # Créer la datetime complète
            final_datetime = selected_date.replace(hour=hour, minute=minute)
            
            # Sauvegarder dans le contexte
            context.user_data['new_datetime'] = final_datetime
            
            # Passer à la confirmation
            await query.edit_message_text(
                f"📅 Nouvelle date et heure sélectionnées :\n"
                f"📆 **{final_datetime.strftime('%A %d %B %Y')}**\n"
                f"🕒 **{final_datetime.strftime('%H:%M')}**\n\n"
                f"Confirmez-vous cette modification ?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Confirmer", callback_data="edit_datetime:confirm")],
                    [InlineKeyboardButton("❌ Annuler", callback_data="edit_datetime:cancel")]
                ])
            )
            return EDIT_CONFIRM_DATETIME
            
    except Exception as e:
        logger.error(f"Erreur sélection heure édition: {e}")
        trip_id = context.user_data.get('editing_trip_id')
        if trip_id:
            await query.edit_message_text(
                "❌ Erreur avec la sélection d'heure.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                ]])
            )
        return EDIT_TIME

async def handle_edit_minute_selection(update: Update, context: CallbackContext):
    """Gère la sélection des minutes pour l'édition"""
    query = update.callback_query
    await query.answer()
    
    # Vérifier que nous sommes en mode édition
    if context.user_data.get('mode') != 'edit':
        return  # Ne pas traiter si pas en mode édition
    
    try:
        # Gérer la sélection de minutes
        if query.data.startswith("minute:"):
            parts = query.data.split(':')
            if len(parts) == 3:
                # Format: minute:hour:minute
                _, hour, minute = parts
                minute = int(minute)
                hour = int(hour)
                # Mettre à jour l'heure si différente de celle stockée
                context.user_data['selected_hour'] = hour
            else:
                # Format: minute:minute (ancien format)
                _, minute = parts
                minute = int(minute)
            
            # Récupérer la date et l'heure sélectionnées
            selected_date = context.user_data.get('selected_date')
            selected_hour = context.user_data.get('selected_hour')
            
            if not selected_date or selected_hour is None:
                logger.error("Date ou heure non trouvée dans le contexte")
                await query.edit_message_text(
                    "❌ Erreur: Les informations de date/heure sont incomplètes. Veuillez réessayer."
                )
                return EDIT_DATE_CALENDAR
            
            # Créer la datetime complète
            final_datetime = selected_date.replace(hour=selected_hour, minute=minute)
            
            # Sauvegarder dans le contexte
            context.user_data['new_datetime'] = final_datetime
            
            # Afficher la confirmation
            await query.edit_message_text(
                f"📅 Nouvelle date et heure sélectionnées :\n"
                f"📆 **{final_datetime.strftime('%A %d %B %Y')}**\n"
                f"🕒 **{final_datetime.strftime('%H:%M')}**\n\n"
                f"Confirmez-vous cette modification ?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Confirmer", callback_data="edit_datetime:confirm")],
                    [InlineKeyboardButton("❌ Annuler", callback_data="edit_datetime:cancel")]
                ])
            )
            return EDIT_CONFIRM_DATETIME
            
    except Exception as e:
        logger.error(f"Erreur sélection minute édition: {e}")
        trip_id = context.user_data.get('editing_trip_id')
        if trip_id:
            await query.edit_message_text(
                "❌ Erreur avec la sélection de minutes.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                ]])
            )
        return EDIT_MINUTE

async def handle_edit_datetime_confirm(update: Update, context: CallbackContext):
    """Confirme ou annule la nouvelle date/heure sélectionnée"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"🔍 Debug confirmation - query.data: {query.data}")
    logger.info(f"🔍 Debug confirmation - context mode: {context.user_data.get('mode')}")
    logger.info(f"🔍 Debug confirmation - trip_id: {context.user_data.get('editing_trip_id')}")
    
    # Vérifier que nous sommes en mode édition
    if context.user_data.get('mode') != 'edit':
        logger.warning(f"⚠️ Mode incorrect: {context.user_data.get('mode')}")
        return ConversationHandler.END  # Retourner une valeur explicite
    
    try:
        trip_id = context.user_data.get('editing_trip_id')
        
        # Vérifier si c'est un cancel
        if query.data == "edit_datetime:cancel":
            # Nettoyer les données temporaires
            context.user_data.pop('selected_date', None)
            context.user_data.pop('selected_hour', None)
            context.user_data.pop('selected_minute', None)
            context.user_data.pop('new_datetime', None)  # Nettoyer aussi new_datetime
            context.user_data.pop('mode', None)
            
            # Retourner à l'édition du trajet
            await handle_trip_edit(update, context)
            return ConversationHandler.END
        
        # Récupérer la date/heure sélectionnée
        # Priorité à new_datetime si elle existe (flux complet), sinon utiliser les composants
        new_datetime = context.user_data.get('new_datetime')
        
        logger.info(f"🔍 Debug - new_datetime: {new_datetime}")
        logger.info(f"🔍 Debug - selected_date: {context.user_data.get('selected_date')}")
        logger.info(f"🔍 Debug - selected_hour: {context.user_data.get('selected_hour')}")
        logger.info(f"🔍 Debug - selected_minute: {context.user_data.get('selected_minute')}")
        
        if not new_datetime:
            # Sinon, construire à partir des composants
            selected_date = context.user_data.get('selected_date')
            selected_hour = context.user_data.get('selected_hour')
            selected_minute = context.user_data.get('selected_minute')
            
            if not all([selected_date, selected_hour is not None, selected_minute is not None]):
                await query.edit_message_text(
                    "❌ Données de date/heure incomplètes.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                    ]])
                )
                return ConversationHandler.END
            
            # Construire la nouvelle datetime
            new_datetime = datetime.combine(selected_date, datetime.min.time().replace(
                hour=selected_hour, minute=selected_minute
            ))
        
        # Vérifier que la date n'est pas dans le passé
        if new_datetime < datetime.now():
            await query.edit_message_text(
                "❌ La date et heure ne peuvent pas être dans le passé.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Recommencer", callback_data=f"edit_field:departure_time:{trip_id}"),
                    InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                ]])
            )
            return ConversationHandler.END
        
        # Mettre à jour le trajet
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet introuvable.")
            return ConversationHandler.END
        
        old_datetime = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
        trip.departure_time = new_datetime
        db.commit()
        
        logger.info(f"✅ Date/heure mise à jour: {old_datetime} → {new_datetime.strftime('%d/%m/%Y à %H:%M')}")
        
        # Nettoyer les données temporaires
        context.user_data.pop('selected_date', None)
        context.user_data.pop('selected_hour', None)
        context.user_data.pop('selected_minute', None)
        context.user_data.pop('new_datetime', None)  # Nettoyer aussi new_datetime
        # Ne pas supprimer le mode ici pour permettre de recommencer
        # context.user_data.pop('mode', None)  # Nettoyer le mode
        
        keyboard = [[
            InlineKeyboardButton("🔙 Retour aux trajets", callback_data="trips:show_driver_upcoming"),
            InlineKeyboardButton("✏️ Modifier encore", callback_data=f"trip:edit:{trip_id}")
        ]]
        
        await query.edit_message_text(
            f"✅ *Date et heure modifiées*\n\n"
            f"Ancienne date : {old_datetime}\n"
            f"Nouvelle date : **{new_datetime.strftime('%d/%m/%Y à %H:%M')}**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Erreur lors de la confirmation de date/heure: {e}")
        
        # Nettoyer le contexte en cas d'erreur pour permettre un redémarrage propre
        context.user_data.pop('selected_date', None)
        context.user_data.pop('selected_hour', None)
        context.user_data.pop('selected_minute', None)
        context.user_data.pop('new_datetime', None)
        # Ne pas supprimer le mode pour permettre de recommencer
        # context.user_data.pop('mode', None)
        
        trip_id = context.user_data.get('editing_trip_id')
        if trip_id:
            await query.edit_message_text(
                "❌ Une erreur est survenue.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                ]])
            )

async def handle_edit_value(update: Update, context: CallbackContext):
    """Traite la nouvelle valeur saisie par l'utilisateur"""
    if update.callback_query:
        # L'utilisateur a cliqué sur Annuler
        trip_id = context.user_data.get('editing_trip_id')
        if trip_id:
            return await handle_trip_edit(update, context)
        return
    
    try:
        new_value = update.message.text.strip()
        trip_id = context.user_data.get('editing_trip_id')
        field_name = context.user_data.get('editing_field')
        
        if not trip_id or not field_name:
            await update.message.reply_text(
                "❌ Session expirée. Veuillez recommencer.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
                ]])
            )
            return
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await update.message.reply_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
                ]])
            )
            return
        
        # Validation et mise à jour selon le champ
        if field_name == 'departure_city':
            trip.departure_city = new_value
            success_msg = f"✅ Ville de départ mise à jour : {new_value}"
            
        elif field_name == 'arrival_city':
            trip.arrival_city = new_value
            success_msg = f"✅ Ville d'arrivée mise à jour : {new_value}"
            
        elif field_name == 'departure_time':
            try:
                # Parser la date au format JJ/MM/AAAA HH:MM
                new_datetime = datetime.strptime(new_value, "%d/%m/%Y %H:%M")
                
                # Vérifier que la date n'est pas dans le passé
                if new_datetime <= datetime.now():
                    await update.message.reply_text(
                        "❌ La date doit être dans le futur.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                        ]])
                    )
                    return
                
                trip.departure_time = new_datetime
                success_msg = f"✅ Date et heure mises à jour : {new_datetime.strftime('%d/%m/%Y à %H:%M')}"
                
            except ValueError:
                await update.message.reply_text(
                    "❌ Format de date invalide. Utilisez : JJ/MM/AAAA HH:MM\n"
                    "Exemple : 25/12/2024 14:30",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                    ]])
                )
                return
                
        elif field_name == 'seats_available':
            try:
                new_seats = int(new_value)
                if new_seats <= 0 or new_seats > 8:
                    raise ValueError("Le nombre de places doit être entre 1 et 8")
                
                trip.seats_available = new_seats
                success_msg = f"✅ Nombre de places mis à jour : {new_seats}"
                
            except ValueError:
                await update.message.reply_text(
                    "❌ Nombre de places invalide. Entrez un nombre entre 1 et 8.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Retour", callback_data=f"trip:edit:{trip_id}")
                    ]])
                )
                return
        
        # Sauvegarder les modifications
        db.commit()
        logger.info(f"Trajet {trip_id} modifié : {field_name} = {new_value}")
        
        # Afficher le message de succès et retourner au menu de modification
        keyboard = [
            [InlineKeyboardButton("✏️ Modifier autre chose", callback_data=f"trip:edit:{trip_id}")],
            [InlineKeyboardButton("🔙 Retour aux trajets", callback_data="trips:show_driver_upcoming")]
        ]
        
        await update.message.reply_text(
            success_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Nettoyer le contexte
        context.user_data.pop('editing_trip_id', None)
        context.user_data.pop('editing_field', None)
        
    except Exception as e:
        logger.error(f"Erreur lors de la modification: {e}")
        await update.message.reply_text(
            "❌ Une erreur est survenue lors de la modification.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
            ]])
        )

# =============================================================================
# HANDLERS POUR SUPPRESSION DE TRAJET
# =============================================================================

async def handle_trip_delete(update: Update, context: CallbackContext):
    """Demande confirmation avant suppression d'un trajet"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(":")[2])
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
                ]])
            )
            return
        
        # Vérifier s'il y a des réservations
        booking_count = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.status.in_(["pending", "confirmed"])
        ).count()
        
        departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
        
        if booking_count > 0:
            message = (
                f"⚠️ *Attention*\n\n"
                f"📍 **{trip.departure_city}** → **{trip.arrival_city}**\n"
                f"📅 {departure_date}\n\n"
                f"Ce trajet a **{booking_count} réservation(s)**.\n"
                f"Si vous le supprimez, les passagers seront automatiquement remboursés.\n\n"
                f"Êtes-vous sûr(e) de vouloir supprimer ce trajet ?"
            )
        else:
            message = (
                f"🗑 *Suppression du trajet*\n\n"
                f"📍 **{trip.departure_city}** → **{trip.arrival_city}**\n"
                f"📅 {departure_date}\n\n"
                f"Êtes-vous sûr(e) de vouloir supprimer ce trajet ?"
            )
        
        keyboard = [
            [InlineKeyboardButton("🗑 Oui, supprimer", callback_data=f"trip:delete_confirm:{trip_id}")],
            [InlineKeyboardButton("❌ Non, annuler", callback_data="trips:show_driver_upcoming")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la demande de suppression: {e}")
        await query.edit_message_text(
            "❌ Une erreur est survenue.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
            ]])
        )

async def handle_trip_delete_confirm(update: Update, context: CallbackContext):
    """Supprime définitivement le trajet après confirmation"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(":")[2])
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
                ]])
            )
            return
        
        # Récupérer les réservations avant suppression pour les notifications
        bookings = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.status.in_(["pending", "confirmed"])
        ).all()
        
        trip_info = f"{trip.departure_city} → {trip.arrival_city} le {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}"
        
        # NOUVEAU: Traiter les remboursements automatiques AVANT la suppression
        refund_success = False
        if bookings:
            try:
                from cancellation_refund_manager import handle_trip_cancellation_refunds
                refund_success = await handle_trip_cancellation_refunds(trip_id, context.bot)
                logger.info(f"Remboursements automatiques pour le trajet {trip_id}: {'réussis' if refund_success else 'partiels'}")
            except Exception as refund_error:
                logger.error(f"Erreur lors des remboursements automatiques: {refund_error}")
        
        # Supprimer toutes les réservations liées
        for booking in bookings:
            db.delete(booking)
        
        # Supprimer le trajet
        db.delete(trip)
        db.commit()
        
        logger.info(f"Trajet {trip_id} supprimé avec {len(bookings)} réservations")
        
        # Message de confirmation adapté selon le succès des remboursements
        if bookings:
            if refund_success:
                message = (
                    f"✅ *Trajet supprimé*\n\n"
                    f"Le trajet **{trip_info}** a été supprimé.\n\n"
                    f"**{len(bookings)} passager(s)** ont été automatiquement remboursés via PayPal."
                )
            else:
                message = (
                    f"✅ *Trajet supprimé*\n\n"
                    f"Le trajet **{trip_info}** a été supprimé.\n\n"
                    f"**{len(bookings)} passager(s)** seront remboursés (certains remboursements en cours de traitement)."
                )
        else:
            message = (
                f"✅ *Trajet supprimé*\n\n"
                f"Le trajet **{trip_info}** a été supprimé avec succès."
            )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Retour aux trajets", callback_data="trips:show_driver_upcoming")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        logger.info(f"Trajet {trip_id} supprimé avec gestion automatique des remboursements")
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du trajet: {e}")
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la suppression.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
            ]])
        )

# =============================================================================
# HANDLERS POUR SIGNALEMENT DE TRAJET
# =============================================================================

async def handle_trip_report(update: Update, context: CallbackContext):
    """Gère le signalement d'un trajet"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(":")[2])
        user_id = update.effective_user.id
        
        # Récupérer les informations du trajet
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Trajet introuvable.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
                ]])
            )
            return
        
        trip_info = f"{trip.departure_city} → {trip.arrival_city} le {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}"
        
        message = (
            f"🚩 **Signaler un problème**\n\n"
            f"**Trajet concerné :**\n"
            f"{trip_info}\n\n"
            f"Si vous rencontrez un problème avec ce trajet :\n"
            f"• Personne malveillante\n"
            f"• Trajet non validé par l'autre partie\n"
            f"• Comportement inapproprié\n"
            f"• Ou tout autre problème\n\n"
            f"📧 **Contactez-nous directement :**\n"
            f"**covoituragesuisse@gmail.com**\n\n"
            f"Décrivez votre problème avec les détails du trajet.\n"
            f"Nous traiterons votre demande dans les plus brefs délais."
        )
        
        keyboard = [
            [InlineKeyboardButton("📧 Copier l'email", callback_data=f"copy_email:{trip_id}")],
            [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Log du signalement pour statistiques
        logger.info(f"SIGNALEMENT: Utilisateur {user_id} a demandé l'email pour signaler le trajet {trip_id} ({trip_info})")
        
    except Exception as e:
        logger.error(f"Erreur lors du signalement: {e}")
        await query.edit_message_text(
            "❌ Une erreur est survenue lors du signalement.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")
            ]])
        )

async def handle_copy_email(update: Update, context: CallbackContext):
    """Affiche l'email de contact de manière claire pour copier"""
    query = update.callback_query
    await query.answer()
    
    message = (
        f"📧 **Email de contact**\n\n"
        f"**covoituragesuisse@gmail.com**\n\n"
        f"Copiez cette adresse email et envoyez-nous un message détaillé concernant le problème rencontré.\n\n"
        f"Merci de préciser :\n"
        f"• Le trajet concerné\n"
        f"• La nature du problème\n"
        f"• Vos coordonnées pour vous recontacter"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver_upcoming")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# =============================================================================
# FONCTION D'ENREGISTREMENT DES HANDLERS
# =============================================================================

def register(application):
    """Enregistre tous les handlers de trip_handlers"""
    logger.info("Enregistrement des handlers trip_handlers")
    
    # Handlers principaux
    application.add_handler(CallbackQueryHandler(show_driver_trips_by_time, pattern=r"^trips:show_driver$"))
    application.add_handler(CallbackQueryHandler(handle_show_trips_by_time, pattern=r"^trips:show_driver_(upcoming|past)$"))
    
    # Handlers pour l'affichage des détails
    application.add_handler(CallbackQueryHandler(handle_trip_view, pattern=r"^trip:view:\d+$"))
    
    # Handlers pour la modification
    application.add_handler(CallbackQueryHandler(handle_trip_edit, pattern=r"^trip:edit:\d+$"))
    # Note: handle_edit_field pour cities est géré par edit_location_conv_handler
    
    # Handlers pour l'édition directe des villes (suggestions)
    application.add_handler(CallbackQueryHandler(handle_edit_departure_select, pattern=r"^edit_departure_select:"))
    application.add_handler(CallbackQueryHandler(handle_edit_arrival_select, pattern=r"^edit_arrival_select:"))
    
    # Handlers pour l'édition du nombre de places
    application.add_handler(CallbackQueryHandler(handle_edit_seats_select, pattern=r"^edit_seats_select:"))
    
    # Note: handle_edit_field pour departure_time est géré par edit_datetime_conv_handler
    # Note: handle_edit_field pour cities est géré par edit_location_conv_handler
    # ConversationHandler pour la saisie des nouvelles valeurs simples
    from telegram.ext import ConversationHandler, MessageHandler, filters
    
    edit_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_edit_field, pattern=r"^edit_field:seats_available:")],
        states={
            EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_value),
                CallbackQueryHandler(handle_trip_edit, pattern=r"^trip:edit:\d+$")  # Pour le bouton Annuler
            ]
        },
        fallbacks=[
            CallbackQueryHandler(handle_trip_edit, pattern=r"^trip:edit:\d+$"),
            CallbackQueryHandler(show_driver_trips_by_time, pattern=r"^trips:show_driver_upcoming$")
        ],
        per_message=False
    )
    
    # ConversationHandler pour l'édition des villes avec recherche
    edit_location_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_edit_field, pattern=r"^edit_field:(departure_city|arrival_city):"),
            CallbackQueryHandler(handle_edit_departure_search, pattern=r"^edit_departure_search$"),
            CallbackQueryHandler(handle_edit_arrival_search, pattern=r"^edit_arrival_search$")
        ],
        states={
            EDIT_DEPARTURE_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_departure_text),
                CallbackQueryHandler(handle_edit_departure_loc_callback, pattern=r"^edit_departure_loc:"),
                CallbackQueryHandler(handle_edit_departure_search, pattern=r"^edit_departure_search$")
            ],
            EDIT_ARRIVAL_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_arrival_text),
                CallbackQueryHandler(handle_edit_arrival_loc_callback, pattern=r"^edit_arrival_loc:"),
                CallbackQueryHandler(handle_edit_arrival_search, pattern=r"^edit_arrival_search$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(handle_trip_edit, pattern=r"^trip:edit:\d+$")
        ],
        per_message=False
    )
    
    # ConversationHandler pour l'édition de la date/heure avec calendrier
    edit_datetime_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_edit_field, pattern=r"^edit_field:departure_time:")
        ],
        states={
            EDIT_DATE_CALENDAR: [
                CallbackQueryHandler(handle_edit_calendar_navigation, pattern=r"^calendar:(prev|next|month):\d+:\d+$"),
                CallbackQueryHandler(handle_edit_day_selection, pattern=r"^calendar:day:\d+:\d+:\d+$")
            ],
            EDIT_TIME: [
                CallbackQueryHandler(handle_edit_time_selection, pattern=r"^time:\d+$"),  # Seulement l'heure
                CallbackQueryHandler(handle_edit_time_selection, pattern=r"^time:\d+:\d+$"),  # Heure et minutes (compatibilité)
                CallbackQueryHandler(handle_edit_time_selection, pattern=r"^flex_time:(morning|afternoon|evening|tbd)$")
            ],
            EDIT_MINUTE: [
                CallbackQueryHandler(handle_edit_minute_selection, pattern=r"^minute:\d+:\d+$")
            ],
            EDIT_CONFIRM_DATETIME: [
                CallbackQueryHandler(handle_edit_datetime_confirm, pattern=r"^edit_datetime:confirm$"),
                CallbackQueryHandler(handle_edit_datetime_confirm, pattern=r"^edit_datetime:cancel$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(handle_trip_edit, pattern=r"^trip:edit:\d+$")
        ],
        per_message=False
    )
    
    # Enregistrer les ConversationHandlers spécialisés EN PREMIER
    application.add_handler(edit_datetime_conv_handler)  # Pour departure_time
    application.add_handler(edit_location_conv_handler)  # Pour cities
    application.add_handler(edit_conv_handler)           # Pour seats_available (plus général)
    
    # Handlers pour la suppression
    application.add_handler(CallbackQueryHandler(handle_trip_delete, pattern=r"^trip:delete:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_trip_delete_confirm, pattern=r"^trip:delete_confirm:\d+$"))
    
    # Handlers pour le signalement
    application.add_handler(CallbackQueryHandler(handle_trip_report, pattern=r"^trip:report:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_copy_email, pattern=r"^copy_email:\d+$"))
    
    # Handler pour le menu des trajets
    application.add_handler(CallbackQueryHandler(list_my_trips_menu, pattern=r"^trips:menu$"))
    application.add_handler(CallbackQueryHandler(list_my_trips, pattern=r"^trips:list_driver$"))
    application.add_handler(CallbackQueryHandler(list_passenger_trips, pattern=r"^trips:list_passenger$"))
    
    # Handlers pour la gestion des trajets passagers
    application.add_handler(CallbackQueryHandler(show_passenger_trip_management, pattern=r"^passenger_trip_management$"))
    application.add_handler(CallbackQueryHandler(handle_passenger_trip_action, pattern=r"^(edit_passenger_trip|delete_passenger_trip|report_passenger_trip):\d+$"))
    application.add_handler(CallbackQueryHandler(confirm_delete_passenger_trip, pattern=r"^confirm_delete_passenger:\d+$"))
    
    # Handlers pour les groupes de trajets réguliers
    application.add_handler(CallbackQueryHandler(handle_regular_group_view, pattern=r"^regular_group:view:"))
    application.add_handler(CallbackQueryHandler(handle_regular_group_edit, pattern=r"^regular_group:edit:"))
    application.add_handler(CallbackQueryHandler(handle_regular_group_view_dates, pattern=r"^regular_group:view_dates:"))
    application.add_handler(CallbackQueryHandler(handle_regular_group_delete, pattern=r"^regular_group:delete:"))
    application.add_handler(CallbackQueryHandler(handle_regular_group_report, pattern=r"^regular_group:report:"))
    application.add_handler(CallbackQueryHandler(confirm_delete_regular_group, pattern=r"^confirm_delete_group:"))
    application.add_handler(CallbackQueryHandler(handle_trip_detail, pattern=r"^trip_detail:\d+$"))
    
    # Nouveaux handlers pour les boutons conducteur
    application.add_handler(CallbackQueryHandler(handle_driver_contact_passengers, pattern=r"^driver:contact_passengers:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_driver_set_meeting_point, pattern=r"^driver:set_meeting:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_driver_confirm_trip_completed, pattern=r"^driver:confirm_trip:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_driver_view_passengers, pattern=r"^driver:view_passengers:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_driver_trip_details, pattern=r"^driver:trip_details:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_confirm_trip_completed, pattern=r"^driver:confirm_completed:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_driver_message_passenger, pattern=r"^driver:message_passenger:\d+$"))
    
    logger.info("Handlers trip_handlers enregistrés avec succès")

async def handle_regular_group_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les détails d'un groupe de trajets réguliers"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le group_id du callback_data
    group_id = query.data.split(":")[-1]
    
    try:
        user_id = update.effective_user.id
        
        db = get_db()
        try:
            # Récupérer l'utilisateur
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await query.edit_message_text("❌ Utilisateur non trouvé.")
                return
            
            # Récupérer tous les trajets du groupe
            trips = db.query(Trip).filter(
                Trip.group_id == group_id,
                Trip.driver_id == user.id
            ).order_by(Trip.departure_time).all()
            
            if not trips:
                await query.edit_message_text("❌ Aucun trajet trouvé dans ce groupe.")
                return
            
            message = f"📅 **Détails du groupe de trajets réguliers**\n\n"
            message += f"🚗 **Trajet:** {trips[0].departure_city} → {trips[0].arrival_city}\n"
            message += f"💰 **Prix:** {format_swiss_price(trips[0].price_per_seat)}\n"
            message += f"👥 **Places disponibles:** {trips[0].seats_available}\n\n"
            message += f"📍 **Trajets individuels ({len(trips)}):**\n"
            
            for i, trip in enumerate(trips, 1):
                # Calculer les places restantes
                bookings = db.query(Booking).filter(
                    Booking.trip_id == trip.id,
                    Booking.status.in_(['confirmed', 'pending'])
                ).all()
                remaining_seats = trip.seats_available - len(bookings)
                
                departure_date = trip.departure_time.strftime("%d/%m/%Y")
                departure_time = trip.departure_time.strftime("%H:%M")
                
                status_icon = "✅" if remaining_seats > 0 else "❌"
                message += f"{status_icon} **{i}.** {departure_date} à {departure_time} ({remaining_seats} places)\n"
            
            # Boutons d'action
            keyboard = [
                [InlineKeyboardButton("🔧 Modifier le groupe", callback_data=f"regular_group:edit:{group_id}")],
                [InlineKeyboardButton("🔙 Retour à mes trajets", callback_data="trips:list_driver")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du groupe {group_id}: {e}")
        await query.edit_message_text("❌ Erreur lors de l'affichage des détails du groupe.")

async def handle_regular_group_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère l'édition d'un groupe de trajets réguliers"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le group_id du callback_data
    group_id = query.data.split(":")[-1]
    
    try:
        user_id = str(update.effective_user.id)
        
        db = get_db()
        try:
            # Vérifier que l'utilisateur possède des trajets dans ce groupe
            trip_count = db.query(Trip).filter(
                Trip.group_id == group_id,
                Trip.driver_id == int(user_id)
            ).count()
            
            if trip_count == 0:
                await query.edit_message_text("❌ Aucun trajet trouvé dans ce groupe.")
                return
            
            message = f"🔧 **Modifier le groupe de trajets réguliers**\n\n"
            message += f"Que souhaitez-vous faire avec ce groupe de {trip_count} trajets ?\n\n"
            message += "⚠️ **Attention:** Les modifications s'appliqueront à tous les trajets du groupe qui n'ont pas encore de réservations confirmées."
            
            # Boutons d'édition
            keyboard = [
                [InlineKeyboardButton("💰 Modifier le prix", callback_data=f"edit_group_price:{group_id}")],
                [InlineKeyboardButton("👥 Modifier les places", callback_data=f"edit_group_seats:{group_id}")],
                [InlineKeyboardButton("❌ Supprimer le groupe", callback_data=f"delete_group:{group_id}")],
                [InlineKeyboardButton("🔙 Retour aux détails", callback_data=f"regular_group:view:{group_id}")],
                [InlineKeyboardButton("🏠 Retour à mes trajets", callback_data="my_trips")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Erreur lors de l'édition du groupe {group_id}: {e}")
        await query.edit_message_text("❌ Erreur lors de l'accès aux options d'édition du groupe.")

async def handle_regular_group_view_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche la liste des dates pour un groupe de trajets réguliers"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le group_id du callback_data
    group_id = query.data.split(":")[-1]
    
    try:
        with SessionLocal() as db:
            # Récupérer tous les trajets du groupe, triés par date
            trips = db.query(Trip).filter(
                Trip.group_id == group_id,
                Trip.is_published == True,
                Trip.departure_time > datetime.now(),
                Trip.is_cancelled == False
            ).order_by(Trip.departure_time).all()
            
            if not trips:
                await query.edit_message_text("❌ Aucun trajet trouvé dans ce groupe.")
                return
            
            # Extraire les données pour éviter les erreurs de session
            trips_data = []
            for trip in trips:
                booking_count = db.query(Booking).filter(
                    Booking.trip_id == trip.id, 
                    Booking.status.in_(["pending", "confirmed"])
                ).count()
                
                trips_data.append({
                    'id': trip.id,
                    'departure_time': trip.departure_time,
                    'seats_available': trip.seats_available,
                    'booking_count': booking_count,
                    'departure_city': trip.departure_city,
                    'arrival_city': trip.arrival_city,
                    'price_per_seat': trip.price_per_seat
                })
        
        # Créer le message avec la liste des dates
        first_trip = trips_data[0]
        message = f"📍 {first_trip['departure_city']} → {first_trip['arrival_city']}\n"
        message += f"💰 {format_swiss_price(round_to_nearest_0_05(first_trip['price_per_seat']))}/place\n\n"
        message += f"📅 **Liste des dates** ({len(trips_data)} trajets):\n\n"
        
        # Créer les boutons pour chaque date (max 10 pour éviter les messages trop longs)
        keyboard = []
        max_trips_shown = 10
        
        for i, trip_data in enumerate(trips_data[:max_trips_shown]):
            date_str = trip_data['departure_time'].strftime("%d/%m/%Y à %H:%M")
            status_str = f"💺 {trip_data['booking_count']}/{trip_data['seats_available']}"
            
            button_text = f"📅 {date_str} - {status_str}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"trip_detail:{trip_data['id']}")])
        
        # Si il y a plus de 10 trajets, ajouter un message
        if len(trips_data) > max_trips_shown:
            message += f"*(Affichage des {max_trips_shown} premiers trajets)*\n\n"
        
        # Boutons de navigation
        keyboard.append([InlineKeyboardButton("🔙 Retour à mes trajets", callback_data="my_trips")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des dates du groupe {group_id}: {e}")
        await query.edit_message_text("❌ Erreur lors de l'affichage des dates du groupe.")

async def handle_trip_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche le détail d'un trajet individuel"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le trip_id du callback_data
    trip_id = query.data.split(":")[-1]
    
    try:
        with SessionLocal() as db:
            # Récupérer le trajet
            trip = db.query(Trip).filter(Trip.id == int(trip_id)).first()
            
            if not trip:
                await query.edit_message_text("❌ Trajet non trouvé.")
                return
            
            # Compter les réservations
            booking_count = db.query(Booking).filter(
                Booking.trip_id == trip.id, 
                Booking.status.in_(["pending", "confirmed"])
            ).count()
            
            # Extraire les données
            trip_data = {
                'id': trip.id,
                'departure_city': trip.departure_city,
                'arrival_city': trip.arrival_city,
                'departure_time': trip.departure_time,
                'seats_available': trip.seats_available,
                'price_per_seat': trip.price_per_seat,
                'booking_count': booking_count,
                'driver_id': trip.driver_id,
                'group_id': trip.group_id
            }
            
            # Vérifier si l'utilisateur est le conducteur
            user_id = update.effective_user.id
            is_driver = trip.driver_id == user_id
        
        # Créer le message de détail
        departure_date = trip_data['departure_time'].strftime("%d/%m/%Y à %H:%M")
        
        message = f"📍 {trip_data['departure_city']} → {trip_data['arrival_city']}\n"
        message += f"📅 {departure_date}\n"
        message += f"💰 {format_swiss_price(round_to_nearest_0_05(trip_data['price_per_seat']))}/place\n"
        message += f"💺 {trip_data['booking_count']}/{trip_data['seats_available']} réservations"
        
        # Créer les boutons d'action
        keyboard = []
        
        if is_driver:
            # Boutons pour le conducteur
            if trip_data['booking_count'] == 0:
                keyboard.append([InlineKeyboardButton("✏️ Modifier", callback_data=f"trip:edit:{trip_data['id']}")])
            keyboard.append([InlineKeyboardButton("🗑 Supprimer", callback_data=f"trip:delete:{trip_data['id']}")])
        else:
            # Boutons pour les passagers
            if trip_data['booking_count'] < trip_data['seats_available']:
                keyboard.append([InlineKeyboardButton("🎫 Réserver", callback_data=f"book_trip:{trip_data['id']}")])
        
        # Bouton de retour (retourner à la liste des dates si c'est un trajet régulier)
        if trip_data['group_id']:
            keyboard.append([InlineKeyboardButton("🔙 Retour aux dates", callback_data=f"regular_group:view_dates:{trip_data['group_id']}")])
        else:
            keyboard.append([InlineKeyboardButton("🔙 Retour à mes trajets", callback_data="my_trips")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du détail du trajet {trip_id}: {e}")
        await query.edit_message_text("❌ Erreur lors de l'affichage du détail du trajet.")

# ===== NOUVELLES FONCTIONS POUR LA GESTION DES TRAJETS PASSAGERS =====

async def handle_regular_group_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la suppression d'un groupe de trajets réguliers"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le group_id du callback_data
    group_id = query.data.split(":")[-1]
    
    try:
        with SessionLocal() as db:
            # Récupérer tous les trajets du groupe
            trips = db.query(Trip).filter(
                Trip.group_id == group_id,
                Trip.is_published == True,
                Trip.departure_time > datetime.now(),
                Trip.is_cancelled == False
            ).all()
            
            if not trips:
                await query.edit_message_text("❌ Aucun trajet trouvé dans ce groupe.")
                return
            
            first_trip = trips[0]
            trip_count = len(trips)
            
            # Demander confirmation
            message = (
                f"🗑️ **Supprimer le groupe de trajets réguliers**\n\n"
                f"📍 {first_trip.departure_city} → {first_trip.arrival_city}\n"
                f"📊 {trip_count} trajet{'s' if trip_count > 1 else ''} à supprimer\n\n"
                f"⚠️ **Cette action est définitive !**\n"
                f"Tous les trajets du groupe seront supprimés."
            )
            
            keyboard = [
                [InlineKeyboardButton("✅ Confirmer la suppression", callback_data=f"confirm_delete_group:{group_id}")],
                [InlineKeyboardButton("❌ Annuler", callback_data="menu:my_trips")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du groupe {group_id}: {e}")
        await query.edit_message_text("❌ Erreur lors de la suppression du groupe.")

async def handle_regular_group_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère le signalement d'un groupe de trajets réguliers"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le group_id du callback_data
    group_id = query.data.split(":")[-1]
    
    try:
        with SessionLocal() as db:
            # Récupérer le premier trajet du groupe pour les informations
            trip = db.query(Trip).filter(
                Trip.group_id == group_id,
                Trip.is_published == True,
                Trip.departure_time > datetime.now(),
                Trip.is_cancelled == False
            ).first()
            
            if not trip:
                await query.edit_message_text("❌ Aucun trajet trouvé dans ce groupe.")
                return
            
            # Compter les trajets dans le groupe
            trip_count = db.query(Trip).filter(
                Trip.group_id == group_id,
                Trip.is_published == True,
                Trip.departure_time > datetime.now(),
                Trip.is_cancelled == False
            ).count()
            
            trip_info = f"{trip.departure_city} → {trip.arrival_city} (Groupe de {trip_count} trajets)"
        
        user_id = update.effective_user.id
        logger.info(f"SIGNALEMENT GROUPE: Utilisateur {user_id} a demandé l'email pour signaler le groupe {group_id} ({trip_info})")
        
        message = (
            f"🚩 **Signaler un problème avec ce groupe de trajets**\n\n"
            f"📍 {trip_info}\n\n"
            f"📧 Pour signaler un problème avec ce groupe de trajets réguliers, "
            f"contactez-nous à :\n\n"
            f"**covoituragesuisse@gmail.com**\n\n"
            f"Merci d'inclure les détails du problème et ce groupe de trajets dans votre message."
        )
        
        keyboard = [
            [InlineKeyboardButton("📧 Ouvrir l'email", url="mailto:covoituragesuisse@gmail.com")],
            [InlineKeyboardButton("🔙 Retour à mes trajets", callback_data="menu:my_trips")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du signalement du groupe {group_id}: {e}")
        await query.edit_message_text("❌ Erreur lors du signalement du groupe.")

async def confirm_delete_regular_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirme et exécute la suppression d'un groupe de trajets réguliers"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le group_id du callback_data
    group_id = query.data.split(":")[-1]
    
    try:
        with SessionLocal() as db:
            # Récupérer tous les trajets du groupe
            trips = db.query(Trip).filter(
                Trip.group_id == group_id,
                Trip.is_published == True,
                Trip.departure_time > datetime.now(),
                Trip.is_cancelled == False
            ).all()
            
            if not trips:
                await query.edit_message_text("❌ Aucun trajet trouvé dans ce groupe.")
                return
            
            first_trip = trips[0]
            trip_count = len(trips)
            trip_info = f"{first_trip.departure_city} → {first_trip.arrival_city}"
            
            # Vérifier s'il y a des réservations
            total_bookings = 0
            for trip in trips:
                booking_count = db.query(Booking).filter(
                    Booking.trip_id == trip.id,
                    Booking.status.in_(["pending", "confirmed"])
                ).count()
                total_bookings += booking_count
            
            if total_bookings > 0:
                await query.edit_message_text(
                    f"❌ **Impossible de supprimer ce groupe**\n\n"
                    f"📍 {trip_info}\n"
                    f"💺 {total_bookings} réservation{'s' if total_bookings > 1 else ''} active{'s' if total_bookings > 1 else ''}\n\n"
                    f"Vous devez d'abord annuler toutes les réservations.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Retour à mes trajets", callback_data="menu:my_trips")]
                    ]),
                    parse_mode="Markdown"
                )
                return
            
            # Supprimer tous les trajets du groupe
            deleted_count = 0
            for trip in trips:
                db.delete(trip)
                deleted_count += 1
            
            db.commit()
            
            logger.info(f"SUPPRESSION GROUPE: {deleted_count} trajets supprimés du groupe {group_id} par l'utilisateur {update.effective_user.id}")
            
            await query.edit_message_text(
                f"✅ **Groupe supprimé avec succès**\n\n"
                f"📍 {trip_info}\n"
                f"🗑️ {deleted_count} trajet{'s' if deleted_count > 1 else ''} supprimé{'s' if deleted_count > 1 else ''}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Retour à mes trajets", callback_data="menu:my_trips")]
                ]),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la suppression confirmée du groupe {group_id}: {e}")
        await query.edit_message_text("❌ Erreur lors de la suppression du groupe.")

# ===== NOUVELLES FONCTIONS POUR LA GESTION DES TRAJETS PASSAGERS =====

async def show_passenger_trip_management(update: Update, context: CallbackContext):
    """Affiche l'interface de gestion des trajets passagers avec toutes les options"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await query.edit_message_text("⚠️ Utilisateur non trouvé.")
            return ConversationHandler.END
        
        # Récupérer les trajets passagers (demandes)
        passenger_trips = db.query(Trip).filter(
            Trip.creator_id == user.id,
            Trip.trip_role == "passenger"
        ).order_by(Trip.departure_time.desc()).all()
        
        if not passenger_trips:
            message = (
                "🎒 *Mes Trajets Passager*\n\n"
                "❌ Aucune demande de trajet créée.\n\n"
                "💡 Créez votre première demande de trajet !"
            )
            keyboard = [
                [InlineKeyboardButton("➕ Créer une demande", callback_data="menu:create")],
                [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
            ]
        else:
            message = "🎒 *Mes Trajets Passager*\n\n"
            keyboard = []
            
            for trip in passenger_trips[:5]:  # Limiter à 5 trajets
                status_emoji = "🟢" if not getattr(trip, 'is_cancelled', False) else "🔴"
                trip_text = f"{status_emoji} {trip.departure_city} → {trip.arrival_city}"
                if hasattr(trip, 'departure_time'):
                    trip_text += f"\n📅 {trip.departure_time.strftime('%d/%m à %H:%M')}"
                
                message += f"\n{trip_text}\n"
                
                # Boutons pour chaque trajet
                trip_keyboard = [
                    InlineKeyboardButton("✏️ Modifier", callback_data=f"edit_passenger_trip:{trip.id}"),
                    InlineKeyboardButton("🗑️ Supprimer", callback_data=f"delete_passenger_trip:{trip.id}"),
                    InlineKeyboardButton("🚨 Signaler", callback_data=f"report_passenger_trip:{trip.id}")
                ]
                keyboard.append(trip_keyboard)
            
            # Boutons généraux
            keyboard.extend([
                [InlineKeyboardButton("➕ Nouvelle demande", callback_data="menu:create")],
                [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
            ])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Erreur dans show_passenger_trip_management: {e}")
        await query.edit_message_text(
            "⚠️ Erreur lors de l'affichage des trajets passagers.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Retour", callback_data="profile:back_to_profile")
            ]])
        )
        return ConversationHandler.END

async def handle_passenger_trip_action(update: Update, context: CallbackContext):
    """Gère les actions sur les trajets passagers (edit/delete/report)"""
    query = update.callback_query
    await query.answer()
    
    action_data = query.data
    action, trip_id = action_data.split(":")
    trip_id = int(trip_id)
    
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        await query.edit_message_text("❌ Trajet non trouvé.")
        return ConversationHandler.END
    
    if action == "edit_passenger_trip":
        # Rediriger vers l'édition de trajet passager
        keyboard = [
            [InlineKeyboardButton("📍 Modifier départ", callback_data=f"edit_trip_departure:{trip_id}")],
            [InlineKeyboardButton("🎯 Modifier arrivée", callback_data=f"edit_trip_arrival:{trip_id}")],
            [InlineKeyboardButton("📅 Modifier date/heure", callback_data=f"edit_trip_datetime:{trip_id}")],
            [InlineKeyboardButton("👥 Modifier nb passagers", callback_data=f"edit_trip_passengers:{trip_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="passenger_trip_management")]
        ]
        
        await query.edit_message_text(
            f"✏️ *Modifier le trajet passager*\n\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Que souhaitez-vous modifier ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif action == "delete_passenger_trip":
        # Demander confirmation de suppression
        keyboard = [
            [InlineKeyboardButton("❌ Confirmer suppression", callback_data=f"confirm_delete_passenger:{trip_id}")],
            [InlineKeyboardButton("⬅️ Annuler", callback_data="passenger_trip_management")]
        ]
        
        await query.edit_message_text(
            f"🗑️ *Supprimer le trajet passager*\n\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"⚠️ **Attention !** Cette action est irréversible.\n\n"
            f"Voulez-vous vraiment supprimer cette demande de trajet ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif action == "report_passenger_trip":
        # Interface de signalement
        keyboard = [
            [InlineKeyboardButton("🚨 Problème de sécurité", callback_data=f"report_safety:{trip_id}")],
            [InlineKeyboardButton("💰 Problème de paiement", callback_data=f"report_payment:{trip_id}")],
            [InlineKeyboardButton("📞 Problème de contact", callback_data=f"report_contact:{trip_id}")],
            [InlineKeyboardButton("❓ Autre problème", callback_data=f"report_other:{trip_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="passenger_trip_management")]
        ]
        
        await query.edit_message_text(
            f"🚨 *Signaler un problème*\n\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\n\n"
            f"Quel type de problème souhaitez-vous signaler ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    return ConversationHandler.END

async def confirm_delete_passenger_trip(update: Update, context: CallbackContext):
    """Confirme et supprime le trajet passager"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[-1])
    
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        await query.edit_message_text("❌ Trajet non trouvé.")
        return ConversationHandler.END
    
    try:
        # Supprimer le trajet
        db.delete(trip)
        db.commit()
        
        await query.edit_message_text(
            "✅ *Trajet passager supprimé*\n\n"
            "Votre demande de trajet a été supprimée avec succès.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Retour à mes trajets", callback_data="passenger_trip_management")]
            ]),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du trajet passager {trip_id}: {e}")
        await query.edit_message_text(
            "❌ Erreur lors de la suppression du trajet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Retour", callback_data="passenger_trip_management")]
            ])
        )
    
    return ConversationHandler.END

# ================================
# HANDLERS POUR BOUTONS CONDUCTEUR
# ================================

async def handle_driver_contact_passengers(update: Update, context: CallbackContext):
    """Handler pour contacter les passagers d'un trajet"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[-1])
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id, Trip.driver_id == user_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé.")
            return
        
        # Récupérer les passagers confirmés
        from database.models import Booking
        bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.status == 'confirmed'
        ).all()
        
        if not bookings:
            await query.edit_message_text(
                "📭 *Aucun passager confirmé*\n\n"
                "Ce trajet n'a pas encore de passagers confirmés.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # Afficher la liste des passagers avec bouton message individuel
        message_text = f"💬 *Contacter les passagers*\n\n"
        message_text += f"📍 **{trip.departure_city}** → **{trip.arrival_city}**\n"
        message_text += f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
        message_text += f"👥 **{len(bookings)} passager(s) confirmé(s):**\n\n"
        
        keyboard = []
        for booking in bookings:
            passenger = db.query(User).filter(User.telegram_id == booking.passenger_id).first()
            if passenger:
                passenger_name = passenger.first_name or "Passager"
                message_text += f"• {passenger_name}\n"
                keyboard.append([
                    InlineKeyboardButton(
                        f"💬 Envoyer un message à {passenger_name}", 
                        callback_data=f"driver:message_passenger:{booking.id}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver")])
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur handle_driver_contact_passengers: {e}")
        await query.edit_message_text("❌ Erreur lors de l'affichage des passagers.")

async def handle_driver_set_meeting_point(update: Update, context: CallbackContext):
    """Handler pour définir un point de rendez-vous"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[-1])
    
    await query.edit_message_text(
        "📍 *Définir le point de rendez-vous*\n\n"
        "Envoyez-moi l'adresse ou la description du point de rendez-vous pour ce trajet.\n\n"
        "💡 *Exemple:* \"Gare de Lausanne, quai 3\" ou \"Place de la Palud, fontaine\"",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Annuler", callback_data="trips:show_driver")]
        ]),
        parse_mode="Markdown"
    )
    
    # Stocker l'ID du trajet pour la prochaine étape
    context.user_data['setting_meeting_point_for_trip'] = trip_id

async def handle_driver_confirm_trip_completed(update: Update, context: CallbackContext):
    """Handler pour confirmer que le trajet a été effectué"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[-1])
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id, Trip.driver_id == user_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé.")
            return
        
        # Vérifier s'il y a des passagers confirmés
        from database.models import Booking
        confirmed_bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.status == 'confirmed'
        ).count()
        
        if confirmed_bookings == 0:
            await query.edit_message_text(
                "⚠️ *Aucun passager confirmé*\n\n"
                "Vous ne pouvez confirmer un trajet que s'il y a des passagers confirmés.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # Demander confirmation
        message_text = (
            f"✅ *Confirmer trajet effectué*\n\n"
            f"📍 **{trip.departure_city}** → **{trip.arrival_city}**\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"👥 {confirmed_bookings} passager(s) confirmé(s)\n\n"
            f"⚠️ **Êtes-vous sûr que ce trajet a été effectué ?**\n"
            f"Cette action déclenchera les paiements aux conducteurs et ne peut pas être annulée."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Oui, confirmer", callback_data=f"driver:confirm_completed:{trip_id}"),
                InlineKeyboardButton("❌ Non, annuler", callback_data="trips:show_driver")
            ]
        ]
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur handle_driver_confirm_trip_completed: {e}")
        await query.edit_message_text("❌ Erreur lors de la confirmation du trajet.")

async def handle_driver_view_passengers(update: Update, context: CallbackContext):
    """Handler pour voir tous les passagers du trajet"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[-1])
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id, Trip.driver_id == user_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé.")
            return
        
        # Récupérer toutes les réservations
        from database.models import Booking
        bookings = db.query(Booking).filter(Booking.trip_id == trip_id).all()
        
        if not bookings:
            await query.edit_message_text(
                "👥 *Aucune réservation*\n\n"
                "Ce trajet n'a pas encore de réservations.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # Construire le message avec tous les passagers
        message_text = f"👥 *Passagers du trajet*\n\n"
        message_text += f"📍 **{trip.departure_city}** → **{trip.arrival_city}**\n"
        message_text += f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
        message_text += f"💰 {format_swiss_price(trip.price_per_seat)}/place\n\n"
        
        confirmed_count = 0
        pending_count = 0
        
        for booking in bookings:
            passenger = db.query(User).filter(User.telegram_id == booking.passenger_id).first()
            passenger_name = passenger.first_name if passenger else "Passager"
            
            status_emoji = "✅" if booking.status == 'confirmed' else "⏳"
            status_text = "Confirmé" if booking.status == 'confirmed' else "En attente"
            
            message_text += f"{status_emoji} **{passenger_name}** - {status_text}\n"
            
            if booking.status == 'confirmed':
                confirmed_count += 1
            else:
                pending_count += 1
        
        message_text += f"\n📊 **Résumé:**\n"
        message_text += f"✅ {confirmed_count} confirmé(s)\n"
        message_text += f"⏳ {pending_count} en attente\n"
        message_text += f"💺 {trip.seats_available - len(bookings)} place(s) libre(s)"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver")]
        ]
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur handle_driver_view_passengers: {e}")
        await query.edit_message_text("❌ Erreur lors de l'affichage des passagers.")

async def handle_driver_trip_details(update: Update, context: CallbackContext):
    """Handler pour afficher les détails complets du trajet"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[-1])
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id, Trip.driver_id == user_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé.")
            return
        
        # Récupérer les statistiques
        from database.models import Booking
        total_bookings = db.query(Booking).filter(Booking.trip_id == trip_id).count()
        confirmed_bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.status == 'confirmed'
        ).count()
        
        # Construire le message détaillé
        message_text = f"ℹ️ *Détails du trajet*\n\n"
        message_text += f"🆔 **ID:** {trip.id}\n"
        message_text += f"📍 **Départ:** {trip.departure_city}\n"
        message_text += f"📍 **Arrivée:** {trip.arrival_city}\n"
        message_text += f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
        message_text += f"💰 **Prix:** {format_swiss_price(trip.price_per_seat)}/place\n"
        message_text += f"💺 **Places:** {trip.seats_available}\n\n"
        
        if hasattr(trip, 'description') and trip.description:
            message_text += f"📝 **Description:** {trip.description}\n\n"
        
        message_text += f"📊 **Réservations:**\n"
        message_text += f"✅ {confirmed_bookings} confirmée(s)\n"
        message_text += f"📋 {total_bookings} total\n"
        message_text += f"💺 {trip.seats_available - total_bookings} libre(s)\n\n"
        
        # Revenus estimés
        estimated_revenue = confirmed_bookings * trip.price_per_seat * 0.88  # 88% pour le conducteur
        message_text += f"💰 **Revenus estimés:** {format_swiss_price(estimated_revenue)}\n"
        message_text += f"📅 **Créé le:** {trip.created_at.strftime('%d/%m/%Y')}"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Retour", callback_data="trips:show_driver")]
        ]
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur handle_driver_trip_details: {e}")
        await query.edit_message_text("❌ Erreur lors de l'affichage des détails.")

async def handle_confirm_trip_completed(update: Update, context: CallbackContext):
    """Confirme définitivement que le trajet a été effectué"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[-1])
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id, Trip.driver_id == user_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé.")
            return
        
        # Marquer le trajet comme terminé
        trip.status = 'completed'
        trip.completed_at = datetime.now()
        db.commit()
        
        # Récupérer les réservations confirmées pour déclencher les paiements
        from database.models import Booking
        confirmed_bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.status == 'confirmed'
        ).all()
        
        # TODO: Déclencher les paiements aux conducteurs ici
        # for booking in confirmed_bookings:
        #     trigger_driver_payment(booking)
        
        await query.edit_message_text(
            f"✅ *Trajet confirmé comme effectué !*\n\n"
            f"📍 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"🎉 Merci d'avoir utilisé notre service !\n"
            f"💰 Les paiements vont être traités automatiquement.\n\n"
            f"⭐ N'hésitez pas à évaluer vos passagers !",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour à mes trajets", callback_data="trips:show_driver")]
            ]),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur handle_confirm_trip_completed: {e}")
        await query.edit_message_text("❌ Erreur lors de la confirmation du trajet.")

async def handle_driver_message_passenger(update: Update, context: CallbackContext):
    """Handler pour envoyer un message à un passager spécifique"""
    query = update.callback_query
    await query.answer()
    
    booking_id = int(query.data.split(":")[-1])
    
    try:
        db = get_db()
        from database.models import Booking
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking:
            await query.edit_message_text("❌ Réservation non trouvée.")
            return
        
        # Récupérer les infos du passager et du trajet
        passenger = db.query(User).filter(User.telegram_id == booking.passenger_id).first()
        trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
        
        if not passenger or not trip:
            await query.edit_message_text("❌ Informations introuvables.")
            return
        
        passenger_name = passenger.first_name or "Passager"
        
        await query.edit_message_text(
            f"💬 *Envoyer un message à {passenger_name}*\n\n"
            f"📍 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"✍️ **Tapez votre message ci-dessous:**\n"
            f"Il sera envoyé directement à {passenger_name}.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Annuler", callback_data=f"driver:contact_passengers:{trip.id}")]
            ]),
            parse_mode="Markdown"
        )
        
        # Stocker les infos pour le prochain message
        context.user_data['messaging_passenger'] = {
            'booking_id': booking_id,
            'passenger_id': booking.passenger_id,
            'passenger_name': passenger_name,
            'trip_id': trip.id
        }
        
    except Exception as e:
        logger.error(f"Erreur handle_driver_message_passenger: {e}")
        await query.edit_message_text("❌ Erreur lors de l'envoi du message.")
