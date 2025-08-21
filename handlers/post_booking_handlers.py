#!/usr/bin/env python3
"""
Handlers pour la communication post-réservation
Gère les interactions entre conducteur et passager après une réservation payée
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database.models import Booking, Trip, User
from database import get_db
from passenger_refund_manager import process_passenger_refund
import logging

logger = logging.getLogger(__name__)

async def handle_contact_driver(update: Update, context: CallbackContext):
    """Gère le contact avec le conducteur"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(':')[1])
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip or not trip.driver:
            await query.edit_message_text("❌ Conducteur non trouvé")
            return
        
        driver = trip.driver
        contact_info = []
        
        if driver.username:
            contact_info.append(f"Telegram: @{driver.username}")
        if driver.phone:
            contact_info.append(f"Téléphone: {driver.phone}")
        if driver.telegram_id:
            contact_info.append(f"Vous pouvez lui écrire directement via ce bot")
        
        contact_text = "\n".join(contact_info) if contact_info else "Aucune information de contact disponible"
        
        # Bouton pour envoyer un message direct
        keyboard = [
            [InlineKeyboardButton("💬 Envoyer un message", callback_data=f"send_message_driver:{trip_id}")],
            [InlineKeyboardButton("🔙 Retour réservations", callback_data="profile:my_bookings")]
        ]
        
        message = (
            f"👤 **Contact Conducteur**\n\n"
            f"**Nom:** {driver.full_name or driver.username or 'Non renseigné'}\n"
            f"**Contact:**\n{contact_text}\n\n"
            f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}"
        )
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur contact_driver: {e}")
        await query.edit_message_text("❌ Erreur lors de la récupération des informations")

async def handle_contact_passenger(update: Update, context: CallbackContext):
    """Gère le contact avec le passager"""
    query = update.callback_query
    await query.answer()
    
    try:
        booking_id = int(query.data.split(':')[1])
        db = get_db()
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking or not booking.passenger:
            await query.edit_message_text("❌ Passager non trouvé")
            return
        
        passenger = booking.passenger
        contact_info = []
        
        if passenger.username:
            contact_info.append(f"Telegram: @{passenger.username}")
        if passenger.phone:
            contact_info.append(f"Téléphone: {passenger.phone}")
        if passenger.telegram_id:
            contact_info.append(f"Vous pouvez lui écrire directement via ce bot")
        
        contact_text = "\n".join(contact_info) if contact_info else "Aucune information de contact disponible"
        
        # Bouton pour envoyer un message direct
        keyboard = [
            [InlineKeyboardButton("💬 Envoyer un message", callback_data=f"send_message_passenger:{booking_id}")],
            [InlineKeyboardButton("🔙 Retour", callback_data=f"trip_details:{booking.trip_id}")]
        ]
        
        message = (
            f"👤 **Contact Passager**\n\n"
            f"**Nom:** {passenger.full_name or passenger.username or 'Non renseigné'}\n"
            f"**Contact:**\n{contact_text}\n\n"
            f"💰 **Montant payé:** {booking.total_price:.2f} CHF\n"
            f"📅 **Réservation:** #{booking_id}"
        )
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur contact_passenger: {e}")
        await query.edit_message_text("❌ Erreur lors de la récupération des informations")

async def handle_meeting_point(update: Update, context: CallbackContext):
    """Gère la définition du point de rendez-vous"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(':')[1])
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé")
            return
        
        # Pour l'instant, point de RDV basique
        keyboard = [
            [InlineKeyboardButton("📍 Gare de départ", callback_data=f"rdv_station:{trip_id}")],
            [InlineKeyboardButton("🏢 Centre-ville", callback_data=f"rdv_center:{trip_id}")],
            [InlineKeyboardButton("✏️ Autre lieu (message)", callback_data=f"rdv_custom:{trip_id}")],
            [InlineKeyboardButton("🔙 Retour réservations", callback_data="profile:my_bookings")]
        ]
        
        message = (
            f"📍 **Point de Rendez-vous**\n\n"
            f"**Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
            f"**Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Où souhaitez-vous vous retrouver ?"
        )
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur meeting_point: {e}")
        await query.edit_message_text("❌ Erreur lors de la gestion du point de RDV")

async def handle_cancel_booking_with_refund(update: Update, context: CallbackContext):
    """Gère l'annulation avec remboursement automatique"""
    query = update.callback_query
    await query.answer()
    
    try:
        logger.info(f"🔥 ANNULATION: callback_data = {query.data}")
        booking_id = int(query.data.split(':')[1])
        logger.info(f"🔥 ANNULATION: booking_id = {booking_id}")
        
        db = get_db()
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        logger.info(f"🔥 ANNULATION: booking trouvé = {booking is not None}")
        
        if not booking:
            await query.edit_message_text("❌ Réservation non trouvée")
            return
        
        logger.info(f"🔥 ANNULATION: booking.status = {booking.status}")
        logger.info(f"🔥 ANNULATION: booking.trip = {booking.trip is not None}")
        
        if booking.status == 'cancelled':
            await query.edit_message_text("❌ Cette réservation est déjà annulée")
            return
        
        # Vérifier les données du booking
        if not booking.trip:
            await query.edit_message_text("❌ Données de réservation incomplètes (trajet manquant)")
            return
            
        if not hasattr(booking, 'total_price') or booking.total_price is None:
            # Utiliser amount si total_price n'existe pas
            price = getattr(booking, 'amount', 0) or 0
        else:
            price = booking.total_price
        
        # Confirmation d'annulation
        keyboard = [
            [InlineKeyboardButton("✅ Confirmer l'annulation", callback_data=f"confirm_cancel:{booking_id}")],
            [InlineKeyboardButton("❌ Garder ma réservation", callback_data=f"trip_details:{booking.trip_id}")]
        ]
        
        message = (
            f"⚠️ **Confirmer l'annulation ?**\n\n"
            f"**Réservation:** #{booking_id}\n"
            f"**Trajet:** {booking.trip.departure_city} → {booking.trip.arrival_city}\n"
            f"**Date:** {booking.trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"**Montant:** {price:.2f} CHF\n\n"
            f"💰 **Remboursement automatique:** Vous serez remboursé intégralement "
            f"sur votre compte PayPal.\n\n"
            f"❓ Êtes-vous sûr de vouloir annuler ?"
        )
        
        logger.info(f"🔥 ANNULATION: Message créé, envoi...")
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur complète cancel_booking: {e}")
        logger.error(f"❌ Type erreur: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        await query.edit_message_text("❌ Données de réservation incomplètes")

async def handle_confirm_cancel(update: Update, context: CallbackContext):
    """Confirme l'annulation et déclenche le remboursement"""
    query = update.callback_query
    await query.answer()
    
    try:
        booking_id = int(query.data.split(':')[1])
        
        await query.edit_message_text("🔄 **Traitement de l'annulation...**\n\nVeuillez patienter...")
        
        # Déclencher le remboursement automatique
        success = await process_passenger_refund(booking_id, context.bot)
        
        if success:
            message = (
                f"✅ **Annulation confirmée !**\n\n"
                f"Votre réservation #{booking_id} a été annulée avec succès.\n\n"
                f"💰 **Remboursement en cours:** Le montant sera remboursé "
                f"sur votre compte PayPal dans les minutes qui suivent.\n\n"
                f"📧 Vous recevrez une confirmation par email de PayPal.\n\n"
                f"Merci d'avoir utilisé CovoiturageSuisse !"
            )
        else:
            message = (
                f"⚠️ **Annulation effectuée mais problème de remboursement**\n\n"
                f"Votre réservation #{booking_id} a été annulée, mais le "
                f"remboursement automatique a échoué.\n\n"
                f"💬 **Contactez le support** avec le numéro #{booking_id} "
                f"pour traiter votre remboursement manuellement.\n\n"
                f"📧 Email de support: support@covoituragesuisse.ch"
            )
        
        await query.edit_message_text(text=message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur confirm_cancel: {e}")
        await query.edit_message_text("❌ Erreur lors de la confirmation d'annulation")

async def handle_trip_details(update: Update, context: CallbackContext):
    """Affiche les détails complets du trajet"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(':')[1])
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé")
            return
        
        # Récupérer toutes les réservations payées
        bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.payment_status == 'completed'
        ).all()
        
        total_passengers = len(bookings)
        total_revenue = sum(b.amount for b in bookings)  # Utiliser 'amount' au lieu de 'total_price'
        
        passengers_list = []
        for booking in bookings:
            passenger_name = booking.passenger.full_name or booking.passenger.username or 'Passager'
            passengers_list.append(f"• {passenger_name} ({booking.amount:.2f} CHF)")
        
        passengers_text = "\n".join(passengers_list) if passengers_list else "Aucun passager"
        
        message = (
            f"🚗 **Détails du Trajet #{trip_id}**\n\n"
            f"📍 **Itinéraire:** {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"👤 **Conducteur:** {trip.driver.full_name or 'Non renseigné'}\n\n"
            f"👥 **Passagers ({total_passengers}):**\n{passengers_text}\n\n"
            f"💰 **Total collecté:** {total_revenue:.2f} CHF"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Retour réservations", callback_data="profile:my_bookings")]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur trip_details: {e}")
        await query.edit_message_text("❌ Erreur lors de l'affichage des détails")

async def handle_send_message_driver(update: Update, context: CallbackContext):
    """Gère l'envoi de message au conducteur"""
    query = update.callback_query
    await query.answer()
    
    try:
        trip_id = int(query.data.split(':')[1])
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip or not trip.driver:
            await query.edit_message_text("❌ Conducteur non trouvé")
            return
        
        driver = trip.driver
        passenger_user = db.query(User).filter(User.telegram_id == query.from_user.id).first()
        
        if not passenger_user:
            await query.edit_message_text("❌ Utilisateur non trouvé")
            return
        
        # Interface pour envoyer un message
        keyboard = [
            [InlineKeyboardButton("🔙 Retour contact", callback_data=f"contact_driver:{trip_id}")]
        ]
        
        message = (
            f"💬 **Envoyer un message à {driver.full_name or driver.username or 'conducteur'}**\n\n"
            f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"✍️ **Tapez votre message ci-dessous et envoyez-le.**\n"
            f"Le message sera transmis automatiquement au conducteur."
        )
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        # Stocker les infos pour le prochain message
        context.user_data['messaging_driver'] = {
            'driver_id': driver.telegram_id,
            'driver_name': driver.full_name or driver.username or 'conducteur',
            'trip_id': trip_id,
            'passenger_name': passenger_user.full_name or passenger_user.username or 'passager'
        }
        
    except Exception as e:
        logger.error(f"Erreur send_message_driver: {e}")
        await query.edit_message_text("❌ Erreur lors de l'envoi du message")

async def handle_rdv_station(update: Update, context: CallbackContext):
    """Gère le choix gare comme point de RDV"""
    query = update.callback_query
    await query.answer("📍 Point de RDV: Gare sélectionnée")
    
    try:
        trip_id = int(query.data.split(':')[1])
        keyboard = [[InlineKeyboardButton("🔙 Retour réservations", callback_data="profile:my_bookings")]]
        
        await query.edit_message_text(
            text="📍 **Point de rendez-vous défini**\n\n🚉 **Gare de départ**\n\nLe conducteur sera informé de votre choix.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Erreur rdv_station: {e}")
        await query.edit_message_text("❌ Erreur lors de la définition du RDV")

async def handle_rdv_center(update: Update, context: CallbackContext):
    """Gère le choix centre-ville comme point de RDV"""
    query = update.callback_query
    await query.answer("📍 Point de RDV: Centre-ville sélectionné")
    
    try:
        trip_id = int(query.data.split(':')[1])
        keyboard = [[InlineKeyboardButton("🔙 Retour réservations", callback_data="profile:my_bookings")]]
        
        await query.edit_message_text(
            text="📍 **Point de rendez-vous défini**\n\n🏢 **Centre-ville**\n\nLe conducteur sera informé de votre choix.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Erreur rdv_center: {e}")
        await query.edit_message_text("❌ Erreur lors de la définition du RDV")

async def handle_rdv_custom(update: Update, context: CallbackContext):
    """Gère le choix lieu personnalisé comme point de RDV"""
    query = update.callback_query
    await query.answer("✏️ Tapez votre lieu de RDV")
    
    try:
        trip_id = int(query.data.split(':')[1])
        keyboard = [[InlineKeyboardButton("🔙 Retour réservations", callback_data="profile:my_bookings")]]
        
        await query.edit_message_text(
            text="✏️ **Lieu personnalisé**\n\nTapez ci-dessous l'adresse ou le lieu de rendez-vous souhaité.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Erreur rdv_custom: {e}")
        await query.edit_message_text("❌ Erreur lors de la définition du RDV")
