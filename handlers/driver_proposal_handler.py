#!/usr/bin/env python
"""
Handler pour la gestion des propositions de conducteurs aux demandes de passagers.
Ce module gère:
- L'affichage des demandes de trajets des passagers
- Les propositions de conducteurs
- L'acceptation/refus des propositions
- L'intégration         keyboard = [
            [InlineKeyboardButton("💳 Réserver avec PayPal", url=payment_button_url)] if payment_button_url else [],
            [InlineKeyboardButton("✅ Accepter", callback_data=f"accept_proposal:{proposal.id}")],
            [InlineKeyboardButton("❌ Refuser", callback_data=f"reject_proposal:{proposal.id}")],
            [InlineKeyboardButton("📋 Voir détails", callback_data=f"view_proposal:{proposal.id}")]
        ]
        
        # Supprimer les listes vides
        keyboard = [row for row in keyboard if row]e système de paiement existant
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from database.models import Trip, User, DriverProposal, Booking
from database import get_db

logger = logging.getLogger(__name__)

# États de conversation pour les propositions
(
    PROPOSAL_MESSAGE,
    PROPOSAL_PRICE,
    PROPOSAL_CAR_INFO,
    PROPOSAL_PICKUP,
    PROPOSAL_CONFIRM
) = range(5)

async def show_passenger_trips(update: Update, context: CallbackContext):
    """Affiche les options pour voir les demandes de trajets des passagers."""
    query = update.callback_query
    await query.answer()
    
    # Proposer les deux options : vue rapide ou recherche avancée
    keyboard = [
        [InlineKeyboardButton("⚡ Vue rapide - Dernières demandes", callback_data="view_quick_passenger_trips")],
        [InlineKeyboardButton("🔍 Recherche avancée - Par canton et date", callback_data="search_passengers")],
        [InlineKeyboardButton("🔙 Retour au menu", callback_data="menu:back_to_main")]
    ]
    
    await query.edit_message_text(
        "🚗 **Demandes de passagers**\n\n"
        "Comment souhaitez-vous rechercher des passagers ?\n\n"
        "⚡ **Vue rapide** : Voir les 10 dernières demandes\n"
        "🔍 **Recherche avancée** : Filtrer par canton, date et heure\n\n"
        "Choisissez votre méthode préférée :",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_quick_passenger_trips(update: Update, context: CallbackContext):
    """Affiche rapidement les dernières demandes de trajets des passagers."""
    query = update.callback_query
    await query.answer()
    
    logger.info("🔥 Vue rapide appelée - Affichage des dernières demandes de passagers")
    
    db = get_db()
    user_id = update.effective_user.id
    
    try:
        # Récupérer les demandes de trajets de passagers (trip_role = 'passenger')
        passenger_trips = db.query(Trip).filter(
            Trip.trip_role == 'passenger',
            Trip.is_published == True,
            Trip.departure_time > datetime.now(),  # Trajets futurs seulement
            Trip.driver_id.is_(None)  # Pas encore de conducteur assigné
        ).order_by(Trip.departure_time).limit(10).all()
        
        logger.info(f"🔥 Nombre de demandes trouvées: {len(passenger_trips)}")
        
        if not passenger_trips:
            logger.info("🔥 Aucune demande trouvée - Affichage du message vide")
            await query.edit_message_text(
                "🔍 **Aucune demande de trajet disponible**\n\n"
                "Il n'y a actuellement aucune demande de passager dans votre région.\n"
                "Revenez plus tard pour voir de nouvelles demandes !\n\n"
                "💡 **Conseil** : Essayez la recherche avancée pour explorer d'autres cantons.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Recherche avancée", callback_data="search_passengers")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="view_passenger_trips")]
                ]),
                parse_mode="Markdown"
            )
            return
    
        # Construire la liste des demandes - chaque trajet comme message séparé
        header_message = "⚡ **Vue rapide - Dernières demandes**\n\n"
        header_message += "👥 Des passagers recherchent un conducteur :\n\n"
        header_message += f"✅ **{len(passenger_trips)} demande(s) trouvée(s)**"
        
        # Envoyer le message d'en-tête
        await query.edit_message_text(
            header_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Actualiser", callback_data="view_quick_passenger_trips")],
                [InlineKeyboardButton("🔍 Recherche avancée", callback_data="search_passengers")],
                [InlineKeyboardButton("🔙 Retour", callback_data="view_passenger_trips")]
            ]),
            parse_mode="Markdown"
        )
        
        # Envoyer chaque trajet comme un message séparé avec ses boutons
        for i, trip in enumerate(passenger_trips, 1):
            # Utiliser full_name en priorité, sinon username, sinon "Utilisateur"
            creator_name = "Utilisateur"
            if trip.creator:
                if trip.creator.full_name:
                    creator_name = trip.creator.full_name
                elif trip.creator.username:
                    creator_name = trip.creator.username
            
            date_str = trip.departure_time.strftime('%d/%m à %H:%M')
            
            trip_message = (
                f"**{i}. {trip.departure_city} → {trip.arrival_city}**\n"
                f"📅 {date_str}\n"
                f"👤 {creator_name}\n"
                f"👥 {trip.seats_available} place(s)\n"
                f"💰 {trip.price_per_seat} CHF/place"
            )
            
            # Boutons pour ce trajet spécifique
            trip_keyboard = [
                [InlineKeyboardButton("🚗 Proposer mes services", callback_data=f"propose_service:{trip.id}")],
                [InlineKeyboardButton("📋 Voir détails", callback_data=f"trip_details:{trip.id}")]
            ]
            
            # Envoyer le message du trajet avec ses boutons
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=trip_message,
                reply_markup=InlineKeyboardMarkup(trip_keyboard),
                parse_mode="Markdown"
            )
        
        logger.info("🔥 Tous les trajets individuels envoyés avec leurs boutons")
        
    except Exception as e:
        logger.error(f"🔥 Erreur dans show_quick_passenger_trips: {e}")
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de l'affichage des demandes.\n\n"
            "Veuillez réessayer plus tard.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="view_passenger_trips")]
            ])
        )
    finally:
        db.close()

async def start_service_proposal(update: Update, context: CallbackContext):
    """Démarre le processus de proposition de service pour un trajet passager."""
    query = update.callback_query
    await query.answer()
    
    trip_id = int(query.data.split(":")[1])
    context.user_data['proposal_trip_id'] = trip_id
    
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip or trip.trip_role != 'passenger':
        await query.edit_message_text(
            "❌ Cette demande de trajet n'est plus disponible.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="view_quick_passenger_trips")
            ]])
        )
        return ConversationHandler.END
    
    # Vérifier si l'utilisateur essaie de proposer ses services à son propre trajet
    user_id = update.effective_user.id
    db_user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if trip.creator_id == db_user.id:
        await query.edit_message_text(
            "❌ **Impossible de proposer vos services**\n\n"
            "Vous ne pouvez pas proposer vos services pour votre propre demande de trajet !\n\n"
            "💡 Créez plutôt une offre de trajet en tant que conducteur.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="view_quick_passenger_trips")
            ]]),
            parse_mode="Markdown"
        )
        db.close()
        return ConversationHandler.END
    
    # Vérifier si l'utilisateur a déjà fait une proposition pour ce trajet
    existing_proposal = db.query(DriverProposal).filter(
        DriverProposal.trip_id == trip_id,
        DriverProposal.driver_id == db_user.id,
        DriverProposal.status == 'pending'
    ).first()
    
    if existing_proposal:
        await query.edit_message_text(
            f"ℹ️ **Proposition déjà envoyée**\n\n"
            f"Vous avez déjà proposé vos services pour ce trajet.\n"
            f"Status: En attente de réponse du passager.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="view_quick_passenger_trips")
            ]])
        )
        return ConversationHandler.END
    
    creator_name = trip.creator.full_name if trip.creator and trip.creator.full_name else (trip.creator.username if trip.creator and trip.creator.username else "Utilisateur")
    date_str = trip.departure_time.strftime('%d/%m/%Y à %H:%M')
    
    # Créer directement la proposition sans demander de message
    proposal = DriverProposal(
        trip_id=trip_id,
        driver_id=db_user.id,
        message=f"Proposition automatique de service pour {trip.departure_city} → {trip.arrival_city}",
        proposed_price=trip.price_per_seat,  # Utiliser le prix demandé par le passager
        car_info="Véhicule disponible",  # Valeur par défaut
        pickup_point=trip.departure_city,  # Point de ramassage par défaut
        status='pending'
    )
    
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    
    logger.info(f"🚗 Nouvelle proposition ID {proposal.id} créée directement pour le trajet {trip_id}")
    
    # Notifier le passager (créateur du trajet)
    try:
        from telegram import Bot
        bot = context.bot
        
        notification_message = (
            f"🚗 **Nouvelle proposition de conducteur !**\n\n"
            f"**Votre trajet :**\n"
            f"🌍 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"**Proposition du conducteur :**\n"
            f"👤 {db_user.full_name if db_user.full_name else (db_user.username if db_user.username else 'Conducteur')}\n"
            f"💰 Prix: {proposal.proposed_price} CHF/place\n"
            f"🚙 Véhicule: {proposal.car_info}\n"
            f"� Ramassage: {proposal.pickup_point}\n\n"
        )
        
        # Créer le lien PayPal pour la réservation
        from paypal_utils import PayPalManager
        try:
            paypal_manager = PayPalManager()
            success, payment_url, error = paypal_manager.create_payment(
                amount=float(proposal.proposed_price),
                description=f"Réservation trajet {trip.departure_city} → {trip.arrival_city}",
                return_url=f"https://covoiturage.ch/payment/success/{proposal.id}",
                cancel_url=f"https://covoiturage.ch/payment/cancel/{proposal.id}"
            )
            
            if success and payment_url:
                notification_message += f"💳 **Réserver maintenant :** [Payer avec PayPal]({payment_url})\n\n"
                payment_button_url = payment_url
            else:
                logger.error(f"Erreur création lien PayPal: {error}")
                notification_message += f"💳 **Réservation :** Contactez le conducteur pour finaliser\n\n"
                payment_button_url = None
        except Exception as e:
            logger.error(f"Erreur création lien PayPal: {e}")
            notification_message += f"💳 **Réservation :** Contactez le conducteur pour finaliser\n\n"
            payment_button_url = None
        
        keyboard = [
            [InlineKeyboardButton("� Réserver avec PayPal", url=payment_url if 'payment_url' in locals() else "https://paypal.com")],
            [InlineKeyboardButton("✅ Accepter", callback_data=f"accept_proposal:{proposal.id}")],
            [InlineKeyboardButton("❌ Refuser", callback_data=f"reject_proposal:{proposal.id}")],
            [InlineKeyboardButton("📋 Voir détails", callback_data=f"view_proposal:{proposal.id}")]
        ]
        
        await bot.send_message(
            chat_id=trip.creator.telegram_id,
            text=notification_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Notification envoyée au passager ID {trip.creator.telegram_id}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification: {e}")
    
    # Confirmer au conducteur
    await query.edit_message_text(
        f"✅ **Proposition envoyée !**\n\n"
        f"**Trajet :** {trip.departure_city} → {trip.arrival_city}\n"
        f"**Date :** {date_str}\n"
        f"**Passager :** {creator_name}\n\n"
        f"Le passager a reçu votre proposition avec un lien PayPal pour réserver directement.\n"
        f"Vous serez notifié de sa réponse.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Retour aux demandes", callback_data="view_quick_passenger_trips")
        ]]),
        parse_mode="Markdown"
    )
    
    db.close()
    return ConversationHandler.END

async def handle_proposal_message(update: Update, context: CallbackContext):
    """Gère le message de présentation du conducteur."""
    message_text = update.message.text.strip()
    
    if len(message_text) < 10:
        await update.message.reply_text(
            "❌ Votre message est trop court. Veuillez écrire au moins 10 caractères pour vous présenter correctement."
        )
        return PROPOSAL_MESSAGE
    
    context.user_data['proposal_message'] = message_text
    
    trip_id = context.user_data.get('proposal_trip_id')
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    message = (
        f"🚗 **Proposition de service**\n\n"
        f"✅ Message enregistré !\n\n"
        f"**Étape 2/4** - Proposez votre prix :\n"
        f"💰 Budget du passager: {trip.price_per_seat} CHF/place\n"
        f"💡 Vous pouvez proposer le même prix ou un prix différent.\n\n"
        f"Écrivez votre prix par place (ex: 15.50) :"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Annuler", callback_data="proposal_cancel")
        ]]),
        parse_mode="Markdown"
    )
    
    return PROPOSAL_PRICE

async def handle_proposal_price(update: Update, context: CallbackContext):
    """Gère la saisie du prix proposé."""
    price_text = update.message.text.strip()
    
    try:
        price = float(price_text.replace(',', '.'))
        if price <= 0 or price > 200:
            raise ValueError("Prix invalide")
    except ValueError:
        await update.message.reply_text(
            "❌ Prix invalide. Veuillez entrer un prix valide entre 0.50 et 200 CHF (ex: 15.50)"
        )
        return PROPOSAL_PRICE
    
    context.user_data['proposal_price'] = price
    
    message = (
        f"🚗 **Proposition de service**\n\n"
        f"💰 Prix proposé: {price} CHF/place\n\n"
        f"**Étape 3/4** - Décrivez votre véhicule :\n"
        f"🚙 Marque, modèle, couleur, confort, etc.\n"
        f"💡 Cela aide le passager à vous identifier."
    )
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Annuler", callback_data="proposal_cancel")
        ]]),
        parse_mode="Markdown"
    )
    
    return PROPOSAL_CAR_INFO

async def handle_proposal_car_info(update: Update, context: CallbackContext):
    """Gère la description du véhicule."""
    car_info = update.message.text.strip()
    
    if len(car_info) < 5:
        await update.message.reply_text(
            "❌ Description trop courte. Veuillez décrire votre véhicule plus en détail."
        )
        return PROPOSAL_CAR_INFO
    
    context.user_data['proposal_car_info'] = car_info
    
    message = (
        f"🚗 **Proposition de service**\n\n"
        f"🚙 Véhicule: {car_info}\n\n"
        f"**Étape 4/4** - Point de ramassage :\n"
        f"📍 Où proposez-vous de récupérer le passager ?\n"
        f"💡 Soyez précis (adresse, point de repère, etc.)"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Annuler", callback_data="proposal_cancel")
        ]]),
        parse_mode="Markdown"
    )
    
    return PROPOSAL_PICKUP

async def handle_proposal_pickup(update: Update, context: CallbackContext):
    """Gère le point de ramassage."""
    pickup_point = update.message.text.strip()
    
    if len(pickup_point) < 5:
        await update.message.reply_text(
            "❌ Point de ramassage trop vague. Veuillez être plus précis."
        )
        return PROPOSAL_PICKUP
    
    context.user_data['proposal_pickup'] = pickup_point
    
    # Récapitulatif
    trip_id = context.user_data.get('proposal_trip_id')
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    creator_name = trip.creator.full_name if trip.creator and trip.creator.full_name else (trip.creator.username if trip.creator and trip.creator.username else "Utilisateur")
    
    message = (
        f"🚗 **Récapitulatif de votre proposition**\n\n"
        f"**Trajet demandé :**\n"
        f"🌍 {trip.departure_city} → {trip.arrival_city}\n"
        f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
        f"👤 Passager: {creator_name}\n\n"
        f"**Votre proposition :**\n"
        f"💭 Message: {context.user_data['proposal_message'][:100]}{'...' if len(context.user_data['proposal_message']) > 100 else ''}\n"
        f"💰 Prix: {context.user_data['proposal_price']} CHF/place\n"
        f"🚙 Véhicule: {context.user_data['proposal_car_info']}\n"
        f"📍 Ramassage: {pickup_point}\n\n"
        f"Confirmez-vous l'envoi de cette proposition ?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Envoyer la proposition", callback_data="proposal_confirm")],
        [InlineKeyboardButton("❌ Annuler", callback_data="proposal_cancel")]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return PROPOSAL_CONFIRM

async def confirm_proposal(update: Update, context: CallbackContext):
    """Confirme et envoie la proposition au passager."""
    query = update.callback_query
    await query.answer()
    
    try:
        db = get_db()
        user_id = update.effective_user.id
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        trip_id = context.user_data.get('proposal_trip_id')
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet introuvable.")
            return ConversationHandler.END
        
        # Créer la proposition en base
        proposal = DriverProposal(
            trip_id=trip_id,
            driver_id=db_user.id,
            message=context.user_data['proposal_message'],
            proposed_price=context.user_data['proposal_price'],
            car_info=context.user_data['proposal_car_info'],
            pickup_point=context.user_data['proposal_pickup'],
            status='pending'
        )
        
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        
        logger.info(f"Nouvelle proposition ID {proposal.id} créée pour le trajet {trip_id}")
        
        # Notifier le passager (créateur du trajet)
        try:
            from telegram import Bot
            bot = context.bot
            
            notification_message = (
                f"🚗 **Nouvelle proposition de conducteur !**\n\n"
                f"**Votre trajet :**\n"
                f"🌍 {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                f"**Proposition du conducteur :**\n"
                f"👤 {db_user.full_name if db_user.full_name else (db_user.username if db_user.username else 'Conducteur')}\n"
                f"💰 Prix: {proposal.proposed_price} CHF/place\n"
                f"🚙 Véhicule: {proposal.car_info}\n"
                f"📍 Ramassage: {proposal.pickup_point}\n\n"
                f"💭 **Message:** {proposal.message}"
            )
            
            keyboard = [
                [InlineKeyboardButton("✅ Accepter", callback_data=f"accept_proposal:{proposal.id}")],
                [InlineKeyboardButton("❌ Refuser", callback_data=f"reject_proposal:{proposal.id}")],
                [InlineKeyboardButton("📋 Voir détails", callback_data=f"view_proposal:{proposal.id}")]
            ]
            
            await bot.send_message(
                chat_id=trip.creator.telegram_id,
                text=notification_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
        
        # Confirmer au conducteur
        await query.edit_message_text(
            f"✅ **Proposition envoyée avec succès !**\n\n"
            f"Votre proposition a été transmise au passager.\n"
            f"Vous recevrez une notification quand il répondra.\n\n"
            f"💡 **Conseil:** Restez disponible sur Telegram pour répondre rapidement !",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voir d'autres demandes", callback_data="view_passenger_trips"),
                InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")
            ]]),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de proposition: {e}")
        await query.edit_message_text("❌ Une erreur est survenue. Veuillez réessayer.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_proposal(update: Update, context: CallbackContext):
    """Annule la création de proposition."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ Proposition annulée.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Retour aux demandes", callback_data="view_passenger_trips")
        ]])
    )
    
    context.user_data.clear()
    return ConversationHandler.END

# ConversationHandler pour les propositions de service
driver_proposal_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_service_proposal, pattern='^propose_service:\\d+$')
    ],
    states={
        PROPOSAL_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_proposal_message)
        ],
        PROPOSAL_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_proposal_price)
        ],
        PROPOSAL_CAR_INFO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_proposal_car_info)
        ],
        PROPOSAL_PICKUP: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_proposal_pickup)
        ],
        PROPOSAL_CONFIRM: [
            CallbackQueryHandler(confirm_proposal, pattern='^proposal_confirm$')
        ]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_proposal, pattern='^proposal_cancel$')
    ],
    name="driver_proposal_conversation",
    persistent=True,
    allow_reentry=True,
    per_message=False,
    per_chat=False,
    per_user=True
)

# Handler global pour afficher les demandes de passagers
view_passenger_trips_handler = CallbackQueryHandler(show_passenger_trips, pattern='^view_passenger_trips$')
view_quick_passenger_trips_handler = CallbackQueryHandler(show_quick_passenger_trips, pattern='^view_quick_passenger_trips$')

# HANDLER GLOBAL pour les boutons "Proposer mes services" (fonctionne de partout)
propose_service_handler = CallbackQueryHandler(start_service_proposal, pattern='^propose_service:\\d+$')
