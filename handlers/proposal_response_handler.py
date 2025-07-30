#!/usr/bin/env python
"""
Handler pour la gestion des réponses aux propositions de conducteurs.
Ce module gère:
- L'acceptation/refus des propositions par les passagers
- La création de réservations confirmées
- L'intégration avec le système de paiement PayPal
- Les notifications aux conducteurs
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from database.models import Trip, User, DriverProposal, Booking
from database import get_db
from paypal_utils import create_paypal_payment

logger = logging.getLogger(__name__)

async def view_proposal_details(update: Update, context: CallbackContext):
    """Affiche les détails complets d'une proposition."""
    query = update.callback_query
    await query.answer()
    
    proposal_id = int(query.data.split(":")[1])
    
    db = get_db()
    proposal = db.query(DriverProposal).filter(DriverProposal.id == proposal_id).first()
    
    if not proposal:
        await query.edit_message_text("❌ Proposition introuvable.")
        return
    
    trip = proposal.trip
    driver = proposal.driver
    
    # Calculer le prix total
    total_price = proposal.proposed_price * trip.seats_available
    
    message = (
        f"🚗 **Détails de la proposition**\n\n"
        f"**Votre demande de trajet :**\n"
        f"🌍 {trip.departure_city} → {trip.arrival_city}\n"
        f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
        f"👥 {trip.seats_available} place(s) demandée(s)\n"
        f"💰 Votre budget: {trip.price_per_seat} CHF/place\n\n"
        f"**Proposition du conducteur :**\n"
        f"👤 **{driver.first_name}**\n"
        f"📧 Contact: @{driver.username if driver.username else 'Non renseigné'}\n"
        f"💰 **Prix proposé: {proposal.proposed_price} CHF/place**\n"
        f"💵 **Total: {total_price} CHF** ({trip.seats_available} place(s))\n"
        f"🚙 **Véhicule:** {proposal.car_info}\n"
        f"📍 **Point de ramassage:** {proposal.pickup_point}\n\n"
        f"💭 **Message du conducteur:**\n"
        f"_{proposal.message}_\n\n"
        f"📱 **Prochaines étapes si vous acceptez:**\n"
        f"1. Confirmation de la réservation\n"
        f"2. Paiement sécurisé via PayPal\n"
        f"3. Échange de contacts avec le conducteur\n"
        f"4. Trajet confirmé !"
    )
    
    keyboard = []
    
    if proposal.status == 'pending':
        keyboard.extend([
            [InlineKeyboardButton("✅ Accepter cette proposition", callback_data=f"accept_proposal:{proposal_id}")],
            [InlineKeyboardButton("❌ Refuser poliment", callback_data=f"reject_proposal:{proposal_id}")]
        ])
    else:
        status_text = {
            'accepted': '✅ Proposition acceptée',
            'rejected': '❌ Proposition refusée',
            'paid': '💳 Paiement effectué'
        }.get(proposal.status, proposal.status)
        keyboard.append([InlineKeyboardButton(f"📊 Status: {status_text}", callback_data="noop")])
    
    keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="main_menu:start")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def accept_proposal(update: Update, context: CallbackContext):
    """Accepte une proposition de conducteur et déclenche le processus de paiement."""
    query = update.callback_query
    await query.answer()
    
    proposal_id = int(query.data.split(":")[1])
    user_id = update.effective_user.id
    
    db = get_db()
    proposal = db.query(DriverProposal).filter(DriverProposal.id == proposal_id).first()
    
    if not proposal:
        await query.edit_message_text("❌ Proposition introuvable.")
        return
    
    trip = proposal.trip
    driver = proposal.driver
    passenger = db.query(User).filter(User.telegram_id == user_id).first()
    
    # Vérifications de sécurité
    if proposal.status != 'pending':
        await query.edit_message_text(
            f"❌ Cette proposition a déjà été traitée (Status: {proposal.status})."
        )
        return
    
    if trip.creator_id != passenger.id:
        await query.edit_message_text("❌ Vous n'êtes pas autorisé à accepter cette proposition.")
        return
    
    # Vérifier si le trajet n'a pas déjà un conducteur assigné
    if trip.driver_id is not None:
        await query.edit_message_text("❌ Ce trajet a déjà un conducteur assigné.")
        return
    
    try:
        # Calculer le montant total
        total_amount = proposal.proposed_price * trip.seats_available
        
        # Créer le paiement PayPal
        payment_url = create_paypal_payment(
            amount=total_amount,
            description=f"Covoiturage {trip.departure_city} → {trip.arrival_city}",
            user_id=passenger.telegram_id,
            trip_id=trip.id,
            proposal_id=proposal_id
        )
        
        if not payment_url:
            raise Exception("Impossible de créer le paiement PayPal")
        
        # Mettre à jour le statut de la proposition
        proposal.status = 'accepted'
        proposal.accepted_at = datetime.now()
        
        # Créer une réservation temporaire (sera confirmée après paiement)
        booking = Booking(
            trip_id=trip.id,
            passenger_id=passenger.id,
            seats_booked=trip.seats_available,
            total_price=total_amount,
            booking_status='pending_payment',
            payment_status='pending'
        )
        
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        logger.info(f"Proposition {proposal_id} acceptée, réservation {booking.id} créée")
        
        # Message de confirmation avec lien de paiement
        confirmation_message = (
            f"✅ **Proposition acceptée !**\n\n"
            f"**Détails du trajet :**\n"
            f"🚗 Conducteur: {driver.first_name}\n"
            f"🌍 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"👥 {trip.seats_available} place(s)\n"
            f"💰 **Total à payer: {total_amount} CHF**\n\n"
            f"🔒 **Paiement sécurisé requis**\n"
            f"Cliquez sur le bouton ci-dessous pour finaliser votre réservation avec PayPal.\n\n"
            f"⚡ **Important:** Votre réservation sera confirmée uniquement après le paiement."
        )
        
        keyboard = [
            [InlineKeyboardButton("💳 Payer avec PayPal", url=payment_url)],
            [InlineKeyboardButton("📋 Voir ma réservation", callback_data=f"view_booking:{booking.id}")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
        ]
        
        await query.edit_message_text(
            confirmation_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Notifier le conducteur de l'acceptation
        try:
            driver_notification = (
                f"🎉 **Votre proposition a été acceptée !**\n\n"
                f"**Trajet :**\n"
                f"🌍 {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                f"👤 Passager: {passenger.first_name}\n"
                f"👥 {trip.seats_available} place(s)\n"
                f"💰 Montant: {total_amount} CHF\n\n"
                f"⏳ **En attente du paiement**\n"
                f"Le passager finalise actuellement son paiement. Vous recevrez une confirmation dès que c'est fait.\n\n"
                f"📱 Préparez-vous à être contacté pour organiser le ramassage !"
            )
            
            await context.bot.send_message(
                chat_id=driver.telegram_id,
                text=driver_notification,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification au conducteur: {e}")
        
        # Rejeter automatiquement les autres propositions pour ce trajet
        other_proposals = db.query(DriverProposal).filter(
            DriverProposal.trip_id == trip.id,
            DriverProposal.id != proposal_id,
            DriverProposal.status == 'pending'
        ).all()
        
        for other_proposal in other_proposals:
            other_proposal.status = 'rejected'
            other_proposal.rejected_at = datetime.now()
            
            # Notifier les autres conducteurs
            try:
                rejection_message = (
                    f"😔 **Proposition non retenue**\n\n"
                    f"Votre proposition pour le trajet {trip.departure_city} → {trip.arrival_city} "
                    f"du {trip.departure_time.strftime('%d/%m à %H:%M')} n'a pas été retenue.\n\n"
                    f"Le passager a choisi une autre option.\n"
                    f"Ne vous découragez pas ! D'autres opportunités vous attendent."
                )
                
                await context.bot.send_message(
                    chat_id=other_proposal.driver.telegram_id,
                    text=rejection_message,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔍 Voir d'autres demandes", callback_data="view_passenger_trips")
                    ]]),
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de notification de rejet: {e}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Erreur lors de l'acceptation de proposition: {e}")
        db.rollback()
        await query.edit_message_text(
            "❌ Une erreur est survenue lors du traitement de votre acceptation. Veuillez réessayer."
        )

async def reject_proposal(update: Update, context: CallbackContext):
    """Refuse poliment une proposition de conducteur."""
    query = update.callback_query
    await query.answer()
    
    proposal_id = int(query.data.split(":")[1])
    user_id = update.effective_user.id
    
    db = get_db()
    proposal = db.query(DriverProposal).filter(DriverProposal.id == proposal_id).first()
    
    if not proposal:
        await query.edit_message_text("❌ Proposition introuvable.")
        return
    
    trip = proposal.trip
    driver = proposal.driver
    passenger = db.query(User).filter(User.telegram_id == user_id).first()
    
    # Vérifications de sécurité
    if proposal.status != 'pending':
        await query.edit_message_text(
            f"❌ Cette proposition a déjà été traitée (Status: {proposal.status})."
        )
        return
    
    if trip.creator_id != passenger.id:
        await query.edit_message_text("❌ Vous n'êtes pas autorisé à traiter cette proposition.")
        return
    
    try:
        # Mettre à jour le statut de la proposition
        proposal.status = 'rejected'
        proposal.rejected_at = datetime.now()
        db.commit()
        
        logger.info(f"Proposition {proposal_id} refusée par le passager")
        
        # Confirmer au passager
        await query.edit_message_text(
            f"❌ **Proposition refusée**\n\n"
            f"Vous avez poliment décliné la proposition de {driver.first_name}.\n\n"
            f"💡 **Conseil:** Votre demande reste active. D'autres conducteurs peuvent encore vous proposer leurs services !",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Voir mes demandes", callback_data="my_trips")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu:start")]
            ]),
            parse_mode="Markdown"
        )
        
        # Notifier le conducteur du refus
        try:
            rejection_message = (
                f"😔 **Proposition déclinée**\n\n"
                f"Le passager a décliné votre proposition pour le trajet "
                f"{trip.departure_city} → {trip.arrival_city} du {trip.departure_time.strftime('%d/%m à %H:%M')}.\n\n"
                f"Ne vous découragez pas ! Il y a de nombreuses autres opportunités disponibles."
            )
            
            await context.bot.send_message(
                chat_id=driver.telegram_id,
                text=rejection_message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Voir d'autres demandes", callback_data="view_passenger_trips")
                ]]),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification de rejet: {e}")
        
    except Exception as e:
        logger.error(f"Erreur lors du refus de proposition: {e}")
        db.rollback()
        await query.edit_message_text(
            "❌ Une erreur est survenue lors du traitement de votre refus. Veuillez réessayer."
        )

async def view_booking_details(update: Update, context: CallbackContext):
    """Affiche les détails d'une réservation."""
    query = update.callback_query
    await query.answer()
    
    booking_id = int(query.data.split(":")[1])
    user_id = update.effective_user.id
    
    db = get_db()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        await query.edit_message_text("❌ Réservation introuvable.")
        return
    
    trip = booking.trip
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    # Vérifier que l'utilisateur a accès à cette réservation
    if booking.passenger_id != user.id:
        await query.edit_message_text("❌ Vous n'avez pas accès à cette réservation.")
        return
    
    # Déterminer le statut et les actions disponibles
    status_emoji = {
        'pending_payment': '⏳',
        'confirmed': '✅',
        'cancelled': '❌',
        'completed': '🎉'
    }.get(booking.booking_status, '❓')
    
    status_text = {
        'pending_payment': 'En attente de paiement',
        'confirmed': 'Confirmée',
        'cancelled': 'Annulée',
        'completed': 'Terminée'
    }.get(booking.booking_status, booking.booking_status)
    
    payment_status_emoji = {
        'pending': '⏳',
        'completed': '✅',
        'failed': '❌',
        'refunded': '↩️'
    }.get(booking.payment_status, '❓')
    
    message = (
        f"📋 **Détails de votre réservation**\n\n"
        f"**Trajet :**\n"
        f"🌍 {trip.departure_city} → {trip.arrival_city}\n"
        f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
        f"👥 {booking.seats_booked} place(s)\n"
        f"💰 Total: {booking.total_price} CHF\n\n"
        f"**Status :**\n"
        f"{status_emoji} Réservation: {status_text}\n"
        f"{payment_status_emoji} Paiement: {booking.payment_status}\n\n"
    )
    
    keyboard = []
    
    if booking.booking_status == 'pending_payment':
        message += (
            f"⚡ **Action requise**\n"
            f"Votre réservation sera confirmée dès que le paiement sera finalisé.\n\n"
            f"💡 Si vous avez des difficultés avec le paiement, contactez le support."
        )
        keyboard.append([InlineKeyboardButton("💳 Finaliser le paiement", callback_data=f"retry_payment:{booking_id}")])
    
    elif booking.booking_status == 'confirmed':
        # Trouver le conducteur via la proposition acceptée
        accepted_proposal = db.query(DriverProposal).filter(
            DriverProposal.trip_id == trip.id,
            DriverProposal.status == 'accepted'
        ).first()
        
        if accepted_proposal:
            driver = accepted_proposal.driver
            message += (
                f"🚗 **Conducteur confirmé :**\n"
                f"👤 {driver.first_name}\n"
                f"📧 Contact: @{driver.username if driver.username else 'Demander au support'}\n"
                f"🚙 Véhicule: {accepted_proposal.car_info}\n"
                f"📍 Ramassage: {accepted_proposal.pickup_point}\n\n"
                f"📱 **Prochaines étapes :**\n"
                f"1. Contactez votre conducteur pour confirmer l'heure et le lieu\n"
                f"2. Soyez ponctuel au point de ramassage\n"
                f"3. Bon voyage ! 🚗💨"
            )
            keyboard.append([InlineKeyboardButton("💬 Contacter le conducteur", url=f"https://t.me/{driver.username}" if driver.username else "https://t.me/CovoiturageSwissBot")])
    
    keyboard.extend([
        [InlineKeyboardButton("🔄 Actualiser", callback_data=f"view_booking:{booking_id}")],
        [InlineKeyboardButton("🔙 Retour", callback_data="my_trips")]
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Handlers pour les réponses aux propositions
proposal_response_handlers = [
    CallbackQueryHandler(view_proposal_details, pattern='^view_proposal:\\d+$'),
    CallbackQueryHandler(accept_proposal, pattern='^accept_proposal:\\d+$'),
    CallbackQueryHandler(reject_proposal, pattern='^reject_proposal:\\d+$'),
    CallbackQueryHandler(view_booking_details, pattern='^view_booking:\\d+$')
]
