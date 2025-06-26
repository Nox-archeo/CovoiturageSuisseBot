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
from telegram.constants import ParseMode
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

# --- ETAPES DU FORMULAIRE DE MODIFICATION ---
(EDIT_DEPARTURE, EDIT_ARRIVAL, EDIT_DATE, EDIT_TIME, EDIT_PRICE, EDIT_SEATS, EDIT_CONFIRM) = range(100, 107)

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

async def list_my_trips(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    db = get_db()
    blocks = []
    driver_trips = db.query(Trip).join(User, Trip.driver_id == User.id).filter(User.telegram_id == user_id, Trip.is_cancelled == False).order_by(Trip.departure_time.asc()).all()
    if driver_trips:
        blocks.append("🚗 *Mes trajets à venir :*\n")
        for trip in driver_trips:
            # Exclure les trajets annulés de l'affichage normal (sécurité)
            if getattr(trip, 'is_cancelled', False):
                continue
            trip_str = (
                f"• {trip.departure_city} → {trip.arrival_city}\n"
                f"  📅 {trip.departure_time.strftime('%d/%m/%Y %H:%M')}\n"
                f"  💰 {trip.price_per_seat:.2f} CHF/place"
            )
            row_btns = []
            booking_count = db.query(Booking).filter(Booking.trip_id == trip.id, Booking.status.in_(["pending", "confirmed"])) .count()
            if booking_count == 0:
                row_btns.append(InlineKeyboardButton("✏️ Modifier", callback_data=f"trip:edit:{trip.id}"))
            row_btns.append(InlineKeyboardButton("❌ Annuler", callback_data=f"trip:cancel:{trip.id}"))
            blocks.append({'text': trip_str, 'buttons': row_btns})
    else:
        blocks.append("Aucun trajet à venir.")
    # Affichage
    text = "\n\n".join([b['text'] if isinstance(b, dict) else b for b in blocks])
    reply_markup_rows = [b['buttons'] for b in blocks if isinstance(b, dict) and b['buttons']]
    reply_markup_rows.append([InlineKeyboardButton("➕ Créer un trajet", callback_data="menu:create")])
    reply_markup_rows.append([InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")])
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(reply_markup_rows),
        parse_mode="Markdown"
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
    query = update.callback_query
    user_id = update.effective_user.id
    db = get_db()
    blocks = []
    if trip_role == "driver":
        driver_trips = db.query(Trip).join(User, Trip.driver_id == User.id).filter(User.telegram_id == user_id, Trip.is_cancelled != True).order_by(Trip.departure_time.asc()).all()
        if driver_trips:
            blocks.append("🚗 *Mes trajets à venir :*\n")
            for trip in driver_trips:
                booking_count = db.query(Booking).filter(Booking.trip_id == trip.id, Booking.status.in_(["pending", "confirmed"])) .count()
                trip_str = (
                    f"• {trip.departure_city} → {trip.arrival_city}\n"
                    f"  📅 {trip.departure_time.strftime('%d/%m/%Y %H:%M')}\n"
                    f"  💰 {trip.price_per_seat:.2f} CHF/place"
                )
                # Générer les boutons pour ce trajet
                row_btns = []
                if booking_count == 0:
                    row_btns.append(InlineKeyboardButton("✏️ Modifier", callback_data=f"trip:edit:{trip.id}"))
                row_btns.append(InlineKeyboardButton("❌ Annuler", callback_data=f"trip:cancel:{trip.id}"))
                # Afficher le bloc message + boutons pour ce trajet
                blocks.append({'text': trip_str, 'buttons': row_btns})
        else:
            blocks.append("Vous n'avez aucun trajet à venir en tant que conducteur.")
    elif trip_role == "passenger":
        passenger_bookings = db.query(Booking).join(User).filter(User.telegram_id == user_id).all()
        if passenger_bookings:
            blocks.append("*En tant que passager (réservations) :*")
            for booking in passenger_bookings:
                trip = booking.trip
                blocks.append(f"• {trip.departure_city} → {trip.arrival_city} le {trip.departure_time.strftime('%d/%m/%Y %H:%M')} (Conducteur: {trip.driver.first_name if trip.driver else 'N/A'})")
        else:
            blocks.append("Vous n'avez aucune réservation en tant que passager.")

    # Construction du message et des claviers
    if trip_role == "driver" and any(isinstance(b, dict) for b in blocks):
        # On a des trajets à afficher avec boutons
        text = blocks[0]  # Titre
        reply_markup_rows = []
        for b in blocks[1:]:
            if isinstance(b, dict):
                text += f"\n\n{b['text']}"
                reply_markup_rows.append(b['buttons'])
            else:
                text += f"\n{b}"
        # Ajout des boutons globaux
        reply_markup_rows.append([InlineKeyboardButton("⬅️ Retour à Mes Trajets", callback_data="menu:my_trips")])
        reply_markup_rows.append([InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")])
        if query:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(reply_markup_rows), parse_mode="Markdown")
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(reply_markup_rows), parse_mode="Markdown")
    else:
        # Aucun trajet conducteur, ou passager
        final_message = "\n".join([b for b in blocks if isinstance(b, str)])
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Retour à Mes Trajets", callback_data="menu:my_trips")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]
        ])
        if query:
            await query.edit_message_text(final_message, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(final_message, reply_markup=reply_markup, parse_mode="Markdown")
# --- Handler Annulation ---
async def handle_cancel_trip_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    db = get_db()
    try:
        trip_id = int(query.data.split(":")[2])
        # Affichage de la confirmation si ce n'est pas un callback de confirmation/annulation
        keyboard = [
            [
                InlineKeyboardButton("✅ Oui, annuler", callback_data=f"confirm_cancel_trip:{trip_id}"),
                InlineKeyboardButton("❌ Non, revenir", callback_data=f"cancel_cancel_trip:{trip_id}")
            ]
        ]
        await query.edit_message_text(
            "⚠️ Es-tu sûr de vouloir annuler ce trajet ?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Erreur lors de la préparation de la confirmation d'annulation: {e}\n{traceback.format_exc()}")
        await query.answer("Erreur lors de l'annulation.", show_alert=True)

# Nouveau handler pour la confirmation explicite
async def handle_confirm_cancel_trip(update: Update, context: CallbackContext):
    query = update.callback_query
    db = get_db()
    try:
        trip_id = int(query.data.split(":")[1])
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            await query.answer("Trajet introuvable.", show_alert=True)
            return
        if not hasattr(trip, "is_cancelled"):
            trip.is_cancelled = False
        if trip.is_cancelled:
            await query.answer("Ce trajet est déjà annulé.", show_alert=True)
            return
        trip.is_cancelled = True
        db.commit()  # Enregistre la modification pour la persistance
        # Notifier les passagers
        bookings = db.query(Booking).filter(Booking.trip_id == trip_id, Booking.status.in_(["pending", "confirmed"]))
        for booking in bookings:
            passenger = db.query(User).filter(User.id == booking.passenger_id).first()
            if passenger:
                try:
                    await context.bot.send_message(passenger.telegram_id, f"❌ Le trajet {trip.departure_city} → {trip.arrival_city} du {trip.departure_time.strftime('%d/%m/%Y %H:%M')} a été annulé par le conducteur.")
                except Exception as e:
                    logger.warning(f"Impossible de notifier le passager {passenger.telegram_id}: {e}")
        await query.edit_message_text("🚫 Ce trajet a été annulé.")
    except Exception as e:
        logger.error(f"Erreur lors de la confirmation d'annulation du trajet: {e}\n{traceback.format_exc()}")
        await query.answer("Erreur lors de l'annulation.", show_alert=True)

# Nouveau handler pour l'annulation de l'annulation
async def handle_cancel_cancel_trip(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.edit_message_text("Annulation annulée. Le trajet n'a pas été annulé.")

# --- Handler Edition ---
async def handle_edit_trip_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    db = get_db()
    try:
        trip_id = int(query.data.split(":")[2])
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            await query.answer("Trajet introuvable.", show_alert=True)
            return ConversationHandler.END
        booking_count = db.query(Booking).filter(Booking.trip_id == trip_id, Booking.status.in_(["pending", "confirmed"])) .count()
        if booking_count > 0:
            await query.answer("Impossible de modifier un trajet avec des réservations.", show_alert=True)
            return ConversationHandler.END
        # Stocker l'ID du trajet à modifier
        context.user_data['edit_trip_id'] = trip_id
        context.user_data['edit_trip'] = trip
        # Pré-remplir les champs
        context.user_data['edit_departure_city'] = trip.departure_city
        context.user_data['edit_arrival_city'] = trip.arrival_city
        context.user_data['edit_date'] = trip.departure_time.strftime('%Y-%m-%d')
        context.user_data['edit_time'] = trip.departure_time.strftime('%H:%M')
        context.user_data['edit_price'] = str(trip.price_per_seat)
        context.user_data['edit_seats'] = str(trip.seats_available)
        await query.edit_message_text(f"✏️ Modification du trajet\n\nVille de départ actuelle : {trip.departure_city}\n\nVeuillez entrer la nouvelle ville de départ :", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Annuler", callback_data="edit_trip:cancel")]]))
        return EDIT_DEPARTURE
    except Exception as e:
        logger.error(f"Erreur lors de la modification du trajet: {e}\n{traceback.format_exc()}")
        await query.answer("Erreur lors de la modification.", show_alert=True)
        return ConversationHandler.END

# --- Formulaire étape par étape ---
async def edit_trip_departure(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    context.user_data['edit_departure_city'] = text
    await update.message.reply_text(f"Ville d'arrivée actuelle : {context.user_data['edit_arrival_city']}\n\nVeuillez entrer la nouvelle ville d'arrivée :", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Annuler", callback_data="edit_trip:cancel")]]))
    return EDIT_ARRIVAL

async def edit_trip_arrival(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    context.user_data['edit_arrival_city'] = text
    await update.message.reply_text(f"Date actuelle : {context.user_data['edit_date']}\n\nVeuillez entrer la nouvelle date (AAAA-MM-JJ) :", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Annuler", callback_data="edit_trip:cancel")]]))
    return EDIT_DATE

async def edit_trip_date(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    try:
        datetime.strptime(text, '%Y-%m-%d')
        context.user_data['edit_date'] = text
        await update.message.reply_text(f"Heure actuelle : {context.user_data['edit_time']}\n\nVeuillez entrer la nouvelle heure (HH:MM, 24h) :", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Annuler", callback_data="edit_trip:cancel")]]))
        return EDIT_TIME
    except ValueError:
        await update.message.reply_text("Format de date invalide. Veuillez entrer la date au format AAAA-MM-JJ :")
        return EDIT_DATE

async def edit_trip_time(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    try:
        datetime.strptime(text, '%H:%M')
        context.user_data['edit_time'] = text
        await update.message.reply_text(f"Prix actuel : {context.user_data['edit_price']} CHF\n\nVeuillez entrer le nouveau prix par place (CHF) :", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Annuler", callback_data="edit_trip:cancel")]]))
        return EDIT_PRICE
    except ValueError:
        await update.message.reply_text("Format d'heure invalide. Veuillez entrer l'heure au format HH:MM (24h) :")
        return EDIT_TIME

async def edit_trip_price(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    try:
        price = float(text)
        if price < 0:
            raise ValueError
        context.user_data['edit_price'] = text
        await update.message.reply_text(f"Nombre de places actuel : {context.user_data['edit_seats']}\n\nVeuillez entrer le nouveau nombre de places disponibles :", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Annuler", callback_data="edit_trip:cancel")]]))
        return EDIT_SEATS
    except ValueError:
        await update.message.reply_text("Prix invalide. Veuillez entrer un nombre positif :")
        return EDIT_PRICE

async def edit_trip_seats(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    try:
        seats = int(text)
        if seats < 1:
            raise ValueError
        context.user_data['edit_seats'] = text
        # Récapitulatif
        recap = (
            f"Merci ! Voici le récapitulatif :\n\n"
            f"Départ : {context.user_data['edit_departure_city']}\n"
            f"Arrivée : {context.user_data['edit_arrival_city']}\n"
            f"Date : {context.user_data['edit_date']}\n"
            f"Heure : {context.user_data['edit_time']}\n"
            f"Prix : {context.user_data['edit_price']} CHF\n"
            f"Places : {context.user_data['edit_seats']}"
        )
        await update.message.reply_text(recap, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirmer", callback_data="edit_trip:confirm")],
            [InlineKeyboardButton("Annuler", callback_data="edit_trip:cancel")]
        ]))
        return EDIT_CONFIRM
    except ValueError:
        await update.message.reply_text("Nombre de places invalide. Veuillez entrer un entier positif :")
        return EDIT_SEATS

async def edit_trip_confirm(update: Update, context: CallbackContext):
    query = update.callback_query
    db = get_db()
    try:
        trip_id = context.user_data.get('edit_trip_id')
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            await query.answer("Trajet introuvable.", show_alert=True)
            return ConversationHandler.END
        # Appliquer les modifications
        trip.departure_city = context.user_data['edit_departure_city']
        trip.arrival_city = context.user_data['edit_arrival_city']
        dt_str = context.user_data['edit_date'] + ' ' + context.user_data['edit_time']
        trip.departure_time = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
        trip.price_per_seat = float(context.user_data['edit_price'])
        trip.seats_available = int(context.user_data['edit_seats'])
        db.commit()
        await query.edit_message_text("✅ Trajet modifié avec succès !")
    except Exception as e:
        logger.error(f"Erreur lors de la confirmation de modification: {e}\n{traceback.format_exc()}")
        await query.answer("Erreur lors de la modification.", show_alert=True)
    return ConversationHandler.END

async def edit_trip_cancel(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.edit_message_text("Modification annulée.")
    return ConversationHandler.END

# --- Ajout du ConversationHandler pour l'édition ---
edit_trip_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_edit_trip_callback, pattern=r"^trip:edit:\d+$")],
    states={
        EDIT_DEPARTURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_trip_departure), CallbackQueryHandler(edit_trip_cancel, pattern="^edit_trip:cancel$")],
        EDIT_ARRIVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_trip_arrival), CallbackQueryHandler(edit_trip_cancel, pattern="^edit_trip:cancel$")],
        EDIT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_trip_date), CallbackQueryHandler(edit_trip_cancel, pattern="^edit_trip:cancel$")],
        EDIT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_trip_time), CallbackQueryHandler(edit_trip_cancel, pattern="^edit_trip:cancel$")],
        EDIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_trip_price), CallbackQueryHandler(edit_trip_cancel, pattern="^edit_trip:cancel$")],
        EDIT_SEATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_trip_seats), CallbackQueryHandler(edit_trip_cancel, pattern="^edit_trip:cancel$")],
        EDIT_CONFIRM: [CallbackQueryHandler(edit_trip_confirm, pattern="^edit_trip:confirm$"), CallbackQueryHandler(edit_trip_cancel, pattern="^edit_trip:cancel$")],
    },
    fallbacks=[CallbackQueryHandler(edit_trip_cancel, pattern="^edit_trip:cancel$")],
    name="edit_trip_conversation",
    persistent=False,
    allow_reentry=True
)

def register(application):
    # Handler pour "Mes trajets" button in main menu
    application.add_handler(CallbackQueryHandler(list_my_trips_menu, pattern="^menu:my_trips$"))
    # Suppression du handler handle_trip_list_choice (plus utilisé)
    application.add_handler(edit_trip_conv_handler)
    application.add_handler(CallbackQueryHandler(handle_cancel_trip_callback, pattern=r"^trip:cancel:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_confirm_cancel_trip, pattern=r"^confirm_cancel_trip:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_cancel_cancel_trip, pattern=r"^cancel_cancel_trip:\d+$"))
    logger.info("Trip (viewing/management) handlers registered.")

# ... (rest of trip_handlers.py, ensure SWISS_CITIES and load_cities are used if needed by other functions here)
# The states like CHOOSING_TYPE, DEPARTURE etc. should be removed if not used by a ConversationHandler in this file.
# If search_trip is still relevant here and not fully in search_trip_handler, it needs proper integration.
