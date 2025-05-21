#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/handlers/trip_creation/common.py
"""
Fonctions communes pour la création de trajets.
Module partagé entre les handlers de conducteur et de passager.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler
from database.models import Trip, User
from database import get_db

logger = logging.getLogger(__name__)

# Constantes pour les différents types de trajets
TRIP_TYPES = {
    "driver": {
        "name": "Conducteur",
        "emoji": "🚗",
        "description": "Vous proposez un trajet avec votre véhicule"
    },
    "passenger": {
        "name": "Passager",
        "emoji": "👥",
        "description": "Vous cherchez un trajet en tant que passager"
    },
    "regular": {
        "name": "Régulier",
        "emoji": "🔄",
        "description": "Trajet qui se répète chaque semaine"
    },
    "women_only": {
        "name": "Entre femmes",
        "emoji": "👩",
        "description": "Trajet réservé aux femmes"
    }
}

def get_trip_creation_keyboard(include_women_only: bool = True) -> InlineKeyboardMarkup:
    """
    Crée un clavier pour le choix du type de trajet.
    
    Args:
        include_women_only: Indique si l'option "Entre femmes" doit être incluse
        
    Returns:
        InlineKeyboardMarkup avec les types de trajets
    """
    keyboard = [
        [
            InlineKeyboardButton(
                f"{TRIP_TYPES['driver']['emoji']} {TRIP_TYPES['driver']['name']}", 
                callback_data="trip_type:driver"
            ),
            InlineKeyboardButton(
                f"{TRIP_TYPES['passenger']['emoji']} {TRIP_TYPES['passenger']['name']}", 
                callback_data="trip_type:passenger"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TRIP_TYPES['regular']['emoji']} {TRIP_TYPES['regular']['name']}", 
                callback_data="trip_type:regular"
            )
        ]
    ]
    
    if include_women_only:
        keyboard.append([
            InlineKeyboardButton(
                f"{TRIP_TYPES['women_only']['emoji']} {TRIP_TYPES['women_only']['name']}", 
                callback_data="trip_type:women_only"
            )
        ])
    
    # Bouton pour annuler
    keyboard.append([
        InlineKeyboardButton("❌ Annuler", callback_data="trip_type:cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_trip_type_selection(update: Update, context: CallbackContext):
    """
    Gère la sélection du type de trajet.
    
    Args:
        update: Update Telegram
        context: Contexte de la conversation
        
    Returns:
        État suivant dans la conversation
    """
    query = update.callback_query
    if not query:
        logger.error("❌ ERREUR: handle_trip_type_selection appelé sans callback_query")
        return None
        
    logger.info(f"🔍 INFO: handle_trip_type_selection appelé avec callback_data={query.data} (user_id={update.effective_user.id})")
    
    # S'assurer que c'est bien un callback de type "trip_type"
    if not query.data or not query.data.startswith("trip_type:"):
        logger.error(f"❌ ERREUR: handle_trip_type_selection appelé avec un callback_data invalide: {query.data}")
        return None
    
    try:
        # Répondre immédiatement au callback pour éviter les erreurs de timeout
        await query.answer()
        
        # Extraire le type de trajet
        _, trip_type = query.data.split(':', 1)
        
        logger.info(f"✅ Type de trajet sélectionné: {trip_type} (user_id={update.effective_user.id})")
        
        if trip_type == "cancel":
            # L'utilisateur annule
            try:
                await query.edit_message_text("❌ Création de trajet annulée.")
            except Exception as e:
                logger.warning(f"⚠️ Impossible d'éditer le message d'annulation: {e}")
                # Envoyer un nouveau message si l'édition échoue
                await query.message.reply_text("❌ Création de trajet annulée.")
            return "CANCEL"
        
        # Vérifier si le type est valide
        if trip_type not in TRIP_TYPES:
            logger.error(f"❌ Type de trajet non valide: {trip_type}")
            try:
                await query.edit_message_text("❌ Type de trajet non valide.")
            except Exception as e:
                logger.warning(f"⚠️ Impossible d'éditer le message d'erreur: {e}")
                await query.message.reply_text("❌ Type de trajet non valide.")
            return "CANCEL"
        
        # Sauvegarder le type dans le contexte
        context.user_data['trip_type'] = trip_type
        logger.debug(f"🔍 DEBUG: Type de trajet '{trip_type}' sauvegardé dans context.user_data")
        
        # Message de confirmation
        type_data = TRIP_TYPES[trip_type]
        try:
            await query.edit_message_text(
                f"{type_data['emoji']} *{type_data['name']}*\n\n"
                f"{type_data['description']}\n\n"
                "➡️ Passons aux détails du trajet...",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'éditer le message de confirmation: {e}")
            # Envoyer un nouveau message si l'édition échoue
            await query.message.reply_text(
                f"{type_data['emoji']} *{type_data['name']}*\n\n"
                f"{type_data['description']}\n\n"
                "➡️ Passons aux détails du trajet...",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Déterminer l'état suivant en fonction du type
        if trip_type == "driver":
            logger.info(f"🚗 Sélection type CONDUCTEUR: transition vers DRIVER_START, user_id={update.effective_user.id}")
            return "DRIVER_START"
        elif trip_type == "passenger":
            logger.info(f"🧍 Sélection type PASSAGER: transition vers PASSENGER_START, user_id={update.effective_user.id}")
            return "PASSENGER_START"
        elif trip_type == "regular":
            context.user_data['is_regular'] = True
            # Pour un trajet régulier, demander d'abord si c'est en tant que conducteur ou passager
            keyboard = [
                [
                    InlineKeyboardButton("🚗 Conducteur", callback_data="regular:driver"),
                    InlineKeyboardButton("👥 Passager", callback_data="regular:passenger")
                ],
                [InlineKeyboardButton("❌ Annuler", callback_data="regular:cancel")]
            ]
            try:
                await query.edit_message_text(
                    "🔄 *Trajet régulier*\n\n"
                    "Êtes-vous conducteur ou passager pour ce trajet régulier?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.warning(f"⚠️ Impossible d'éditer le message de trajet régulier: {e}")
                await query.message.reply_text(
                    "🔄 *Trajet régulier*\n\n"
                    "Êtes-vous conducteur ou passager pour ce trajet régulier?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
            return "REGULAR_ROLE"
        elif trip_type == "women_only":
            context.user_data['women_only'] = True
            # Pour un trajet entre femmes, vérifier si l'utilisatrice est bien une femme
            user_id = update.effective_user.id
            db = get_db()
            user = db.query(User).filter_by(telegram_id=user_id).first()
            
            if user and user.gender == 'F':
                # C'est une femme, demander si c'est en tant que conductrice ou passagère
                keyboard = [
                    [
                        InlineKeyboardButton("🚗 Conductrice", callback_data="women:driver"),
                        InlineKeyboardButton("👥 Passagère", callback_data="women:passenger")
                    ],
                    [InlineKeyboardButton("❌ Annuler", callback_data="women:cancel")]
                ]
                try:
                    await query.edit_message_text(
                        "👩 *Trajet entre femmes*\n\n"
                        "Êtes-vous conductrice ou passagère pour ce trajet?",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Impossible d'éditer le message pour femmes: {e}")
                    await query.message.reply_text(
                        "👩 *Trajet entre femmes*\n\n"
                        "Êtes-vous conductrice ou passagère pour ce trajet?",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.MARKDOWN
                    )
                return "WOMEN_ROLE"
            else:
                # Ce n'est pas une femme ou le genre n'est pas défini
                keyboard = [
                    [InlineKeyboardButton("✅ Compléter mon profil", callback_data="complete_profile")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="back_to_trip_type")]
                ]
                try:
                    await query.edit_message_text(
                        "⚠️ *Trajet entre femmes*\n\n"
                        "Ce type de trajet est réservé aux utilisatrices ayant "
                        "indiqué leur genre dans leur profil.\n\n"
                        "Veuillez compléter votre profil avant de continuer.",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Impossible d'éditer le message de vérification femme: {e}")
                    await query.message.reply_text(
                        "⚠️ *Trajet entre femmes*\n\n"
                        "Ce type de trajet est réservé aux utilisatrices ayant "
                        "indiqué leur genre dans leur profil.\n\n"
                        "Veuillez compléter votre profil avant de continuer.",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.MARKDOWN
                    )
                return "WOMEN_ONLY_CHECK"
        
        # Cas par défaut si le type n'est pas reconnu mais valide
        return "CANCEL"
    
    except Exception as e:
        logger.error(f"❌ ERREUR dans handle_trip_type_selection: {e}", exc_info=True)
        try:
            await query.edit_message_text("❌ Une erreur s'est produite. Veuillez réessayer.")
        except Exception as edit_error:
            logger.error(f"❌ Erreur lors de l'édition du message après exception: {edit_error}")
            # Envoyer un nouveau message si l'édition échoue
            try:
                await query.message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer.")
            except Exception as reply_error:
                logger.error(f"❌ Erreur critique, impossible d'envoyer un message d'erreur: {reply_error}")
        return "CANCEL"

def format_trip_summary(trip_data: Dict[str, Any]) -> str:
    """
    Formate un résumé du trajet à partir des données.
    
    Args:
        trip_data: Dictionnaire contenant les données du trajet
        
    Returns:
        Texte formaté avec le résumé du trajet
    """
    # Déterminer s'il s'agit d'un trajet conducteur ou passager
    is_driver = trip_data.get('trip_type') == 'driver'
    role_emoji = "🚗" if is_driver else "👥"
    role_text = "Conducteur" if is_driver else "Passager"
    
    # Formater la date et l'heure
    departure_date = trip_data.get('selected_datetime')
    date_str = departure_date.strftime('%d/%m/%Y à %H:%M') if departure_date else "Non définie"
    
    # Construire le résumé
    summary = [
        f"{role_emoji} *Trajet en tant que {role_text}*",
        "",
        f"🏙️ *Départ:* {trip_data.get('departure', 'Non défini')}",
        f"🏙️ *Arrivée:* {trip_data.get('arrival', 'Non défini')}",
        f"📅 *Date:* {date_str}",
    ]
    
    # Ajouter les informations spécifiques au conducteur
    if is_driver:
        seats = trip_data.get('seats', 0)
        price = trip_data.get('price', 0)
        
        summary.extend([
            f"👥 *Places:* {seats}",
            f"💰 *Prix par place:* {price} CHF"
        ])
        
        # Calcul de la commission
        if price:
            commission = price * 0.12  # 12% de commission
            driver_receives = price - commission
            summary.append(f"💸 *Vous recevrez:* {driver_receives:.2f} CHF par passager")
    
    # Ajouter les préférences si présentes
    preferences = trip_data.get('trip_preferences', {})
    if preferences:
        summary.append("")
        summary.append("🔧 *Préférences:*")
        
        from handlers.preferences.trip_preferences_handler import PREFERENCES
        for pref_id, option_id in preferences.items():
            if pref_id in PREFERENCES:
                pref_data = PREFERENCES[pref_id]
                option_label = next(
                    (option['label'] for option in pref_data['options'] if option['id'] == option_id),
                    "Non défini"
                )
                summary.append(f"  ✓ {pref_data['name']}: {option_label}")
    
    # Ajouter les informations supplémentaires
    additional_info = trip_data.get('additional_info')
    if additional_info:
        summary.append("")
        summary.append(f"📝 *Informations:* {additional_info}")
    
    # Ajouter des balises spéciales
    if trip_data.get('is_regular'):
        summary.append("")
        summary.append("🔄 Ce trajet est régulier (hebdomadaire)")
    
    if trip_data.get('women_only'):
        summary.append("")
        summary.append("👩 Ce trajet est réservé aux femmes")
    
    return "\n".join(summary)

async def show_trip_summary(update: Update, context: CallbackContext, next_state: str):
    """
    Affiche un résumé du trajet avec des options pour confirmer ou modifier.
    
    Args:
        update: Update Telegram
        context: Contexte de la conversation
        next_state: État suivant après confirmation
        
    Returns:
        État suivant dans la conversation
    """
    query = None
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    
    # Récupérer les données du trajet
    trip_data = context.user_data
    
    # Formater le résumé
    summary = format_trip_summary(trip_data)
    
    # Clavier pour confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmer", callback_data="trip:confirm"),
            InlineKeyboardButton("✏️ Modifier", callback_data="trip:edit")
        ],
        [InlineKeyboardButton("❌ Annuler", callback_data="trip:cancel")]
    ]
    
    # Envoyer le message
    if query:
        await query.edit_message_text(
            f"📋 *Résumé du trajet*\n\n{summary}\n\n"
            "Veuillez vérifier les informations et confirmer.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            f"📋 *Résumé du trajet*\n\n{summary}\n\n"
            "Veuillez vérifier les informations et confirmer.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Stocker l'état suivant dans le contexte
    context.user_data['next_state_after_confirm'] = next_state
    
    return "CONFIRMING_TRIP"

async def handle_trip_confirmation(update: Update, context: CallbackContext):
    """
    Gère la confirmation ou modification d'un trajet.
    
    Args:
        update: Update Telegram
        context: Contexte de la conversation
        
    Returns:
        État suivant dans la conversation
    """
    query = update.callback_query
    await query.answer()
    
    # Extraire l'action
    _, action = query.data.split(':', 1)
    
    if action == "confirm":
        # Récupérer l'état suivant stocké
        next_state = context.user_data.get('next_state_after_confirm', "END")
        
        # Confirmer le trajet
        await query.edit_message_text(
            "✅ *Trajet confirmé!*\n\n"
            "Votre trajet a été créé avec succès.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Passer à l'état suivant
        return next_state
    
    elif action == "edit":
        # Afficher les options de modification
        keyboard = [
            [InlineKeyboardButton("🏙️ Départ", callback_data="edit:departure")],
            [InlineKeyboardButton("🏙️ Arrivée", callback_data="edit:arrival")],
            [InlineKeyboardButton("📅 Date et heure", callback_data="edit:datetime")]
        ]
        
        # Ajouter les boutons spécifiques au conducteur/passager
        if context.user_data.get('trip_type') == 'driver':
            keyboard.extend([
                [InlineKeyboardButton("👥 Nombre de places", callback_data="edit:seats")],
                [InlineKeyboardButton("💰 Prix", callback_data="edit:price")]
            ])
        
        # Bouton pour les préférences
        keyboard.append([InlineKeyboardButton("🔧 Préférences", callback_data="edit:preferences")])
        
        # Bouton pour les informations supplémentaires
        keyboard.append([InlineKeyboardButton("📝 Informations", callback_data="edit:info")])
        
        # Bouton pour revenir au résumé
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="edit:back")])
        
        await query.edit_message_text(
            "✏️ *Modifier le trajet*\n\n"
            "Que souhaitez-vous modifier?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "EDITING_TRIP"
    
    elif action == "cancel":
        # Annuler la création du trajet
        await query.edit_message_text(
            "❌ Création de trajet annulée.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "CANCEL"
    
    else:
        # Action non reconnue
        await query.edit_message_text("❌ Action non valide.")
        return "CANCEL"

async def handle_edit_selection(update: Update, context: CallbackContext):
    """
    Gère la sélection d'un élément à éditer.
    
    Args:
        update: Update Telegram
        context: Contexte de la conversation
        
    Returns:
        État suivant dans la conversation
    """
    query = update.callback_query
    await query.answer()
    
    # Extraire l'élément à éditer
    _, edit_item = query.data.split(':', 1)
    
    if edit_item == "back":
        # Revenir au résumé du trajet
        next_state = context.user_data.get('next_state_after_confirm', "END")
        return await show_trip_summary(update, context, next_state)
    
    # Stocker l'élément à éditer
    context.user_data['editing_item'] = edit_item
    
    # Gérer chaque type d'élément
    if edit_item == "departure":
        # Éditer le lieu de départ
        from utils.location_picker import start_location_selection
        return await start_location_selection(
            update, context, 
            "departure", 
            "🏙️ Sélectionnez une nouvelle ville de départ:"
        )
    
    elif edit_item == "arrival":
        # Éditer le lieu d'arrivée
        from utils.location_picker import start_location_selection
        return await start_location_selection(
            update, context, 
            "arrival", 
            "🏙️ Sélectionnez une nouvelle ville d'arrivée:"
        )
    
    elif edit_item == "datetime":
        # Éditer la date et l'heure
        from utils.date_picker import start_date_selection
        return await start_date_selection(
            update, context,
            "📅 Sélectionnez une nouvelle date pour votre trajet:"
        )
    
    elif edit_item == "seats":
        # Éditer le nombre de places
        keyboard = []
        for i in range(1, 9):
            keyboard.append([InlineKeyboardButton(str(i), callback_data=f"seats:{i}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="seats:back")])
        
        await query.edit_message_text(
            "👥 Sélectionnez le nombre de places disponibles:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return "EDITING_SEATS"
    
    elif edit_item == "price":
        # Éditer le prix
        await query.edit_message_text(
            "💰 Entrez le nouveau prix par place (en CHF):"
        )
        
        return "EDITING_PRICE"
    
    elif edit_item == "preferences":
        # Éditer les préférences
        from handlers.preferences.trip_preferences_handler import show_preferences_menu
        return await show_preferences_menu(update, context)
    
    elif edit_item == "info":
        # Éditer les informations supplémentaires
        await query.edit_message_text(
            "📝 Entrez les informations supplémentaires pour ce trajet:"
        )
        
        return "EDITING_INFO"
    
    else:
        # Élément non reconnu
        await query.edit_message_text("❌ Élément à éditer non valide.")
        return "CANCEL"

# États pour le module commun
common_states = {
    "CONFIRMING_TRIP": [
        CallbackQueryHandler(handle_trip_confirmation, pattern=r"^trip:(confirm|edit|cancel)$")
    ],
    "EDITING_TRIP": [
        CallbackQueryHandler(handle_edit_selection, pattern=r"^edit:.+$")
    ]
}
