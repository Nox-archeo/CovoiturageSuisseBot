#!/usr/bin/env python3
"""
Système de confirmation de trajet pour libérer le paiement au conducteur
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database.db_manager import get_db
from database.models import Booking, Trip, User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def check_completed_trips_for_confirmation(context: CallbackContext):
    """
    Fonction automatique qui vérifie les trajets terminés et demande confirmation
    À exécuter périodiquement (par exemple toutes les heures)
    """
    try:
        db = get_db()
        
        # Chercher les trajets terminés dans les dernières 24h qui n'ont pas été confirmés
        yesterday = datetime.now() - timedelta(days=1)
        completed_trips = db.query(Trip).filter(
            Trip.departure_time < datetime.now(),  # Trajet passé
            Trip.departure_time > yesterday,  # Pas trop ancien
            Trip.status != 'confirmed_completed'  # Pas encore confirmé
        ).all()
        
        for trip in completed_trips:
            # Vérifier s'il y a des réservations payées pour ce trajet
            paid_bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.is_paid == True,
                Booking.status == 'confirmed'
            ).all()
            
            if paid_bookings:
                # Envoyer demande de confirmation au conducteur
                await send_trip_completion_request(context.bot, trip, paid_bookings, db)
                
    except Exception as e:
        logger.error(f"Erreur check_completed_trips: {e}")

async def send_trip_completion_request(bot, trip: Trip, bookings: list, db):
    """
    Envoie une demande de confirmation de trajet au conducteur
    """
    try:
        total_amount = sum(booking.amount for booking in bookings if booking.amount)
        driver_amount = total_amount * 0.88  # 88% pour le conducteur (12% commission)
        
        passenger_names = []
        for booking in bookings:
            passenger = db.query(User).filter(User.id == booking.passenger_id).first()
            if passenger:
                passenger_names.append(passenger.full_name or passenger.username or f"Passager {booking.passenger_id}")
        
        message = (
            f"🏁 *Confirmation de trajet requis*\n\n"
            f"📍 Trajet : {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 Date : {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"👥 Passagers : {', '.join(passenger_names)}\n"
            f"💰 Montant à recevoir : {driver_amount:.2f} CHF\n\n"
            f"❓ *Le trajet a-t-il bien eu lieu ?*\n"
            f"Confirmez pour débloquer votre paiement."
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Trajet effectué", callback_data=f"confirm_trip_completed:{trip.id}")],
            [InlineKeyboardButton("❌ Trajet non effectué", callback_data=f"confirm_trip_cancelled:{trip.id}")],
            [InlineKeyboardButton("⏰ Rappeler plus tard", callback_data=f"confirm_trip_later:{trip.id}")]
        ]
        
        await bot.send_message(
            chat_id=trip.driver_id,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        logger.info(f"📤 Demande confirmation envoyée au conducteur {trip.driver_id} pour trajet {trip.id}")
        
    except Exception as e:
        logger.error(f"Erreur send_trip_completion_request: {e}")

async def handle_trip_confirmation_callback(update: Update, context: CallbackContext):
    """
    Gère les callbacks de confirmation de trajet
    """
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        action = data.split(':')[0]
        trip_id = int(data.split(':')[1])
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé.")
            return
        
        if action == "confirm_trip_completed":
            # Marquer le trajet comme confirmé et libérer les paiements
            await confirm_trip_completed(query, trip, db)
            
        elif action == "confirm_trip_cancelled":
            # Trajet annulé - rembourser les passagers
            await confirm_trip_cancelled(query, trip, db)
            
        elif action == "confirm_trip_later":
            # Reporter la demande
            await query.edit_message_text(
                f"⏰ Demande de confirmation reportée.\n"
                f"Vous recevrez un nouveau rappel dans quelques heures."
            )
            
    except Exception as e:
        logger.error(f"Erreur handle_trip_confirmation_callback: {e}")

async def confirm_trip_completed(query, trip: Trip, db):
    """
    Confirme qu'un trajet a bien eu lieu et libère les paiements
    """
    try:
        # Marquer le trajet comme confirmé
        trip.status = 'confirmed_completed'
        db.commit()
        
        # Récupérer les réservations payées
        paid_bookings = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.is_paid == True
        ).all()
        
        total_amount = sum(booking.amount for booking in paid_bookings if booking.amount)
        driver_amount = total_amount * 0.88
        
        # Marquer les réservations comme terminées
        for booking in paid_bookings:
            booking.status = 'completed'
        db.commit()
        
        # TODO: Ici il faudrait déclencher le virement au conducteur
        # Pour l'instant, on simule avec un message
        
        message = (
            f"✅ *Trajet confirmé !*\n\n"
            f"📍 {trip.departure_city} → {trip.arrival_city}\n"
            f"💰 Montant à recevoir : {driver_amount:.2f} CHF\n\n"
            f"🏦 *Votre paiement sera traité dans les prochaines 24h.*\n"
            f"Vous recevrez une confirmation par email."
        )
        
        await query.edit_message_text(message, parse_mode='Markdown')
        
        # Notifier les passagers
        for booking in paid_bookings:
            try:
                passenger = db.query(User).filter(User.id == booking.passenger_id).first()
                if passenger and passenger.telegram_id:
                    await query.bot.send_message(
                        chat_id=passenger.telegram_id,
                        text=f"✅ *Trajet confirmé*\n\n"
                             f"Le conducteur a confirmé que votre trajet a bien eu lieu.\n"
                             f"📍 {trip.departure_city} → {trip.arrival_city}\n"
                             f"📅 {trip.departure_time.strftime('%d/%m/%Y')}\n\n"
                             f"Merci d'avoir utilisé CovoiturageSuisse !",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Erreur notification passager {booking.passenger_id}: {e}")
        
        logger.info(f"✅ Trajet {trip.id} confirmé, paiement de {driver_amount:.2f} CHF libéré")
        
    except Exception as e:
        logger.error(f"Erreur confirm_trip_completed: {e}")

async def confirm_trip_cancelled(query, trip: Trip, db):
    """
    Confirme qu'un trajet n'a pas eu lieu et rembourse les passagers
    """
    try:
        # Marquer le trajet comme annulé
        trip.status = 'cancelled'
        db.commit()
        
        # Récupérer les réservations payées pour remboursement
        paid_bookings = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.is_paid == True
        ).all()
        
        # TODO: Ici il faudrait déclencher les remboursements PayPal
        # Pour l'instant, on simule
        
        for booking in paid_bookings:
            booking.status = 'refunded'
        db.commit()
        
        message = (
            f"❌ *Trajet annulé*\n\n"
            f"📍 {trip.departure_city} → {trip.arrival_city}\n\n"
            f"🔄 *Les passagers seront automatiquement remboursés.*\n"
            f"Les remboursements seront traités dans les prochaines 24h."
        )
        
        await query.edit_message_text(message, parse_mode='Markdown')
        
        # Notifier les passagers du remboursement
        for booking in paid_bookings:
            try:
                passenger = db.query(User).filter(User.id == booking.passenger_id).first()
                if passenger and passenger.telegram_id:
                    await query.bot.send_message(
                        chat_id=passenger.telegram_id,
                        text=f"🔄 *Remboursement en cours*\n\n"
                             f"Le trajet {trip.departure_city} → {trip.arrival_city} "
                             f"du {trip.departure_time.strftime('%d/%m/%Y')} a été annulé.\n\n"
                             f"💰 Votre remboursement de {booking.amount} CHF sera traité "
                             f"dans les prochaines 24h.",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Erreur notification remboursement {booking.passenger_id}: {e}")
        
        logger.info(f"❌ Trajet {trip.id} annulé, {len(paid_bookings)} remboursements en cours")
        
    except Exception as e:
        logger.error(f"Erreur confirm_trip_cancelled: {e}")
