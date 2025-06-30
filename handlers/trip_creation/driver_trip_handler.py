#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/handlers/trip_creation/driver_trip_handler.py
"""
Handler pour la création de trajet en tant que conducteur.
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
    DRIVER_START,
    DEPARTURE,
    ARRIVAL,
    CALENDAR,
    TIME,
    CONFIRM_DATETIME,
    SEATS,
    PRICE,
    ADDITIONAL_INFO,
    PREFERENCES,
    CONFIRM,
    REGULAR_DETAILS,
    EDITING_TRIP,
    EDITING_SEATS,
    EDITING_PRICE,
    EDITING_INFO,
    REGULAR_ROLE,
    WOMEN_ROLE,
    WOMEN_ONLY_CHECK,
    CANCEL
) = range(21)

async def start_driver_trip(update: Update, context: CallbackContext):
    """Démarre le processus de création d'un trajet conducteur"""
    logger.debug("🔍 DEBUG: start_driver_trip appelé")
    if update.callback_query:
        logger.debug(f"🔍 DEBUG: callback_data={update.callback_query.data}")

    query = update.callback_query
    if query:
        await query.answer()
        
    # Enregistrons des informations pour le débogage
    logger.info(f"Démarrage création trajet conducteur: user_id={update.effective_user.id}")
    
    # Vérifier si l'utilisateur est autorisé à être conducteur
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if not user:
        # L'utilisateur n'a pas de profil, il faut en créer un
        user = User(telegram_id=user_id, username=update.effective_user.username)
        db.add(user)
        db.commit()
    
    # Vérifier si l'utilisateur est déjà un conducteur
    if not user.is_driver:
        # L'utilisateur n'est pas encore conducteur
        keyboard = [
            [InlineKeyboardButton("✅ Devenir conducteur", callback_data="become_driver")],
            [InlineKeyboardButton("❌ Annuler", callback_data="cancel_driver")]
        ]
        
        message_text = (
            "🚗 *Mode Conducteur*\n\n"
            "Pour créer un trajet en tant que conducteur, vous devez d'abord "
            "activer votre profil conducteur.\n\n"
            "En devenant conducteur, vous acceptez:\n"
            "- De fournir un véhicule en bon état\n"
            "- D'avoir un permis de conduire valide\n"
            "- De respecter le code de la route"
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
        
        logger.debug("🔍 DEBUG: Retourne l'état BECOMING_DRIVER")
        return "BECOMING_DRIVER" 
    
    # L'utilisateur est déjà conducteur, continuer avec la création du trajet
    logger.debug("🔍 DEBUG: Appel start_departure_selection")
    return await start_departure_selection(update, context)

async def handle_become_driver(update: Update, context: CallbackContext):
    """Gère l'activation du profil conducteur"""
    query = update.callback_query
    await query.answer()
    
    # Extraire l'action
    action = query.data
    
    if action == "become_driver":
        # Activer le profil conducteur
        user_id = query.from_user.id
        db = get_db()
        user = db.query(User).filter_by(telegram_id=user_id).first()
        
        if user:
            user.is_driver = True
            db.commit()
            logger.info(f"Utilisateur {user_id} est devenu conducteur")
            
            # Vérifier si l'utilisateur a déjà un email PayPal
            if user.paypal_email:
                # Email PayPal déjà configuré, continuer avec la création du trajet
                await query.edit_message_text(
                    "✅ *Profil conducteur activé!*\n\n"
                    f"📧 Email PayPal : `{user.paypal_email}`\n\n"
                    "Vous pouvez maintenant créer des trajets en tant que conducteur.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Continuer avec la création du trajet
                logger.debug("🔍 DEBUG: Appel start_departure_selection")
                return await start_departure_selection(update, context)
            else:
                # Pas d'email PayPal, demander la configuration
                keyboard = [
                    [InlineKeyboardButton("💳 Configurer PayPal", callback_data="setup_paypal")],
                    [InlineKeyboardButton("⏭️ Ignorer pour l'instant", callback_data="skip_paypal_setup")]
                ]
                
                await query.edit_message_text(
                    "✅ *Profil conducteur activé!*\n\n"
                    "💳 *Configuration PayPal requise*\n\n"
                    "Pour recevoir vos paiements automatiques (88% du montant), "
                    "vous devez configurer votre email PayPal.\n\n"
                    "⚠️ Sans email PayPal, vous ne pourrez pas recevoir de paiements automatiques.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                # Définir l'état suivant après configuration PayPal
                context.user_data['next_state_after_paypal'] = "DEPARTURE"
                return "PAYPAL_SETUP"
        else:
            await query.edit_message_text(
                "❌ Erreur: Votre profil n'a pas été trouvé."
            )
            return ConversationHandler.END
    
    elif action == "cancel_driver":
        # Annuler l'activation
        await query.edit_message_text(
            "❌ Activation du profil conducteur annulée."
        )
        return ConversationHandler.END
    
    elif action == "skip_paypal_setup":
        # Ignorer la configuration PayPal pour l'instant
        await query.edit_message_text(
            "⏭️ *Configuration PayPal ignorée*\n\n"
            "Vous pourrez configurer votre email PayPal plus tard avec /paypal\n\n"
            "⚠️ Attention : Sans email PayPal configuré, vous ne recevrez "
            "pas de paiements automatiques pour vos trajets."
        )
        
        # Continuer avec la création du trajet
        return await start_departure_selection(update, context)
    
    elif action == "setup_paypal":
        # Rediriger vers le handler de configuration PayPal
        from handlers.paypal_setup_handler import request_paypal_email
        return await request_paypal_email(update, context)
    
    else:
        # Action non reconnue
        await query.edit_message_text("❌ Action non reconnue.")
        return ConversationHandler.END

async def start_departure_selection(update: Update, context: CallbackContext):
    """Démarre la sélection de la ville de départ"""
    # Initialiser le dictionnaire des données du trajet
    context.user_data['trip_type'] = 'driver'
    
    # Rediriger vers le sélecteur de localité
    return await start_location_selection(
        update, context, 
        "departure", 
        "🏙️ Sélectionnez votre ville de départ:"
    )

async def after_departure_selection(update: Update, context: CallbackContext):
    """Handler appelé après la sélection de la ville de départ"""
    # Rediriger vers le sélecteur de localité pour la ville d'arrivée
    return await start_location_selection(
        update, context, 
        "arrival", 
        "🏙️ Sélectionnez votre ville d'arrivée:"
    )

async def after_arrival_selection(update: Update, context: CallbackContext):
    """Handler appelé après la sélection de la ville d'arrivée"""
    # Rediriger vers le sélecteur de date
    return await start_date_selection(
        update, context,
        "📅 Sélectionnez la date de départ:"
    )

async def after_datetime_selection(update: Update, context: CallbackContext):
    """Handler appelé après la sélection de la date et l'heure"""
    query = update.callback_query
    await query.answer()
    
    # Créer un clavier pour le nombre de places
    keyboard = []
    # Créer des boutons pour 1 à 8 places
    for i in range(1, 9):
        keyboard.append([InlineKeyboardButton(str(i), callback_data=f"seats:{i}")])
    
    await query.edit_message_text(
        "👥 Combien de places proposez-vous?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SEATS

async def handle_seats_selection(update: Update, context: CallbackContext):
    """Gère la sélection du nombre de places"""
    query = update.callback_query
    await query.answer()
    
    # Extraire le nombre de places
    parts = query.data.split(':', 1)
    if len(parts) != 2:
        await query.edit_message_text("❌ Nombre de places non valide.")
        return SEATS
    
    _, seats_str = parts
    
    try:
        seats = int(seats_str)
        if seats < 1 or seats > 8:
            raise ValueError("Nombre de places hors limites")
        
        # Sauvegarder le nombre de places
        context.user_data['seats'] = seats
        context.user_data['available_seats'] = seats  # Pour garder la trace des places restantes
        
        # Passer à la sélection du prix
        await query.edit_message_text(
            "💰 Quel est le prix par place (en CHF)?\n\n"
            "Entrez un nombre (par exemple: 15 ou 12.50)"
        )
        
        return PRICE
        
    except ValueError:
        await query.edit_message_text("❌ Nombre de places non valide.")
        return SEATS

async def handle_price_input(update: Update, context: CallbackContext):
    """Gère l'entrée du prix par place"""
    # Récupérer le prix entré
    price_text = update.message.text.strip().replace(',', '.')
    
    try:
        price = float(price_text)
        if price < 0:
            raise ValueError("Prix négatif")
        
        # Arrondir à 2 décimales
        price = round(price, 2)
        
        # Sauvegarder le prix
        context.user_data['price'] = price
        
        # Calculer la commission
        commission = price * 0.12  # 12% de commission
        driver_receives = price - commission
        
        # Informer l'utilisateur sur la commission
        keyboard = [
            [InlineKeyboardButton("✅ Continuer", callback_data="price:continue")],
            [InlineKeyboardButton("✏️ Modifier", callback_data="price:edit")]
        ]
        
        await update.message.reply_text(
            f"💰 *Prix:* {price:.2f} CHF par place\n\n"
            f"📊 *Commission de 12%:* {commission:.2f} CHF\n"
            f"💸 *Vous recevrez:* {driver_receives:.2f} CHF par passager\n\n"
            f"Souhaitez-vous continuer?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "CONFIRMING_PRICE"
        
    except ValueError:
        await update.message.reply_text(
            "❌ Prix non valide. Veuillez entrer un nombre positif (ex: 15 ou 12.50)."
        )
        return PRICE

async def handle_price_confirmation(update: Update, context: CallbackContext):
    """Gère la confirmation du prix"""
    query = update.callback_query
    await query.answer()
    
    # Extraire l'action
    _, action = query.data.split(':', 1)
    
    if action == "continue":
        # Passer aux informations supplémentaires
        await query.edit_message_text(
            "📝 Souhaitez-vous ajouter des informations supplémentaires?\n\n"
            "Par exemple:\n"
            "- Point de rendez-vous précis\n"
            "- Type de voiture\n"
            "- Autres détails importants\n\n"
            "Entrez vos informations ou cliquez sur 'Passer':",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏭️ Passer", callback_data="info:skip")]
            ])
        )
        
        return ADDITIONAL_INFO
        
    elif action == "edit":
        # Permettre à l'utilisateur de modifier le prix
        await query.edit_message_text(
            "💰 Veuillez entrer un nouveau prix par place (en CHF):"
        )
        
        return PRICE
    
    else:
        # Action non reconnue
        await query.edit_message_text("❌ Action non reconnue.")
        return PRICE

async def handle_additional_info(update: Update, context: CallbackContext):
    """Gère l'entrée des informations supplémentaires"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # L'utilisateur a cliqué sur "Passer"
        if query.data == "info:skip":
            context.user_data['additional_info'] = None
        else:
            # Action non reconnue
            await query.edit_message_text("❌ Action non reconnue.")
            return ADDITIONAL_INFO
    else:
        # L'utilisateur a entré du texte
        info_text = update.message.text.strip()
        context.user_data['additional_info'] = info_text
    
    # Passer aux préférences
    return await show_preferences_menu(update, context)

async def after_preferences(update: Update, context: CallbackContext):
    """Handler appelé après la sélection des préférences"""
    # Passer à la confirmation du trajet
    return await show_trip_summary(update, context, "SAVE_TRIP")

async def save_trip(update: Update, context: CallbackContext):
    """Sauvegarde le trajet dans la base de données"""
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
    
    # Créer le nouveau trajet
    try:
        new_trip = Trip(
            driver_id=user.id,
            departure_city=trip_data.get('departure'),
            arrival_city=trip_data.get('arrival'),
            departure_time=trip_data.get('selected_datetime'),
            seats_available=trip_data.get('seats', 1),
            available_seats=trip_data.get('seats', 1),  # Au départ, toutes les places sont disponibles
            price_per_seat=trip_data.get('price', 0),
            additional_info=trip_data.get('additional_info'),
            booking_deadline=trip_data.get('selected_datetime') - timedelta(hours=1),  # Par défaut 1h avant
            is_published=True,  # Publier automatiquement
            
            # Préférences
            preferences = trip_data.get('trip_preferences', {})
        )
        
        # Ajouter les préférences spécifiques si présentes
        preferences = trip_data.get('trip_preferences', {})
        if preferences:
            if 'smoking' in preferences:
                new_trip.smoking = preferences['smoking']
            if 'music' in preferences:
                new_trip.music = preferences['music']
            if 'talk_preference' in preferences:
                new_trip.talk_preference = preferences['talk_preference']
            if 'pets_allowed' in preferences:
                new_trip.pets_allowed = preferences['pets_allowed']
            if 'luggage_size' in preferences:
                new_trip.luggage_size = preferences['luggage_size']
        
        # Autres options spéciales
        new_trip.recurring = trip_data.get('is_regular', False)
        new_trip.women_only = trip_data.get('women_only', False)
        
        # Sauvegarder dans la base de données
        db.add(new_trip)
        db.commit()
        
        # Log de création réussie
        logger.info(f"Nouveau trajet créé par {user_id} de {new_trip.departure_city} à {new_trip.arrival_city}")
        
        # Message de confirmation
        message_text = (
            "✅ *Trajet créé avec succès!*\n\n"
            f"Votre trajet de *{new_trip.departure_city}* à *{new_trip.arrival_city}* "
            f"le {new_trip.departure_time.strftime('%d/%m/%Y à %H:%M')} a été enregistré.\n\n"
            f"Il est maintenant visible pour les passagers potentiels."
        )
        
        # Ajouter des boutons pour les actions suivantes
        keyboard = [
            [InlineKeyboardButton("📋 Voir mes trajets", callback_data="view_my_trips")],
            [InlineKeyboardButton("🚗 Créer un autre trajet", callback_data="create_another_trip")],
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
        # Gérer les erreurs de création de trajet
        logger.error(f"Erreur lors de la création du trajet: {str(e)}")
        
        await update.callback_query.edit_message_text(
            "❌ Une erreur est survenue lors de la création du trajet.\n\n"
            "Veuillez réessayer plus tard."
        )
        
        return ConversationHandler.END

async def handle_after_creation_action(update: Update, context: CallbackContext):
    """Gère les actions après la création d'un trajet"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "create_another_trip":
        # Redémarrer le processus de création
        return await start_driver_trip(update, context)
    
    elif action == "view_my_trips":
        # Rediriger vers la liste des trajets de l'utilisateur
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

# Définir le ConversationHandler pour la création de trajet conducteur
driver_trip_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_driver_trip, pattern=r"^trip_type:driver$"),
        CommandHandler("creer", start_driver_trip)
    ],
    states={
        # États initiaux
        "BECOMING_DRIVER": [
            CallbackQueryHandler(handle_become_driver, pattern=r"^(become_driver|cancel_driver)$")
        ],
        
        # État intermédiaire après sélection du type de trajet
        "DRIVER_START": [
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
                lambda u, c: handle_datetime_action(u, c, SEATS), 
                pattern=r"^datetime:(confirm|change|cancel)$"
            )
        ],
        
        # Sélection du nombre de places
        SEATS: [
            CallbackQueryHandler(handle_seats_selection, pattern=r"^seats:\d+$")
        ],
        
        # Saisie du prix
        PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_input)
        ],
        "CONFIRMING_PRICE": [
            CallbackQueryHandler(handle_price_confirmation, pattern=r"^price:(continue|edit)$")
        ],
        
        # Informations supplémentaires
        ADDITIONAL_INFO: [
            CallbackQueryHandler(handle_additional_info, pattern=r"^info:skip$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_additional_info)
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
        
        # Édition du trajet
        "EDITING_TRIP": [
            CallbackQueryHandler(handle_edit_selection, pattern=r"^edit:.+$")
        ],
        "EDITING_SEATS": [
            CallbackQueryHandler(
                lambda u, c: handle_seats_selection(u, c), 
                pattern=r"^seats:\d+$"
            )
        ],
        "EDITING_PRICE": [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_input)
        ],
        "EDITING_INFO": [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_additional_info)
        ],
        
        # Sauvegarde du trajet
        "SAVE_TRIP": [
            CallbackQueryHandler(save_trip, pattern=r"^trip:confirm$"),
            CallbackQueryHandler(handle_trip_confirmation, pattern=r"^trip:(edit|cancel)$")
        ],
        
        # Action après création
        ConversationHandler.END: [
            CallbackQueryHandler(
                handle_after_creation_action, 
                pattern=r"^(create_another_trip|view_my_trips|back_to_menu)$"
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
    name="driver_trip_creation",
    persistent=True,
)

def register(application):
    """Enregistre les handlers pour la création de trajet conducteur"""
    logger.info("Enregistrement des handlers de création de trajet conducteur")
    
    # Enregistrer le ConversationHandler
    application.add_handler(driver_trip_handler)
    
    # Autres handlers si nécessaire
