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
            [InlineKeyboardButton("🔙 Retour", callback_data=f"trip_details:{trip_id}")]
        ]
        
        message = (
            f"👤 **Contact Conducteur**\n\n"
            f"**Nom:** {driver.first_name or 'Non renseigné'}\n"
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
            f"**Nom:** {passenger.first_name or 'Non renseigné'}\n"
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
            [InlineKeyboardButton("🔙 Retour", callback_data=f"trip_details:{trip_id}")]
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
        booking_id = int(query.data.split(':')[1])
        db = get_db()
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking:
            await query.edit_message_text("❌ Réservation non trouvée")
            return
        
        if booking.status == 'cancelled':
            await query.edit_message_text("❌ Cette réservation est déjà annulée")
            return
        
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
            f"**Montant:** {booking.total_price:.2f} CHF\n\n"
            f"💰 **Remboursement automatique:** Vous serez remboursé intégralement "
            f"sur votre compte PayPal.\n\n"
            f"❓ Êtes-vous sûr de vouloir annuler ?"
        )
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur cancel_booking: {e}")
        await query.edit_message_text("❌ Erreur lors de l'annulation")

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
        total_revenue = sum(b.total_price for b in bookings)
        
        passengers_list = []
        for booking in bookings:
            passenger_name = booking.passenger.first_name or booking.passenger.username or 'Passager'
            passengers_list.append(f"• {passenger_name} ({booking.total_price:.2f} CHF)")
        
        passengers_text = "\n".join(passengers_list) if passengers_list else "Aucun passager"
        
        message = (
            f"🚗 **Détails du Trajet #{trip_id}**\n\n"
            f"📍 **Itinéraire:** {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"👤 **Conducteur:** {trip.driver.first_name or 'Non renseigné'}\n\n"
            f"👥 **Passagers ({total_passengers}):**\n{passengers_text}\n\n"
            f"💰 **Total collecté:** {total_revenue:.2f} CHF"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Retour au menu principal", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur trip_details: {e}")
        await query.edit_message_text("❌ Erreur lors de l'affichage des détails")
