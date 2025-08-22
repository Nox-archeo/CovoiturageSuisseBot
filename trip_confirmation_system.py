#!/usr/bin/env python3
"""
Système de confirmation de trajet DOUBLE (conducteur + passager) pour libérer le paiement
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database.db_manager import get_db
from database.models import Booking, Trip, User
from datetime import datetime, timedelta
from paypal_utils import PayPalManager
import logging

logger = logging.getLogger(__name__)

async def add_confirmation_buttons_to_trip(trip_id: int, user_id: int, user_type: str):
    """
    Ajoute les boutons de confirmation à un trajet si nécessaire
    
    Args:
        trip_id: ID du trajet
        user_id: ID de l'utilisateur (conducteur ou passager)
        user_type: 'driver' ou 'passenger'
    
    Returns:
        Liste de boutons à ajouter
    """
    try:
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            return []
        
        # Vérifier s'il y a des réservations payées pour ce trajet
        paid_bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.is_paid == True,
            Booking.status == 'confirmed'
        ).all()
        
        if not paid_bookings:
            return []  # Pas de paiements, pas de boutons
        
        now = datetime.now()
        
        # Déterminer l'état de confirmation actuel
        confirmation_state = get_trip_confirmation_state(trip_id, db)
        
        buttons = []
        
        if user_type == 'driver':
            # Boutons pour le conducteur
            if not confirmation_state['driver_confirmed']:
                if trip.departure_time > now:
                    # Trajet futur - bouton avec avertissement
                    days_until = (trip.departure_time - now).days
                    if days_until > 0:
                        button_text = f"⚠️ Confirmer trajet ({days_until}j avant)"
                    else:
                        button_text = "✅ Confirmer trajet effectué"
                else:
                    # Trajet passé - bouton normal
                    button_text = "✅ Confirmer trajet effectué"
                
                buttons.append(InlineKeyboardButton(
                    button_text, 
                    callback_data=f"confirm_trip_driver:{trip_id}"
                ))
            else:
                # Conducteur a déjà confirmé
                if confirmation_state['passenger_confirmed']:
                    buttons.append(InlineKeyboardButton(
                        "🎉 Trajet confirmé (paiement libéré)", 
                        callback_data="noop"
                    ))
                else:
                    buttons.append(InlineKeyboardButton(
                        "⏳ En attente confirmation passager", 
                        callback_data="noop"
                    ))
        
        elif user_type == 'passenger':
            # Boutons pour le passager
            # Vérifier que cet utilisateur a bien une réservation sur ce trajet
            user_booking = None
            for booking in paid_bookings:
                passenger = db.query(User).filter(User.id == booking.passenger_id).first()
                if passenger and passenger.telegram_id == user_id:
                    user_booking = booking
                    break
            
            if not user_booking:
                return []  # Cet utilisateur n'a pas de réservation payée
            
            # Vérifier l'état de confirmation de ce passager spécifique
            passenger_confirmations = confirmation_state.get('passenger_confirmations', {})
            passenger_confirmed = passenger_confirmations.get(str(user_booking.passenger_id), False)
            
            if not passenger_confirmed:
                if trip.departure_time > now:
                    # Trajet futur - bouton avec avertissement
                    days_until = (trip.departure_time - now).days
                    if days_until > 0:
                        button_text = f"⚠️ Confirmer trajet ({days_until}j avant)"
                    else:
                        button_text = "✅ Confirmer trajet effectué"
                else:
                    # Trajet passé - bouton normal
                    button_text = "✅ Confirmer trajet effectué"
                
                buttons.append(InlineKeyboardButton(
                    button_text, 
                    callback_data=f"confirm_trip_passenger:{trip_id}:{user_booking.id}"
                ))
            else:
                # Ce passager a déjà confirmé
                if confirmation_state['all_confirmed']:
                    buttons.append(InlineKeyboardButton(
                        "🎉 Trajet confirmé (paiement libéré)", 
                        callback_data="noop"
                    ))
                else:
                    buttons.append(InlineKeyboardButton(
                        "⏳ En attente autres confirmations", 
                        callback_data="noop"
                    ))
        
        return buttons
        
    except Exception as e:
        logger.error(f"Erreur add_confirmation_buttons_to_trip: {e}")
        return []

def get_trip_confirmation_state(trip_id: int, db):
    """
    Récupère l'état des confirmations pour un trajet
    
    Returns:
        dict avec driver_confirmed, passenger_confirmations, all_confirmed
    """
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            return {'driver_confirmed': False, 'passenger_confirmations': {}, 'all_confirmed': False}
        
        # Vérifier confirmation conducteur
        driver_confirmed = getattr(trip, 'driver_confirmed_completion', False)
        
        # Vérifier confirmations passagers
        paid_bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.is_paid == True,
            Booking.status == 'confirmed'
        ).all()
        
        passenger_confirmations = {}
        all_passengers_confirmed = True
        
        for booking in paid_bookings:
            passenger_confirmed = getattr(booking, 'passenger_confirmed_completion', False)
            passenger_confirmations[str(booking.passenger_id)] = passenger_confirmed
            
            if not passenger_confirmed:
                all_passengers_confirmed = False
        
        # Toutes les confirmations reçues ?
        all_confirmed = driver_confirmed and all_passengers_confirmed and len(paid_bookings) > 0
        
        return {
            'driver_confirmed': driver_confirmed,
            'passenger_confirmations': passenger_confirmations,
            'passenger_confirmed': all_passengers_confirmed,  # Pour compatibilité
            'all_confirmed': all_confirmed
        }
        
    except Exception as e:
        logger.error(f"Erreur get_trip_confirmation_state: {e}")
        return {'driver_confirmed': False, 'passenger_confirmations': {}, 'all_confirmed': False}

async def handle_trip_confirmation_callback(update: Update, context: CallbackContext):
    """
    Gère les callbacks de confirmation de trajet (double confirmation)
    """
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        parts = data.split(':')
        action = parts[0]
        trip_id = int(parts[1])
        
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            await query.edit_message_text("❌ Trajet non trouvé.")
            return
        
        now = datetime.now()
        
        if action == "confirm_trip_driver":
            await handle_driver_confirmation(query, trip, db, now)
            
        elif action == "confirm_trip_passenger":
            booking_id = int(parts[2]) if len(parts) > 2 else None
            await handle_passenger_confirmation(query, trip, booking_id, db, now)
            
    except Exception as e:
        logger.error(f"Erreur handle_trip_confirmation_callback: {e}")
        await query.edit_message_text("❌ Erreur lors de la confirmation.")

async def handle_driver_confirmation(query, trip: Trip, db, now: datetime):
    """Gère la confirmation du conducteur"""
    try:
        # Vérifier si confirmation prématurée
        if trip.departure_time > now:
            days_until = (trip.departure_time - now).days
            hours_until = (trip.departure_time - now).total_seconds() / 3600
            
            if True:  # Toujours demander double confirmation pour sécurité paiement
                # Demander confirmation pour trajet futur
                keyboard = [
                    [InlineKeyboardButton("✅ Oui, confirmer quand même", callback_data=f"force_confirm_driver:{trip.id}")],
                    [InlineKeyboardButton("❌ Annuler", callback_data="noop")]
                ]
                
                await query.edit_message_text(
                    f"⚠️ **Attention !**\n\n"
                    f"Le trajet a lieu dans {days_until} jour(s).\n"
                    f"📅 Date prévue : {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                    f"❓ **Voulez-vous vraiment confirmer que le trajet a eu lieu ?**\n"
                    f"Cette action libérera le paiement aux passagers.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
        
        # Confirmation normale
        await confirm_driver_completion(query, trip, db)
        
    except Exception as e:
        logger.error(f"Erreur handle_driver_confirmation: {e}")

async def handle_passenger_confirmation(query, trip: Trip, booking_id: int, db, now: datetime):
    """Gère la confirmation d'un passager"""
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            await query.edit_message_text("❌ Réservation non trouvée.")
            return
        
        # Vérifier si confirmation prématurée
        if trip.departure_time > now:
            days_until = (trip.departure_time - now).days
            
            if True:  # Toujours demander double confirmation pour sécurité paiement
                # Demander confirmation pour trajet futur
                keyboard = [
                    [InlineKeyboardButton("✅ Oui, confirmer quand même", callback_data=f"force_confirm_passenger:{trip.id}:{booking_id}")],
                    [InlineKeyboardButton("❌ Annuler", callback_data="noop")]
                ]
                
                await query.edit_message_text(
                    f"⚠️ **Attention !**\n\n"
                    f"Le trajet a lieu dans {days_until} jour(s).\n"
                    f"📅 Date prévue : {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                    f"❓ **Voulez-vous vraiment confirmer que le trajet a eu lieu ?**\n"
                    f"Cette confirmation est nécessaire pour le paiement du conducteur.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
        
        # Confirmation normale
        await confirm_passenger_completion(query, trip, booking, db)
        
    except Exception as e:
        logger.error(f"Erreur handle_passenger_confirmation: {e}")

async def confirm_driver_completion(query, trip: Trip, db):
    """Confirme la completion côté conducteur"""
    try:
        # Marquer la confirmation conducteur
        trip.driver_confirmed_completion = True
        db.commit()
        
        # Vérifier si toutes les confirmations sont reçues
        confirmation_state = get_trip_confirmation_state(trip.id, db)
        
        if confirmation_state['all_confirmed']:
            # Toutes les confirmations reçues - libérer le paiement
            await release_payment_to_driver(query, trip, db)
        else:
            # En attente des confirmations passagers
            await query.edit_message_text(
                f"✅ **Votre confirmation enregistrée !**\n\n"
                f"📍 {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                f"⏳ **En attente des confirmations des passagers.**\n"
                f"Le paiement sera libéré une fois que tous les passagers auront confirmé.",
                parse_mode='Markdown'
            )
        
        logger.info(f"✅ Conducteur a confirmé le trajet {trip.id}")
        
    except Exception as e:
        logger.error(f"Erreur confirm_driver_completion: {e}")

async def confirm_passenger_completion(query, trip: Trip, booking: Booking, db):
    """Confirme la completion côté passager"""
    try:
        # Marquer la confirmation passager
        booking.passenger_confirmed_completion = True
        db.commit()
        
        # Vérifier si toutes les confirmations sont reçues
        confirmation_state = get_trip_confirmation_state(trip.id, db)
        
        if confirmation_state['all_confirmed']:
            # Toutes les confirmations reçues - libérer le paiement
            await release_payment_to_driver(query, trip, db)
        else:
            # En attente d'autres confirmations
            await query.edit_message_text(
                f"✅ **Votre confirmation enregistrée !**\n\n"
                f"📍 {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                f"⏳ **En attente d'autres confirmations.**\n"
                f"Le paiement du conducteur sera libéré une fois que toutes les parties auront confirmé.",
                parse_mode='Markdown'
            )
        
        logger.info(f"✅ Passager {booking.passenger_id} a confirmé le trajet {trip.id}")
        
    except Exception as e:
        logger.error(f"Erreur confirm_passenger_completion: {e}")

async def release_payment_to_driver(query, trip: Trip, db):
    """Libère le paiement au conducteur après double confirmation"""
    try:
        # Marquer le trajet comme complètement confirmé
        trip.status = 'completed_confirmed'
        trip.payment_released = True
        db.commit()
        
        # Calculer le montant à libérer
        paid_bookings = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.is_paid == True
        ).all()
        
        total_amount = sum(booking.amount for booking in paid_bookings if booking.amount)
        driver_amount = total_amount * 0.88  # 88% pour le conducteur
        
        # Marquer les réservations comme terminées
        for booking in paid_bookings:
            booking.status = 'completed_confirmed'
        db.commit()
        
        # Message de confirmation
        message = (
            f"🎉 **PAIEMENT LIBÉRÉ !**\n\n"
            f"📍 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"💰 **Montant : {driver_amount:.2f} CHF**\n\n"
            f"✅ Toutes les confirmations reçues !\n"
            f"🏦 Votre paiement sera traité dans les prochaines 24h.\n\n"
            f"Merci d'utiliser CovoiturageSuisse !"
        )
        
        await query.edit_message_text(message, parse_mode='Markdown')
        
        # Notifier le conducteur
        try:
            await query.bot.send_message(
                chat_id=trip.driver_id,
                text=message,
                parse_mode='Markdown'
            )
        except:
            pass  # Éviter erreur si c'est déjà le conducteur
        
        # Notifier tous les passagers
        for booking in paid_bookings:
            try:
                passenger = db.query(User).filter(User.id == booking.passenger_id).first()
                if passenger and passenger.telegram_id:
                    await query.bot.send_message(
                        chat_id=passenger.telegram_id,
                        text=f"🎉 **Trajet confirmé !**\n\n"
                             f"📍 {trip.departure_city} → {trip.arrival_city}\n"
                             f"📅 {trip.departure_time.strftime('%d/%m/%Y')}\n\n"
                             f"✅ Le conducteur a été payé suite à vos confirmations mutuelles.\n"
                             f"Merci d'avoir utilisé CovoiturageSuisse !",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Erreur notification passager {booking.passenger_id}: {e}")
        
        logger.info(f"🎉 Paiement de {driver_amount:.2f} CHF libéré pour trajet {trip.id}")
        
        # 🚀 NOUVEAU: Déclencher le vrai paiement au conducteur
        await process_driver_payout(trip, driver_amount, db)
        
    except Exception as e:
        logger.error(f"Erreur release_payment_to_driver: {e}")

async def process_driver_payout(trip: Trip, driver_amount: float, db):
    """
    Traite le paiement automatique au conducteur via PayPal
    """
    try:
        # Récupérer les infos du conducteur
        driver = db.query(User).filter(User.id == trip.driver_id).first()
        
        if not driver:
            logger.error(f"Conducteur non trouvé pour trip {trip.id}")
            return
            
        if not driver.paypal_email:
            logger.error(f"Conducteur {driver.id} n'a pas d'email PayPal configuré")
            # Marquer qu'il faut un paiement manuel
            trip.status = 'payment_pending_manual'
            db.commit()
            return
        
        # Initialiser PayPal
        paypal = PayPalManager()
        
        # Description du trajet pour PayPal
        trip_description = f"{trip.departure_city} → {trip.arrival_city} ({trip.departure_time.strftime('%d/%m/%Y')})"
        
        # 💰 EFFECTUER LE PAIEMENT RÉEL
        logger.info(f"🏦 Tentative de paiement PayPal : {driver_amount:.2f} CHF vers {driver.paypal_email}")
        
        success, payout_details = paypal.payout_to_driver(
            driver_email=driver.paypal_email,
            amount=driver_amount,
            trip_description=trip_description
        )
        
        if success and payout_details:
            # ✅ PAIEMENT RÉUSSI
            batch_id = payout_details.get('batch_id')
            trip.payout_batch_id = batch_id
            trip.status = 'completed_paid'
            trip.driver_amount = driver_amount
            trip.commission_amount = sum(booking.amount for booking in db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.is_paid == True
            ).all()) * 0.12
            
            db.commit()
            
            logger.info(f"✅ Paiement PayPal réussi ! Batch ID: {batch_id}")
            
            # Notifier le conducteur du paiement réussi
            try:
                from telegram import Bot
                bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
                await bot.send_message(
                    chat_id=driver.telegram_id,
                    text=f"💰 **PAIEMENT ENVOYÉ !**\n\n"
                         f"📧 PayPal: {driver.paypal_email}\n"
                         f"💵 Montant: {driver_amount:.2f} CHF\n"
                         f"🚗 Trajet: {trip_description}\n\n"
                         f"✅ Le paiement arrivera dans votre compte PayPal dans les prochaines minutes.\n\n"
                         f"Merci d'utiliser CovoiturageSuisse !",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Erreur notification conducteur paiement: {e}")
                
        else:
            # ❌ ÉCHEC DU PAIEMENT - Basculer en mode manuel
            logger.error(f"❌ Échec paiement PayPal pour trajet {trip.id}")
            trip.status = 'payment_pending_manual'
            trip.driver_amount = driver_amount
            trip.commission_amount = sum(booking.amount for booking in db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.is_paid == True
            ).all()) * 0.12
            db.commit()
            
            # Enregistrer pour traitement manuel
            try:
                with open('/Users/margaux/CovoiturageSuisse/paiements_manuels.txt', 'a') as f:
                    f.write(f"[{trip.departure_time.strftime('%d/%m/%Y %H:%M')}] "
                           f"Trajet {trip.id}: {driver_amount:.2f} CHF → {driver.paypal_email} "
                           f"({trip.departure_city} → {trip.arrival_city})\n")
            except:
                pass
            
            # Notifier que le paiement sera manuel
            try:
                from telegram import Bot
                bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
                await bot.send_message(
                    chat_id=driver.telegram_id,
                    text=f"✅ **Trajet confirmé - Paiement en cours**\n\n"
                         f"💰 Montant: {driver_amount:.2f} CHF\n"
                         f"🚗 Trajet: {trip_description}\n\n"
                         f"🏦 Votre paiement sera traité manuellement dans les 24h.\n"
                         f"📧 Destination: {driver.paypal_email}\n\n"
                         f"Merci d'utiliser CovoiturageSuisse !",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Erreur notification paiement manuel: {e}")
                
    except Exception as e:
        logger.error(f"Erreur process_driver_payout: {e}")
        # Marquer pour traitement manuel
        trip.status = 'payment_error'
        db.commit()
