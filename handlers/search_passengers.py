#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Handler pour la recherche de trajets de passagers par les conducteurs.
Permet aux conducteurs de rechercher des demandes de trajets de passagers.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CallbackContext,
    filters
)
from database import get_db
from database.models import Trip, User
from utils.date_picker import create_date_buttons, format_date_display

logger = logging.getLogger(__name__)

# États de conversation
(
    CANTON_SELECTION,
    DATE_SELECTION,
    SHOWING_RESULTS,
    CONTACT_PASSENGER
) = range(4)

# Mapping des cantons suisses
CANTONS = {
    'VD': {'name': 'Vaud', 'emoji': '🏔️'},
    'FR': {'name': 'Fribourg', 'emoji': '🌄'},
    'GE': {'name': 'Genève', 'emoji': '🏛️'},
    'VS': {'name': 'Valais', 'emoji': '⛰️'},
    'NE': {'name': 'Neuchâtel', 'emoji': '🌊'},
    'JU': {'name': 'Jura', 'emoji': '🌲'},
    'BE': {'name': 'Berne', 'emoji': '🐻'},
    'ZH': {'name': 'Zurich', 'emoji': '🏙️'},
    'AG': {'name': 'Argovie', 'emoji': '🌾'},
    'LU': {'name': 'Lucerne', 'emoji': '🌅'},
    'BL': {'name': 'Bâle-Campagne', 'emoji': '🏘️'},
    'BS': {'name': 'Bâle-Ville', 'emoji': '🏢'},
    'SO': {'name': 'Soleure', 'emoji': '🏰'},
    'SG': {'name': 'Saint-Gall', 'emoji': '🏞️'},
    'GR': {'name': 'Grisons', 'emoji': '🗻'},
    'TI': {'name': 'Tessin', 'emoji': '🌴'},
    'AI': {'name': 'Appenzell Rh.-Int.', 'emoji': '🚠'},
    'AR': {'name': 'Appenzell Rh.-Ext.', 'emoji': '🚠'},
    'GL': {'name': 'Glaris', 'emoji': '🌄'},
    'SZ': {'name': 'Schwyz', 'emoji': '⛰️'},
    'OW': {'name': 'Obwald', 'emoji': '🏔️'},
    'NW': {'name': 'Nidwald', 'emoji': '🏔️'},
    'UR': {'name': 'Uri', 'emoji': '🗻'},
    'TG': {'name': 'Thurgovie', 'emoji': '🌾'},
    'SH': {'name': 'Schaffhouse', 'emoji': '🏛️'},
    'ZG': {'name': 'Zoug', 'emoji': '💼'}
}

def load_swiss_localities() -> Dict[str, Any]:
    """Charge les données des localités suisses"""
    try:
        with open('/Users/margaux/CovoiturageSuisse/data/swiss_localities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement des localités suisses: {e}")
        return {}

def get_cities_by_canton(canton_code: str) -> List[str]:
    """Récupère les villes d'un canton donné"""
    localities = load_swiss_localities()
    cities = []
    
    for city_name, city_data in localities.items():
        if city_data.get('canton') == canton_code:
            cities.append(city_name)
    
    # Trier par ordre alphabétique
    cities.sort()
    
    # Debug: afficher le nombre de villes trouvées
    logger.info(f"Canton {canton_code}: {len(cities)} villes trouvées")
    if len(cities) > 0 and len(cities) <= 10:
        logger.info(f"Villes du canton {canton_code}: {', '.join(cities)}")
    elif len(cities) > 10:
        logger.info(f"Premières villes du canton {canton_code}: {', '.join(cities[:10])}...")
    
    return cities

def get_date_display(date_filter: str) -> str:
    """Retourne un texte lisible pour le filtre de date"""
    if date_filter == "today":
        return "aujourd'hui"
    elif date_filter == "tomorrow":
        return "demain"
    elif date_filter == "week":
        return "cette semaine"
    elif date_filter == "month":
        return "ce mois"
    else:
        return "toutes les dates"

async def start_passenger_search(update: Update, context: CallbackContext) -> int:
    """Démarre la recherche de passagers"""
    logger.info(f"🚀 START PASSENGER SEARCH: user_id={update.effective_user.id}")
    
    # RESET COMPLET des données utilisateur pour éviter les conflits d'état
    context.user_data.clear()
    logger.info("🔄 Reset complet des données utilisateur pour éviter les conflits")
    
    # Vérifier si l'utilisateur est conducteur
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if not user or not user.is_driver:
        logger.warning(f"🚫 Utilisateur {user_id} n'est pas conducteur - accès refusé")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Vous devez être un conducteur vérifié pour rechercher des passagers.\n\n"
                "Activez d'abord votre profil conducteur depuis le menu principal."
            )
        else:
            await update.message.reply_text(
                "❌ Vous devez être un conducteur vérifié pour rechercher des passagers.\n\n"
                "Activez d'abord votre profil conducteur depuis le menu principal."
            )
        db.close()
        return ConversationHandler.END
    
    logger.info(f"✅ Utilisateur {user_id} est un conducteur vérifié - accès autorisé")
    db.close()
    
    # Initialiser les données de recherche
    context.user_data['search_data'] = {}
    context.user_data['conversation_state'] = 'CANTON_SELECTION'
    logger.info("📋 Données de recherche initialisées - passage à CANTON_SELECTION")
    logger.info("✅ Données de recherche initialisées")
    
    # Créer le clavier avec les cantons
    keyboard = []
    canton_items = list(CANTONS.items())
    
    # Organiser en lignes de 2 boutons
    for i in range(0, len(canton_items), 2):
        row = []
        for j in range(2):
            if i + j < len(canton_items):
                canton_code, canton_info = canton_items[i + j]
                row.append(InlineKeyboardButton(
                    f"{canton_info['emoji']} {canton_info['name']}", 
                    callback_data=f"search_canton:{canton_code}"
                ))
        keyboard.append(row)
    
    # Ajouter les options spéciales
    keyboard.extend([
        [InlineKeyboardButton("🌍 Toute la Suisse", callback_data="search_canton:ALL")],
        [InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")]
    ])
    
    message_text = (
        "🔍 *Recherche de passagers*\n\n"
        "Trouvez des passagers qui cherchent un trajet dans votre région !\n\n"
        "📍 *Étape 1:* Choisissez un canton ou une région"
    )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message_text, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    return CANTON_SELECTION

async def handle_canton_selection(update: Update, context: CallbackContext) -> int:
    """Gère la sélection du canton"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"🎯 CANTON SELECTION: Callback data reçu: {query.data}")
    
    if query.data == "search_cancel":
        await query.edit_message_text("❌ Recherche annulée.")
        return ConversationHandler.END
    
    canton_code = query.data.split(':')[1]
    logger.info(f"🎯 CANTON SELECTION: Canton sélectionné: {canton_code}")
    
    # Initialiser search_data si nécessaire
    if 'search_data' not in context.user_data:
        context.user_data['search_data'] = {}
    
    context.user_data['search_data']['canton'] = canton_code
    
    # Créer le clavier pour la sélection de date
    keyboard = [
        [InlineKeyboardButton("📅 Aujourd'hui", callback_data="search_date:today")],
        [InlineKeyboardButton("📅 Demain", callback_data="search_date:tomorrow")],
        [InlineKeyboardButton("📅 Cette semaine", callback_data="search_date:week")],
        [InlineKeyboardButton("📅 Ce mois", callback_data="search_date:month")],
        [InlineKeyboardButton("📅 Toutes les dates", callback_data="search_date:all")],
        [InlineKeyboardButton("🔙 Retour", callback_data="search_back_canton")],
        [InlineKeyboardButton("❌ Annuler", callback_data="search_cancel")]
    ]
    
    canton_name = "Toute la Suisse" if canton_code == "ALL" else CANTONS.get(canton_code, {}).get('name', canton_code)
    
    message_text = (
        f"📍 *Canton sélectionné:* {canton_name}\n\n"
        "📅 *Étape 2:* Choisissez une période de recherche\n\n"
        "Vous verrez toutes les demandes de trajets des passagers "
        "pour la période sélectionnée."
    )
    
    await query.edit_message_text(
        message_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return DATE_SELECTION

async def handle_date_selection(update: Update, context: CallbackContext) -> int:
    """Gère la sélection de la date et lance la recherche"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "search_cancel":
        await query.edit_message_text("❌ Recherche annulée.")
        return ConversationHandler.END
    
    if query.data == "search_back_canton":
        # Retour à la sélection de canton
        return await start_passenger_search(update, context)
    
    date_option = query.data.split(':')[1]
    context.user_data['search_data']['date_filter'] = date_option
    
    # Effectuer la recherche
    return await perform_passenger_search(update, context)

async def perform_passenger_search(update: Update, context: CallbackContext) -> int:
    """Effectue la recherche de passagers et affiche les résultats"""
    query = update.callback_query
    search_data = context.user_data.get('search_data', {})
    
    canton = search_data.get('canton')
    date_filter = search_data.get('date_filter')
    
    try:
        db = get_db()
        
        # Construire la requête de base pour les demandes de passagers
        base_query = db.query(Trip).filter(
            Trip.trip_role == 'passenger',  # Demandes de passagers
            Trip.is_published == True,
            Trip.is_cancelled == False,
            Trip.departure_time >= datetime.now()  # Trajets futurs uniquement
        )
        
        # Filtrer par canton si spécifié
        if canton and canton != "ALL":
            # Charger les villes du canton
            logger.info(f"🔍 DEBUG: Tentative de chargement des villes pour canton: {canton}")
            canton_cities = get_cities_by_canton(canton)
            logger.info(f"🔍 DEBUG: Recherche dans canton {canton}: {len(canton_cities)} villes trouvées")
            
            # Debug détaillé pour FR
            if canton == "FR":
                logger.info(f"🔍 DEBUG FRIBOURG: Fonction retourne {len(canton_cities)} villes")
                if canton_cities:
                    logger.info(f"🔍 DEBUG FRIBOURG: Premières villes: {', '.join(canton_cities[:10])}")
                    if "Giffers" in canton_cities:
                        logger.info("✅ DEBUG FRIBOURG: Giffers trouvé dans la liste")
                    else:
                        logger.error("❌ DEBUG FRIBOURG: Giffers PAS trouvé dans la liste")
                else:
                    logger.error("❌ DEBUG FRIBOURG: Liste des villes est VIDE")
            
            if canton_cities:
                # Appliquer le filtre des villes du canton
                base_query = base_query.filter(
                    Trip.departure_city.in_(canton_cities) | 
                    Trip.arrival_city.in_(canton_cities)
                )
                logger.info(f"✅ Filtre appliqué pour canton {canton}")
            else:
                # Aucune ville trouvée pour ce canton - pas de résultats
                logger.error(f"❌ ERREUR: Aucune ville trouvée pour canton {canton}")
                await query.edit_message_text(
                    f"🔍 *Recherche de passagers*\n\n"
                    f"📍 Région: {CANTONS.get(canton, {}).get('name', canton)}\n"
                    f"📅 Période: {get_date_display(date_filter)}\n\n"
                    f"❌ Aucune ville connue pour ce canton.\n\n"
                    f"Veuillez vérifier les données ou essayer un autre canton.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_passengers")
                    ]])
                )
                return SHOWING_RESULTS
        
        # Filtrer par date
        now = datetime.now()
        if date_filter == "today":
            end_of_day = now.replace(hour=23, minute=59, second=59)
            base_query = base_query.filter(
                Trip.departure_time >= now,
                Trip.departure_time <= end_of_day
            )
        elif date_filter == "tomorrow":
            tomorrow = now + timedelta(days=1)
            start_tomorrow = tomorrow.replace(hour=0, minute=0, second=0)
            end_tomorrow = tomorrow.replace(hour=23, minute=59, second=59)
            base_query = base_query.filter(
                Trip.departure_time >= start_tomorrow,
                Trip.departure_time <= end_tomorrow
            )
        elif date_filter == "week":
            end_week = now + timedelta(days=7)
            base_query = base_query.filter(
                Trip.departure_time >= now,
                Trip.departure_time <= end_week
            )
        elif date_filter == "month":
            end_month = now + timedelta(days=30)
            base_query = base_query.filter(
                Trip.departure_time >= now,
                Trip.departure_time <= end_month
            )
        # "all" = pas de filtre de date
        
        # Ordonner par date
        passenger_trips = base_query.order_by(Trip.departure_time).limit(10).all()
        
        # Construire le message de résultats
        canton_name = "Toute la Suisse" if canton == "ALL" else CANTONS.get(canton, {}).get('name', canton)
        date_desc = {
            "today": "aujourd'hui",
            "tomorrow": "demain", 
            "week": "cette semaine",
            "month": "ce mois",
            "all": "toutes les dates"
        }.get(date_filter, "période sélectionnée")
        
        if not passenger_trips:
            message_text = (
                f"🔍 *Recherche de passagers*\n\n"
                f"📍 *Région:* {canton_name}\n"
                f"📅 *Période:* {date_desc}\n\n"
                f"😕 *Aucune demande trouvée*\n\n"
                f"Aucun passager ne cherche de trajet pour ces critères.\n"
                f"Essayez d'élargir votre recherche ou de revenir plus tard."
            )
            
            keyboard = [
                [InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="back_to_menu")]
            ]
            
            await query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return SHOWING_RESULTS
        else:
            # Message d'en-tête
            header_message = (
                f"🔍 *Recherche de passagers*\n\n"
                f"📍 *Région:* {canton_name}\n"
                f"📅 *Période:* {date_desc}\n\n"
                f"✅ *{len(passenger_trips)} demande(s) trouvée(s)*\n\n"
                f"Voici les demandes de trajets trouvées :"
            )
            
            # Supprimer le message de recherche précédent et envoyer l'en-tête
            await query.edit_message_text(
                header_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="back_to_menu")]
                ])
            )
            
            # Envoyer chaque trajet comme un message séparé avec ses boutons
            for i, trip in enumerate(passenger_trips, 1):
                # Récupérer les informations du passager
                try:
                    passenger = db.query(User).filter_by(id=trip.creator_id).first()
                    passenger_name = passenger.username if passenger and passenger.username else "Utilisateur"
                except:
                    passenger_name = "Utilisateur"
                
                # Format de la date
                departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
                
                # Gérer le nombre de places recherchées
                seats_needed = getattr(trip, 'seats_available', 1) or 1
                seats_text = f"{seats_needed} place{'s' if seats_needed > 1 else ''}"
                
                # Créer le message pour ce trajet
                trip_message = (
                    f"*Demande {i}:*\n"
                    f"🏁 {trip.departure_city} → {trip.arrival_city}\n"
                    f"📅 {departure_date}\n"
                    f"👥 {seats_text} recherchée{'s' if seats_needed > 1 else ''}\n"
                    f"👤 Par: @{passenger_name}\n"
                )
                
                if hasattr(trip, 'additional_info') and trip.additional_info:
                    info_preview = trip.additional_info[:50] + "..." if len(trip.additional_info) > 50 else trip.additional_info
                    trip_message += f"💬 {info_preview}\n"
                
                # Boutons pour ce trajet spécifique
                trip_keyboard = [
                    [InlineKeyboardButton("🚗 Proposer mes services", callback_data=f"propose_service:{trip.id}")],
                    [InlineKeyboardButton("📋 Voir détails", callback_data=f"search_passenger_details:{trip.id}")]
                ]
                
                # Envoyer le message du trajet avec ses boutons
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=trip_message,
                    reply_markup=InlineKeyboardMarkup(trip_keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
            
            return SHOWING_RESULTS
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de passagers: {e}")
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de la recherche.\n\n"
            "Veuillez réessayer plus tard.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")
            ]])
        )
        return SHOWING_RESULTS

async def show_passenger_trip_details(update: Update, context: CallbackContext) -> int:
    """Affiche les détails d'une demande de trajet de passager"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(':')[1])
    
    try:
        db = get_db()
        trip = db.query(Trip).filter_by(id=trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Cette demande de trajet n'existe plus.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")
                ]])
            )
            return SHOWING_RESULTS
        
        # Récupérer les informations du passager
        passenger = db.query(User).filter_by(id=trip.creator_id).first()
        passenger_name = passenger.username if passenger and passenger.username else "Utilisateur anonyme"
        passenger_rating = passenger.passenger_rating if passenger else 5.0
        
        # Format de la date
        departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
        
        # Gérer l'heure flexible
        time_display = departure_date
        if hasattr(trip, 'flexible_time') and trip.flexible_time:
            hour = trip.departure_time.hour
            if 6 <= hour < 12:
                time_display = trip.departure_time.strftime("%d/%m/%Y") + " - Dans la matinée"
            elif 12 <= hour < 18:
                time_display = trip.departure_time.strftime("%d/%m/%Y") + " - L'après-midi"
            elif 18 <= hour < 23:
                time_display = trip.departure_time.strftime("%d/%m/%Y") + " - En soirée"
            else:
                time_display = trip.departure_time.strftime("%d/%m/%Y") + " - Heure à définir"
        
        # Construire le message détaillé  
        seats_needed = getattr(trip, 'seats_available', 1) or 1
        seats_text = f"{seats_needed} place{'s' if seats_needed > 1 else ''}"
        
        message_text = (
            f"🚗 *Demande de trajet*\n\n"
            f"🏁 *Itinéraire:* {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 *Date:* {time_display}\n"
            f"👥 *Places recherchées:* {seats_text}\n"
            f"👤 *Passager:* @{passenger_name}\n"
            f"⭐ *Note:* {passenger_rating:.1f}/5.0\n\n"
        )
        
        # Ajouter les informations supplémentaires
        if hasattr(trip, 'additional_info') and trip.additional_info:
            message_text += f"💬 *Commentaire:*\n{trip.additional_info}\n\n"
        
        # Ajouter les préférences si disponibles
        preferences = []
        if hasattr(trip, 'smoking') and trip.smoking:
            if trip.smoking == "no_smoking":
                preferences.append("🚭 Non-fumeur")
            elif trip.smoking == "smoking_ok":
                preferences.append("🚬 Fumeur OK")
        
        if hasattr(trip, 'pets_allowed') and trip.pets_allowed:
            if trip.pets_allowed == "no_pets":
                preferences.append("🐕‍🦺 Pas d'animaux")
            elif trip.pets_allowed == "pets_ok":
                preferences.append("🐕 Animaux OK")
        
        if hasattr(trip, 'luggage_size') and trip.luggage_size:
            if trip.luggage_size == "small":
                preferences.append("🎒 Bagages légers")
            elif trip.luggage_size == "medium":
                preferences.append("🧳 Bagages moyens")
            elif trip.luggage_size == "large":
                preferences.append("🏗️ Gros bagages")
        
        if preferences:
            message_text += f"🔧 *Préférences:*\n" + "\n".join([f"  • {pref}" for pref in preferences]) + "\n\n"
        
        # Ajouter des informations sur le trajet
        if hasattr(trip, 'women_only') and trip.women_only:
            message_text += "👩‍🦳 *Trajet entre femmes uniquement*\n\n"
        
        if hasattr(trip, 'recurring') and trip.recurring:
            message_text += "🔄 *Trajet régulier (hebdomadaire)*\n\n"
        
        # Boutons d'action
        keyboard = [
            [InlineKeyboardButton("� Proposer mes services", callback_data=f"propose_service:{trip_id}")],
            [InlineKeyboardButton("�📱 Contacter ce passager", callback_data=f"search_contact:{trip_id}")],
            [InlineKeyboardButton("📍 Voir sur la carte", callback_data=f"search_map:{trip_id}")],
            [InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")],
            [InlineKeyboardButton("🔍 Nouvelle recherche", callback_data="search_new")]
        ]
        
        await query.edit_message_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return SHOWING_RESULTS
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des détails du trajet {trip_id}: {e}")
        await query.edit_message_text(
            "❌ Impossible d'afficher les détails de cette demande.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour aux résultats", callback_data="search_back_results")
            ]])
        )
        return SHOWING_RESULTS

async def contact_passenger(update: Update, context: CallbackContext) -> int:
    """Gère le contact avec un passager - VERSION SÉCURISÉE avec paiement obligatoire"""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(':')[1])
    
    try:
        db = get_db()
        trip = db.query(Trip).filter_by(id=trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Cette demande de trajet n'existe plus.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="search_back_results")
                ]])
            )
            return SHOWING_RESULTS
        
        # Récupérer les informations du passager (mais sans révéler les détails de contact)
        passenger = db.query(User).filter_by(id=trip.creator_id).first()
        
        if not passenger:
            await query.edit_message_text(
                "❌ Impossible de contacter ce passager.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="search_back_results")
                ]])
            )
            return SHOWING_RESULTS
        
        # Vérifier si ce conducteur a déjà une proposition en cours
        from database.models import DriverProposal
        conductor_id = query.from_user.id
        existing_proposal = db.query(DriverProposal).filter(
            DriverProposal.trip_id == trip_id,
            DriverProposal.driver_id == conductor_id,
            DriverProposal.status == 'pending'
        ).first()
        
        # Construire les informations du trajet (sans révéler l'identité du passager)
        trip_info = f"{trip.departure_city} → {trip.arrival_city}"
        trip_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
        
        if existing_proposal:
            # Proposition déjà envoyée - Afficher l'état
            keyboard = [
                [InlineKeyboardButton("⏳ Proposition en attente", callback_data="search_no_action")],
                [InlineKeyboardButton("� Retour aux détails", callback_data=f"search_passenger_details:{trip_id}")]
            ]
            
            contact_message = (
                f"⏳ *Proposition déjà envoyée*\n\n"
                f"👤 *Passager:* Anonyme (révélé après paiement)\n"
                f"📍 *Trajet:* {trip_info}\n"
                f"📅 *Date:* {trip_date}\n\n"
                f"🔒 *Votre proposition est en attente de réponse.*\n"
                f"📱 *Contact révélé uniquement après paiement du passager.*"
            )
        else:
            # Nouvelle proposition - Système sécurisé
            keyboard = [
                [InlineKeyboardButton("� Proposer mon service", callback_data=f"search_send_proposal:{trip_id}")],
                [InlineKeyboardButton("🔙 Retour aux détails", callback_data=f"search_passenger_details:{trip_id}")]
            ]
            
            contact_message = (
                f"💰 *Proposer votre service de conducteur*\n\n"
                f"👤 *Passager:* Anonyme (révélé après paiement)\n"
                f"📍 *Trajet:* {trip_info}\n"
                f"📅 *Date:* {trip_date}\n\n"
                f"🔐 *Système sécurisé PayPal:*\n"
                f"• Votre proposition sera envoyée au passager\n"
                f"• Il recevra un lien de paiement sécurisé\n"
                f"• Vos contacts révélés après paiement confirmé\n"
                f"• Commission: 12% | Votre part: 88%\n\n"
                f"📝 *Proposez vos services pour ce trajet.*"
            )
        
        await query.edit_message_text(
            contact_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CONTACT_PASSENGER
        
    except Exception as e:
        logger.error(f"Erreur lors du contact avec le passager pour le trajet {trip_id}: {e}")
        await query.edit_message_text(
            "❌ Erreur lors de la préparation du contact.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="search_back_results")
            ]])
        )
        return SHOWING_RESULTS

async def send_secure_proposal(update: Update, context: CallbackContext, trip_id: int) -> int:
    """Envoie une proposition sécurisée au passager avec paiement PayPal obligatoire"""
    query = update.callback_query
    await query.answer()
    
    try:
        db = get_db()
        trip = db.query(Trip).filter_by(id=trip_id).first()
        
        if not trip:
            await query.edit_message_text(
                "❌ Cette demande de trajet n'existe plus.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="search_back_results")
                ]])
            )
            return SHOWING_RESULTS
        
        # Vérifier que le conducteur a un profil complet
        from database.models import DriverProposal
        conductor_id = query.from_user.id
        conductor = db.query(User).filter_by(telegram_id=conductor_id).first()
        
        if not conductor or not conductor.paypal_email:
            await query.edit_message_text(
                "❌ *Profil incomplet*\n\n"
                "Pour proposer vos services, vous devez d'abord :\n"
                "• Créer votre profil conducteur\n"
                "• Ajouter votre email PayPal\n\n"
                "Utilisez /profil pour compléter votre profil.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data=f"search_passenger_details:{trip_id}")
                ]])
            )
            return CONTACT_PASSENGER
        
        # Créer la proposition de conducteur
        proposal = DriverProposal(
            trip_id=trip_id,
            driver_id=conductor_id,
            driver_name=conductor.full_name or conductor.username or "Conducteur",
            driver_paypal_email=conductor.paypal_email,
            status='pending',
            created_at=datetime.now()
        )
        
        db.add(proposal)
        db.commit()
        
        # Informer le passager qu'il a reçu une proposition
        passenger = db.query(User).filter_by(id=trip.creator_id).first()
        if passenger and passenger.telegram_id:
            trip_info = f"{trip.departure_city} → {trip.arrival_city}"
            trip_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
            
            # Message au passager avec lien de paiement sécurisé
            passenger_message = (
                f"🚗 *Nouvelle proposition de conducteur !*\n\n"
                f"📍 *Trajet:* {trip_info}\n"
                f"📅 *Date:* {trip_date}\n"
                f"👤 *Conducteur:* {proposal.driver_name}\n\n"
                f"💰 *Paiement sécurisé PayPal requis*\n"
                f"• Commission plateforme: 12%\n"
                f"• Montant conducteur: 88%\n\n"
                f"🔐 Les coordonnées du conducteur seront révélées après paiement confirmé."
            )
            
            keyboard = [
                [InlineKeyboardButton("💳 Procéder au paiement", callback_data=f"pay_proposal:{proposal.id}")],
                [InlineKeyboardButton("❌ Refuser", callback_data=f"reject_proposal:{proposal.id}")]
            ]
            
            try:
                await context.bot.send_message(
                    chat_id=passenger.telegram_id,
                    text=passenger_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Erreur envoi message au passager {passenger.telegram_id}: {e}")
        
        # Confirmer au conducteur
        confirmation_message = (
            f"✅ *Proposition envoyée avec succès !*\n\n"
            f"📍 *Trajet:* {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 *Date:* {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"🔔 *Le passager a été notifié*\n"
            f"💳 *Paiement sécurisé requis avant révélation des contacts*\n"
            f"⏰ *Vous serez notifié dès qu'il confirme le paiement*\n\n"
            f"💰 *Votre rémunération: 88% du montant payé*"
        )
        
        await query.edit_message_text(
            confirmation_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour aux recherches", callback_data="search_back_results")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="back_to_menu")]
            ])
        )
        
        return CONTACT_PASSENGER
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la proposition pour le trajet {trip_id}: {e}")
        await query.edit_message_text(
            "❌ Erreur lors de l'envoi de la proposition.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data=f"search_passenger_details:{trip_id}")
            ]])
        )
        return CONTACT_PASSENGER

async def handle_search_actions(update: Update, context: CallbackContext) -> int:
    """Gère les actions diverses de la recherche"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "search_new":
        # Nouvelle recherche
        return await start_passenger_search(update, context)
    
    elif query.data == "search_back_results":
        # Retour aux résultats de recherche
        return await perform_passenger_search(update, context)
    
    elif query.data == "back_to_menu":
        # Retour au menu principal
        await query.edit_message_text(
            "👋 Retour au menu principal.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")
            ]])
        )
        return ConversationHandler.END
    
    elif query.data.startswith("search_send_proposal:"):
        # Envoyer une proposition sécurisée au passager
        trip_id = int(query.data.split(':')[1])
        return await send_secure_proposal(update, context, trip_id)
    
    elif query.data == "search_no_action":
        await query.answer("⏳ Votre proposition est en attente de réponse.", show_alert=True)
        return CONTACT_PASSENGER
    
    elif query.data.startswith("search_copy_message:"):
        # Copier le message prédéfini
        await query.answer("📋 Message copié ! Vous pouvez maintenant le coller dans Telegram.", show_alert=True)
        return CONTACT_PASSENGER
    
    elif query.data.startswith("search_share_phone:"):
        # Partager le numéro (fonctionnalité future)
        await query.answer("📞 Fonctionnalité bientôt disponible !", show_alert=True)
        return CONTACT_PASSENGER
    
    elif query.data.startswith("search_map:"):
        # Voir sur la carte (fonctionnalité future)
        await query.answer("📍 Fonctionnalité bientôt disponible !", show_alert=True)
        return SHOWING_RESULTS
    
    elif query.data == "search_no_direct_contact":
        await query.answer("⚠️ Ce passager a un profil privé. Utilisez les autres options de contact.", show_alert=True)
        return CONTACT_PASSENGER
    
    else:
        # Action non reconnue
        await query.edit_message_text("❌ Action non reconnue.")
        return ConversationHandler.END

async def handle_cancel_search(update: Update, context: CallbackContext) -> int:
    """Gère l'annulation de la recherche depuis n'importe quel état"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ Recherche annulée.")
    context.user_data.clear()
    return ConversationHandler.END

# Configuration du ConversationHandler
search_passengers_handler = ConversationHandler(
    entry_points=[
        CommandHandler("chercher_passagers", start_passenger_search),
        CallbackQueryHandler(start_passenger_search, pattern=r"^search_passengers$")
    ],
    states={
        CANTON_SELECTION: [
            CallbackQueryHandler(handle_canton_selection, pattern=r"^search_canton:"),
            # Permettre de relancer la recherche même si on est dans cet état
            CommandHandler("chercher_passagers", start_passenger_search)
        ],
        DATE_SELECTION: [
            CallbackQueryHandler(handle_date_selection, pattern=r"^search_date:"),
            CallbackQueryHandler(handle_date_selection, pattern=r"^search_back_canton$"),
            # Permettre de relancer la recherche même si on est dans cet état
            CommandHandler("chercher_passagers", start_passenger_search)
        ],
        SHOWING_RESULTS: [
            CallbackQueryHandler(show_passenger_trip_details, pattern=r"^search_passenger_details:"),
            CallbackQueryHandler(contact_passenger, pattern=r"^search_contact:"),
            CallbackQueryHandler(handle_search_actions, pattern=r"^(search_new|search_back_results|back_to_menu|search_map:)"),
            # Permettre de relancer la recherche même si on est dans cet état
            CommandHandler("chercher_passagers", start_passenger_search)
        ],
        CONTACT_PASSENGER: [
            CallbackQueryHandler(handle_search_actions, pattern=r"^search_copy_message:"),
            CallbackQueryHandler(handle_search_actions, pattern=r"^search_share_phone:"),
            CallbackQueryHandler(handle_search_actions, pattern=r"^search_send_proposal:"),
            CallbackQueryHandler(handle_search_actions, pattern=r"^search_no_action$"),
            CallbackQueryHandler(handle_search_actions, pattern=r"^search_no_direct_contact$"),
            CallbackQueryHandler(show_passenger_trip_details, pattern=r"^search_passenger_details:"),
            CallbackQueryHandler(handle_search_actions, pattern=r"^(search_new|search_back_results|back_to_menu)"),
            # Permettre de relancer la recherche même si on est dans cet état
            CommandHandler("chercher_passagers", start_passenger_search)
        ]
    },
    fallbacks=[
        CommandHandler("chercher_passagers", start_passenger_search),  # Fallback pour relancer
        CallbackQueryHandler(handle_search_actions, pattern=r"^back_to_menu$"),
        CallbackQueryHandler(handle_cancel_search, pattern=r"^search_cancel$")  # 🔧 FIX: Gérer l'annulation
    ],
    allow_reentry=True,  # Permettre de relancer la conversation
    name="search_passengers",
    # 🎯 FIX FINAL: Configuration identique au create_trip_handler qui FONCTIONNE
    persistent=True,
    per_message=False,
    per_chat=False,
    per_user=True  # Chaque utilisateur a sa propre conversation
)

async def cmd_search_passengers(update: Update, context: CallbackContext):
    """Handler pour la commande /chercher_passagers"""
    return await start_passenger_search(update, context)

def register_search_passengers_handler(application):
    """Enregistre le handler de recherche de passagers"""
    logger.info("🔧 REGISTRATION: Enregistrement du handler de recherche de passagers")
    
    # Handler principal de conversation - PRIORITÉ ABSOLUE
    application.add_handler(search_passengers_handler)
    logger.info("✅ REGISTRATION: ConversationHandler search_passengers_handler ajouté")
    
    # ❌ SUPPRIMÉ: Handler en doublon qui crée des conflits avec menu_handlers
    # application.add_handler(CallbackQueryHandler(
    #     start_passenger_search, 
    #     pattern=r"^search_passengers$"
    # ))
    
    # Ajouter la commande /chercher_passagers
    application.add_handler(CommandHandler("chercher_passagers", cmd_search_passengers))
    
    logger.info("✅ REGISTRATION: Handler de recherche de passagers enregistré SANS conflit")

if __name__ == "__main__":
    # Pour les tests
    print("Handler de recherche de passagers créé avec succès!")
    print(f"Cantons supportés: {len(CANTONS)}") 
    print("Commandes disponibles:")
    print("- /chercher_passagers")
    print("- Callback: search_passengers")
