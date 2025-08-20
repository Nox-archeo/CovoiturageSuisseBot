#!/usr/bin/env python3
"""
Handlers pour l'annulation de réservations avec remboursement automatique
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from database.models import Booking, User
from database import get_db

logger = logging.getLogger(__name__)

async def handle_booking_cancellation(update: Update, context: CallbackContext):
    """Gère l'annulation d'une réservation avec remboursement automatique"""
    query = update.callback_query
    await query.answer()
    
    try:
        booking_id = int(query.data.split(':')[1])
        user_id = update.effective_user.id
        
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await query.edit_message_text("❌ Erreur: utilisateur non trouvé.")
            return
        
        booking = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.passenger_id == user.id
        ).first()
        
        if not booking:
            await query.edit_message_text("❌ Réservation non trouvée ou non autorisée.")
            return
        
        if booking.status == 'cancelled':
            await query.edit_message_text("❌ Cette réservation est déjà annulée.")
            return
        
        if not booking.is_paid:
            await query.edit_message_text("❌ Cette réservation n'a pas été payée.")
            return
        
        trip = booking.trip
        if not trip:
            await query.edit_message_text("❌ Trajet associé introuvable.")
            return
        
        # Vérifier que les champs essentiels ne sont pas None
        if not booking.total_price or not trip.departure_time:
            await query.edit_message_text("❌ Données de réservation incomplètes.")
            return
        
        # Confirmation d'annulation
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmer l'annulation", callback_data=f"confirm_cancel_booking:{booking_id}"),
                InlineKeyboardButton("❌ Annuler", callback_data="profile:my_bookings")
            ]
        ]
        
        message = (
            f"⚠️ *Confirmer l'annulation*\n\n"
            f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
            f"💰 **Montant à rembourser:** {booking.total_price:.2f} CHF\n\n"
            f"🔄 **Remboursement automatique via PayPal**\n"
            f"Vous serez remboursé dans les minutes qui suivent.\n\n"
            f"⚠️ **Cette action est définitive.**"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de réservation: {e}")
        await query.edit_message_text("❌ Erreur lors de l'annulation.")


async def confirm_booking_cancellation(update: Update, context: CallbackContext):
    """Confirme et traite l'annulation avec remboursement"""
    query = update.callback_query
    await query.answer()
    
    try:
        booking_id = int(query.data.split(':')[1])
        user_id = update.effective_user.id
        
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await query.edit_message_text("❌ Erreur: utilisateur non trouvé.")
            return
        
        booking = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.passenger_id == user.id
        ).first()
        
        if not booking or booking.status == 'cancelled':
            await query.edit_message_text("❌ Réservation non trouvée ou déjà annulée.")
            return
        
        # Vérifier l'email PayPal de l'utilisateur
        if not user.paypal_email:
            keyboard = [
                [InlineKeyboardButton("📧 Ajouter email PayPal", callback_data=f"add_paypal_for_refund:{booking_id}")],
                [InlineKeyboardButton("🔙 Retour", callback_data="profile:my_bookings")]
            ]
            
            message = (
                f"📧 **Email PayPal requis**\n\n"
                f"Pour recevoir le remboursement automatique, "
                f"vous devez renseigner votre email PayPal.\n\n"
                f"💰 **Montant à rembourser:** {booking.total_price:.2f} CHF"
            )
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Traiter l'annulation et le remboursement
        await query.edit_message_text("🔄 **Traitement de l'annulation en cours...**", parse_mode='Markdown')
        
        # Importer le gestionnaire de remboursement
        try:
            from passenger_refund_manager import process_passenger_refund
            refund_success = await process_passenger_refund(booking_id, context.bot)
            
            if refund_success:
                # Récupérer le trajet pour libérer la place
                trip = booking.trip
                
                # LIBÉRER LA PLACE dans le trajet
                if trip and trip.current_passengers > 0:
                    trip.current_passengers -= 1
                    logger.info(f"✅ Place libérée: {trip.current_passengers}/{trip.max_passengers}")
                
                # Marquer la réservation comme annulée
                booking.status = 'cancelled'
                booking.payment_status = 'refunded'
                
                # SUPPRIMER la réservation pour qu'elle n'apparaisse plus dans le profil
                db.delete(booking)
                db.commit()
                
                message = (
                    f"✅ **Annulation confirmée !**\n\n"
                    f"💰 **Remboursement de {booking.total_price:.2f} CHF traité**\n"
                    f"📧 Envoyé sur: {user.paypal_email}\n\n"
                    f"⏱️ Le remboursement apparaîtra sur votre compte PayPal "
                    f"dans les minutes qui suivent.\n\n"
                    f"✅ **Place libérée** dans le trajet du conducteur"
                )
                
                # Notifier le conducteur avec info sur la place libérée
                try:
                    driver = trip.driver if trip else None
                    if driver and driver.telegram_id:
                        available_spots = trip.max_passengers - trip.current_passengers
                        await context.bot.send_message(
                            chat_id=driver.telegram_id,
                            text=f"� **Annulation de réservation**\n\n"
                                 f"Un passager a annulé sa réservation :\n\n"
                                 f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
                                 f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                                 f"💰 **Montant:** {booking.total_price:.2f} CHF\n\n"
                                 f"✅ **Bonne nouvelle:** Une place s'est libérée !\n"
                                 f"🆓 **Places disponibles:** {available_spots}/{trip.max_passengers}\n\n"
                                 f"Le remboursement a été traité automatiquement.",
                            parse_mode='Markdown'
                        )
                        logger.info(f"✅ Conducteur notifié (ID: {driver.telegram_id})")
                except Exception as e:
                    logger.error(f"Erreur notification conducteur: {e}")
                
            else:
                # Même si remboursement échoue, libérer la place et supprimer la réservation
                trip = booking.trip
                
                # LIBÉRER LA PLACE
                if trip and trip.current_passengers > 0:
                    trip.current_passengers -= 1
                    logger.info(f"✅ Place libérée malgré échec remboursement: {trip.current_passengers}/{trip.max_passengers}")
                
                # SUPPRIMER la réservation
                db.delete(booking)
                db.commit()
                
                message = (
                    f"⚠️ **Annulation terminée**\n\n"
                    f"✅ **Réservation annulée et place libérée**\n"
                    f"❌ **Remboursement automatique échoué**\n\n"
                    f"💬 **Contactez le support** pour le remboursement:\n"
                    f"📝 Réservation #{booking_id}\n"
                    f"📧 PayPal: {user.paypal_email}\n"
                    f"💰 Montant: {booking.total_price:.2f} CHF\n\n"
                    f"Le remboursement sera traité manuellement."
                )
                
                # Notifier le conducteur même en cas d'échec remboursement
                try:
                    driver = trip.driver if trip else None
                    if driver and driver.telegram_id:
                        available_spots = trip.max_passengers - trip.current_passengers
                        await context.bot.send_message(
                            chat_id=driver.telegram_id,
                            text=f"🚨 **Annulation de réservation**\n\n"
                                 f"Un passager a annulé sa réservation :\n\n"
                                 f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
                                 f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                                 f"✅ **Place libérée !**\n"
                                 f"🆓 **Places disponibles:** {available_spots}/{trip.max_passengers}\n\n"
                                 f"⚠️ Remboursement à traiter manuellement.",
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logger.error(f"Erreur notification conducteur: {e}")
            
        except ImportError:
            # Fallback si le module n'existe pas
            booking.status = 'cancelled'
            db.commit()
            
            message = (
                f"✅ **Réservation annulée**\n\n"
                f"💬 **Le remboursement sera traité manuellement**\n"
                f"Contactez le support avec:\n"
                f"📝 Réservation #{booking_id}\n"
                f"📧 PayPal: {user.paypal_email}\n"
                f"💰 Montant: {booking.total_price:.2f} CHF"
            )
        
        await query.edit_message_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur lors de la confirmation d'annulation: {e}")
        await query.edit_message_text("❌ Erreur lors du traitement de l'annulation.")


async def add_paypal_for_refund(update: Update, context: CallbackContext):
    """Demande l'email PayPal pour le remboursement"""
    query = update.callback_query
    await query.answer()
    
    try:
        booking_id = query.data.split(':')[1]
        
        message = (
            f"📧 **Ajouter votre email PayPal**\n\n"
            f"Pour recevoir le remboursement automatique, "
            f"veuillez saisir votre adresse email PayPal en répondant à ce message.\n\n"
            f"💡 **Important:** L'email doit être exactement "
            f"celui associé à votre compte PayPal.\n\n"
            f"✍️ **Tapez votre email PayPal maintenant:**"
        )
        
        # Stocker l'ID de réservation pour la suite
        context.user_data['pending_refund_booking_id'] = booking_id
        
        await query.edit_message_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur lors de la demande d'email PayPal: {e}")
        await query.edit_message_text("❌ Erreur.")


# Handlers exportés
booking_cancellation_handler = CallbackQueryHandler(handle_booking_cancellation, pattern="^cancel_booking:\d+$")
confirm_cancellation_handler = CallbackQueryHandler(confirm_booking_cancellation, pattern="^confirm_cancel_booking:\d+$")
add_paypal_handler = CallbackQueryHandler(add_paypal_for_refund, pattern="^add_paypal_for_refund:\d+$")
