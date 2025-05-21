#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/handlers/trip_creation/passenger_trip_handler.py
"""
Handler pour la création de trajet en tant que passager.
"""
import logging
from datetime import datetime, timedelta
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
from utils.date_picker import (
    start_date_selection, handle_calendar_navigation, 
    handle_day_selection, handle_time_selection, handle_datetime_action
)
from utils.location_picker import (
    start_location_selection, handle_location_selection, handle_location_query
)
from handlers.preferences.trip_preferences_handler import (
    show_preferences_menu, show_preference_options, 
    handle_option_selection, handle_preferences_action
)
from .common import (
    get_trip_creation_keyboard, handle_trip_type_selection,
    show_trip_summary, handle_trip_confirmation, handle_edit_selection,
    common_states
)

logger = logging.getLogger(__name__)

# États de conversation
(
    TRIP_TYPE,
    PASSENGER_START,
    DEPARTURE,
    ARRIVAL,
    CALENDAR,
    TIME,
    CONFIRM_DATETIME,
    PASSENGER_COUNT,
    NEEDS,
    PREFERENCES,
    CONFIRM,
    REGULAR_DETAILS,
    EDITING_TRIP,
    EDITING_PASSENGER_COUNT,
    EDITING_NEEDS,
    REGULAR_ROLE,
    WOMEN_ROLE,
    WOMEN_ONLY_CHECK,
    CANCEL
) = range(19)

async def start_passenger_trip(update: Update, context: CallbackContext):
    """Démarre le processus de création d'un trajet passager"""
    logger.debug("🔍 DEBUG: start_passenger_trip appelé")
    if update.callback_query:
        logger.debug(f"🔍 DEBUG: callback_data={update.callback_query.data}")
        
    query = update.callback_query
    if query:
        await query.answer()
    
    # Enregistrons des informations pour le débogage
    logger.info(f"Démarrage création trajet passager: user_id={update.effective_user.id}")
    
    # Vérifier si l'utilisateur est autorisé à être passager
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if not user:
        # L'utilisateur n'a pas de profil, il faut en créer un
        user = User(telegram_id=user_id, username=update.effective_user.username)
        db.add(user)
        db.commit()
    
    # Vérifier si l'utilisateur est déjà un passager
    if not user.is_passenger:
        # L'utilisateur n'est pas encore passager
        keyboard = [
            [InlineKeyboardButton("✅ Devenir passager", callback_data="become_passenger")],
            [InlineKeyboardButton("❌ Annuler", callback_data="cancel_passenger")]
        ]
        
        message_text = (
            "👥 *Mode Passager*\n\n"
            "Pour créer une demande de trajet, vous devez d'abord "
            "activer votre profil passager.\n\n"
            "En devenant passager, vous acceptez:\n"
            "- De respecter les règles définies par les conducteurs\n"
            "- De prévenir en cas d'annulation\n"
            "- De traiter les autres utilisateurs avec respect"
        )
        
        if query:
            await query.edit_message_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return "BECOMING_PASSENGER"
    
    # L'utilisateur est déjà passager, continuer avec la création de la demande
    return await start_departure_selection(update, context)

async def handle_become_passenger(update: Update, context: CallbackContext):
    """Gère l'activation du profil passager"""
    query = update.callback_query
    await query.answer()
    
    # Extraire l'action
    action = query.data
    
    if action == "become_passenger":
        # Activer le profil passager
        user_id = query.from_user.id
        db = get_db()
        user = db.query(User).filter_by(telegram_id=user_id).first()
        
        if user:
            user.is_passenger = True
            db.commit()
            logger.info(f"Utilisateur {user_id} est devenu passager")
            
            await query.edit_message_text(
                "✅ *Profil passager activé!*\n\n"
                "Vous pouvez maintenant créer des demandes de trajet.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Continuer avec la création de la demande
            return await start_departure_selection(update, context)
        else:
            await query.edit_message_text(
                "❌ Erreur: Votre profil n'a pas été trouvé."
            )
            return ConversationHandler.END
    
    elif action == "cancel_passenger":
        # Annuler l'activation
        await query.edit_message_text(
            "❌ Activation du profil passager annulée."
        )
        return ConversationHandler.END
    
    else:
        # Action non reconnue
        await query.edit_message_text("❌ Action non reconnue.")
        return ConversationHandler.END

async def start_departure_selection(update: Update, context: CallbackContext):
    """Démarre la sélection de la ville de départ"""
    # Initialiser le dictionnaire des données du trajet
    context.user_data['trip_type'] = 'passenger'
    
    # Rediriger vers le sélecteur de localité
    return await start_location_selection(
        update, context, 
        "departure", 
        "🏙️ D'où souhaitez-vous partir?"
    )

async def after_departure_selection(update: Update, context: CallbackContext):
    """Handler appelé après la sélection de la ville de départ"""
    # Rediriger vers le sélecteur de localité pour la ville d'arrivée
    return await start_location_selection(
        update, context, 
        "arrival", 
        "🏙️ Où souhaitez-vous aller?"
    )

async def after_arrival_selection(update: Update, context: CallbackContext):
    """Handler appelé après la sélection de la ville d'arrivée"""
    # Rediriger vers le sélecteur de date
    return await start_date_selection(
        update, context,
        "📅 À quelle date souhaitez-vous partir?"
    )

async def after_datetime_selection(update: Update, context: CallbackContext):
    """Handler appelé après la sélection de la date et l'heure"""
    query = update.callback_query
    await query.answer()
    
    # Créer un clavier pour le nombre de passagers
    keyboard = []
    # Créer des boutons pour 1 à 4 passagers
    for i in range(1, 5):
        keyboard.append([InlineKeyboardButton(f"{i} {('personne' if i == 1 else 'personnes')}", callback_data=f"passengers:{i}")])
    
    await query.edit_message_text(
        "👥 Combien de personnes voyagent avec vous?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PASSENGER_COUNT

async def handle_passenger_count(update: Update, context: CallbackContext):
    """Gère la sélection du nombre de passagers"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le nombre de passagers
    parts = query.data.split(':', 1)
    if len(parts) != 2:
        await query.edit_message_text("❌ Nombre de passagers non valide.")
        return PASSENGER_COUNT
    
    _, passengers_str = parts
    
    try:
        passengers = int(passengers_str)
        if passengers < 1 or passengers > 4:
            raise ValueError("Nombre de passagers hors limites")
        
        # Sauvegarder le nombre de passagers
        context.user_data['passengers'] = passengers
        
        # Passer à la saisie des besoins spécifiques
        await query.edit_message_text(
            "📝 Avez-vous des besoins particuliers?\n\n"
            "Par exemple:\n"
            "- Flexibilité horaire\n"
            "- Bagages volumineux\n"
            "- Autres informations importantes\n\n"
            "Entrez vos besoins ou cliquez sur 'Passer':",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏭️ Passer", callback_data="needs:skip")]
            ])
        )
        
        return NEEDS
        
    except ValueError:
        await query.edit_message_text("❌ Nombre de passagers non valide.")
        return PASSENGER_COUNT

async def handle_needs_input(update: Update, context: CallbackContext):
    """Gère l'entrée des besoins spécifiques"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # L'utilisateur a cliqué sur "Passer"
        if query.data == "needs:skip":
            context.user_data['needs'] = None
        else:
            # Action non reconnue
            await query.edit_message_text("❌ Action non reconnue.")
            return NEEDS
    else:
        # L'utilisateur a entré du texte
        needs_text = update.message.text.strip()
        context.user_data['needs'] = needs_text
    
    # Passer aux préférences
    return await show_preferences_menu(update, context)

async def after_preferences(update: Update, context: CallbackContext):
    """Handler appelé après la sélection des préférences"""
    # Passer à la confirmation de la demande
    return await show_trip_summary(update, context, "SAVE_TRIP")

async def save_trip_request(update: Update, context: CallbackContext):
    """Sauvegarde la demande de trajet dans la base de données"""
    # Récupérer les données du trajet
    trip_data = context.user_data
    
    # Récupérer l'utilisateur
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if not user:
        # Cas improbable mais à gérer
        await update.callback_query.edit_message_text(
            "❌ Erreur: Votre profil n'a pas été trouvé."
        )
        return ConversationHandler.END
    
    # Créer la nouvelle demande de trajet (utiliser la même table Trip avec un flag)
    try:
        new_request = Trip(
            passenger_id=user.id,  # Utiliser passenger_id au lieu de driver_id
            departure_city=trip_data.get('departure'),
            arrival_city=trip_data.get('arrival'),
            departure_time=trip_data.get('selected_datetime'),
            seats_needed=trip_data.get('passengers', 1),  # Nombre de passagers nécessaires
            is_request=True,  # Flag pour indiquer qu'il s'agit d'une demande
            additional_info=trip_data.get('needs'),
            
            # Préférences
            preferences = trip_data.get('trip_preferences', {})
        )
        
        # Ajouter les préférences spécifiques si présentes
        preferences = trip_data.get('trip_preferences', {})
        if preferences:
            if 'smoking' in preferences:
                new_request.smoking = preferences['smoking']
            if 'music' in preferences:
                new_request.music = preferences['music']
            if 'talk_preference' in preferences:
                new_request.talk_preference = preferences['talk_preference']
            if 'pets_allowed' in preferences:
                new_request.pets_allowed = preferences['pets_allowed']
            if 'luggage_size' in preferences:
                new_request.luggage_size = preferences['luggage_size']
        
        # Autres options spéciales
        new_request.recurring = trip_data.get('is_regular', False)
        new_request.women_only = trip_data.get('women_only', False)
        
        # Sauvegarder dans la base de données
        db.add(new_request)
        db.commit()
        
        # Log de création réussie
        logger.info(f"Nouvelle demande de trajet créée par {user_id} de {new_request.departure_city} à {new_request.arrival_city}")
        
        # Message de confirmation
        message_text = (
            "✅ *Demande de trajet créée avec succès!*\n\n"
            f"Votre demande de trajet de *{new_request.departure_city}* à *{new_request.arrival_city}* "
            f"le {new_request.departure_time.strftime('%d/%m/%Y à %H:%M')} a été enregistrée.\n\n"
            f"Elle est maintenant visible pour les conducteurs potentiels."
        )
        
        # Ajouter des boutons pour les actions suivantes
        keyboard = [
            [InlineKeyboardButton("🔍 Chercher des trajets", callback_data="search_trips")],
            [InlineKeyboardButton("📋 Voir mes demandes", callback_data="view_my_requests")],
            [InlineKeyboardButton("🔙 Menu principal", callback_data="back_to_menu")]
        ]
        
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Nettoyer les données temporaires
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        # Gérer les erreurs de création de demande
        logger.error(f"Erreur lors de la création de la demande de trajet: {str(e)}")
        
        await update.callback_query.edit_message_text(
            "❌ Une erreur est survenue lors de la création de la demande.\n\n"
            "Veuillez réessayer plus tard."
        )
        
        return ConversationHandler.END

async def handle_after_creation_action(update: Update, context: CallbackContext):
    """Gère les actions après la création d'une demande de trajet"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "search_trips":
        # Rediriger vers la recherche de trajets
        # Cette fonction doit être définie ailleurs
        from handlers.trip_search.search_handler import start_search
        return await start_search(update, context)
    
    elif action == "view_my_requests":
        # Rediriger vers la liste des demandes de l'utilisateur
        # Cette fonction doit être définie ailleurs
        from handlers.trip_handlers import list_my_trips
        return await list_my_trips(update, context)
    
    elif action == "back_to_menu":
        # Rediriger vers le menu principal
        # Cette fonction doit être définie ailleurs
        from handlers.menu_handlers import back_to_menu
        return await back_to_menu(update, context)
    
    else:
        # Action non reconnue, retourner au menu
        from handlers.menu_handlers import back_to_menu
        return await back_to_menu(update, context)

# Définir le ConversationHandler pour la création de demande de trajet passager
passenger_trip_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_passenger_trip, pattern=r"^trip_type:passenger$"),
        CommandHandler("demander", start_passenger_trip)
    ],
    states={
        # États initiaux
        "BECOMING_PASSENGER": [
            CallbackQueryHandler(handle_become_passenger, pattern=r"^(become_passenger|cancel_passenger)$")
        ],
        
        # État intermédiaire après sélection du type de trajet
        "PASSENGER_START": [
            # Cet état est généralement transitoire et va directement à start_departure_selection
            CallbackQueryHandler(start_departure_selection, pattern=r"^.*$")
        ],
        
        # Sélection de localités
        "ENTERING_LOCATION": [
            CallbackQueryHandler(
                lambda u, c: after_departure_selection(u, c) if c.user_data.get('location_action') == 'departure' else after_arrival_selection(u, c), 
                pattern=r"^(departure|arrival):.+$"
            )
        ],
        "SEARCHING_LOCATION": [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_query)
        ],
        "SELECTING_FROM_RESULTS": [
            CallbackQueryHandler(
                lambda u, c: after_departure_selection(u, c) if c.user_data.get('location_action') == 'departure' else after_arrival_selection(u, c), 
                pattern=r"^(departure|arrival):.+$"
            )
        ],
        
        # Sélection de date et heure
        "CALENDAR": [
            CallbackQueryHandler(handle_calendar_navigation, pattern=r"^calendar:(prev|next|month):\d+:\d+$"),
            CallbackQueryHandler(handle_day_selection, pattern=r"^calendar:day:\d+:\d+:\d+$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=r"^calendar:cancel$")
        ],
        "TIME": [
            CallbackQueryHandler(handle_time_selection, pattern=r"^time:\d+:\d+$"),
            CallbackQueryHandler(lambda u, c: start_date_selection(u, c), pattern=r"^time:back$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=r"^time:cancel$")
        ],
        "CONFIRM_DATETIME": [
            CallbackQueryHandler(
                lambda u, c: handle_datetime_action(u, c, PASSENGER_COUNT), 
                pattern=r"^datetime:(confirm|change|cancel)$"
            )
        ],
        
        # Sélection du nombre de passagers
        PASSENGER_COUNT: [
            CallbackQueryHandler(handle_passenger_count, pattern=r"^passengers:\d+$")
        ],
        
        # Saisie des besoins spécifiques
        NEEDS: [
            CallbackQueryHandler(handle_needs_input, pattern=r"^needs:skip$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_needs_input)
        ],
        
        # Préférences
        "CHOOSING_PREFERENCE": [
            CallbackQueryHandler(show_preference_options, pattern=r"^pref:[a-z_]+$"),
            CallbackQueryHandler(
                lambda u, c: handle_preferences_action(u, c, "CONFIRM"), 
                pattern=r"^pref:(save|cancel)$"
            )
        ],
        "SELECTING_OPTION": [
            CallbackQueryHandler(handle_option_selection, pattern=r"^option:.+$")
        ],
        
        # Confirmation finale
        "CONFIRMING_TRIP": [
            CallbackQueryHandler(
                lambda u, c: handle_trip_confirmation(u, c), 
                pattern=r"^trip:(confirm|edit|cancel)$"
            )
        ],
        
        # Édition de la demande
        "EDITING_TRIP": [
            CallbackQueryHandler(handle_edit_selection, pattern=r"^edit:.+$")
        ],
        "EDITING_PASSENGER_COUNT": [
            CallbackQueryHandler(
                lambda u, c: handle_passenger_count(u, c), 
                pattern=r"^passengers:\d+$"
            )
        ],
        "EDITING_NEEDS": [
            CallbackQueryHandler(handle_needs_input, pattern=r"^needs:skip$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_needs_input)
        ],
        
        # Sauvegarde de la demande
        "SAVE_TRIP": [
            CallbackQueryHandler(save_trip_request, pattern=r"^trip:confirm$"),
            CallbackQueryHandler(handle_trip_confirmation, pattern=r"^trip:(edit|cancel)$")
        ],
        
        # Action après création
        ConversationHandler.END: [
            CallbackQueryHandler(
                handle_after_creation_action, 
                pattern=r"^(search_trips|view_my_requests|back_to_menu)$"
            )
        ],
        
        # États de sortie
        "CANCEL": [
            # Retour au menu principal ou autre action
            CallbackQueryHandler(
                lambda u, c: ConversationHandler.END,
                pattern=r".*"
            )
        ]
    },
    fallbacks=[
        CommandHandler("annuler", lambda u, c: ConversationHandler.END),
        # Autres fallbacks si nécessaire
    ],
    name="passenger_trip_request",
    persistent=True,
)

def register(application):
    """Enregistre les handlers pour la création de demande de trajet passager"""
    logger.info("Enregistrement des handlers de création de demande de trajet passager")
    
    # Enregistrer le ConversationHandler
    application.add_handler(passenger_trip_handler)
    
    # Autres handlers si nécessaire
