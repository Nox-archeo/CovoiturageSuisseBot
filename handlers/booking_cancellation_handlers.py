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
        price = booking.total_price or booking.amount or 0
        if not price or not trip.departure_time:
            logger.error(f"❌ Données incomplètes - price: {price}, departure_time: {trip.departure_time}")
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
            f"💰 **Montant à rembourser:** {price:.2f} CHF\n\n"
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
        
        # Calculer le prix (utiliser amount si total_price n'existe pas)
        price = booking.total_price or booking.amount or 0
        
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
                f"💰 **Montant à rembourser:** {price:.2f} CHF"
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
                # Marquer la réservation comme annulée
                booking.status = 'cancelled'
                booking.payment_status = 'refunded'
                db.commit()
                
                message = (
                    f"✅ **Annulation confirmée !**\n\n"
                    f"💰 **Remboursement de {price:.2f} CHF traité**\n"
                    f"📧 Envoyé sur: {user.paypal_email}\n\n"
                    f"⏱️ Le remboursement apparaîtra sur votre compte PayPal "
                    f"dans les minutes qui suivent."
                )
                
                # Notifier le conducteur
                try:
                    trip = booking.trip
                    driver = trip.driver
                    if driver and driver.telegram_id:
                        await context.bot.send_message(
                            chat_id=driver.telegram_id,
                            text=f"📝 **Réservation annulée**\n\n"
                                 f"Un passager a annulé sa réservation pour votre trajet "
                                 f"{trip.departure_city} → {trip.arrival_city} "
                                 f"le {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}.\n\n"
                                 f"Réservation #{booking_id} - Remboursement automatique effectué.",
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logger.error(f"Erreur notification conducteur: {e}")
                
            else:
                message = (
                    f"⚠️ **Annulation en cours**\n\n"
                    f"Votre réservation a été annulée mais le remboursement "
                    f"automatique a échoué.\n\n"
                    f"💬 **Contactez le support** avec cette information:\n"
                    f"📝 Réservation #{booking_id}\n"
                    f"📧 PayPal: {user.paypal_email}\n\n"
                    f"Le remboursement sera traité manuellement."
                )
                
                # Marquer quand même comme annulé
                booking.status = 'cancelled'
                db.commit()
            
            # 🔥 CORRECTION: Notifier TOUJOURS le conducteur, même si remboursement échoué
            try:
                trip = booking.trip
                driver = trip.driver if trip else None
                if driver and driver.telegram_id:
                    refund_status = "automatique effectué" if refund_success else "en cours (traitement manuel)"
                    await context.bot.send_message(
                        chat_id=driver.telegram_id,
                        text=f"📝 **Réservation annulée**\n\n"
                             f"Un passager a annulé sa réservation pour votre trajet "
                             f"{trip.departure_city} → {trip.arrival_city} "
                             f"le {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}.\n\n"
                             f"Réservation #{booking_id} - Remboursement {refund_status}.",
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ Notification conducteur envoyée pour annulation #{booking_id}")
            except Exception as e:
                logger.error(f"❌ Erreur notification conducteur: {e}")
            
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
                f"💰 Montant: {price:.2f} CHF"
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
