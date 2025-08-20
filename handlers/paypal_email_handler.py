#!/usr/bin/env python3
"""
Handler pour traiter l'email PayPal saisi par l'utilisateur pour les remboursements
"""

import logging
import re
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from database.models import User
from database import get_db

logger = logging.getLogger(__name__)

async def handle_paypal_email_for_refund(update: Update, context: CallbackContext):
    """Traite l'email PayPal saisi pour un remboursement"""
    
    # Vérifier si l'utilisateur a une réservation en attente de remboursement
    if 'pending_refund_booking_id' not in context.user_data:
        return
    
    booking_id = context.user_data['pending_refund_booking_id']
    email = update.message.text.strip()
    
    # Validation basique de l'email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        await update.message.reply_text(
            "❌ **Format d'email invalide**\n\n"
            "Veuillez saisir une adresse email valide :\n"
            "📧 exemple@paypal.com",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await update.message.reply_text("❌ Erreur: utilisateur non trouvé.")
            return
        
        # Mettre à jour l'email PayPal de l'utilisateur
        user.paypal_email = email
        db.commit()
        
        # Nettoyer les données temporaires
        del context.user_data['pending_refund_booking_id']
        
        await update.message.reply_text(
            f"✅ **Email PayPal enregistré !**\n\n"
            f"📧 **Email:** {email}\n\n"
            f"🔄 **Traitement du remboursement en cours...**",
            parse_mode='Markdown'
        )
        
        # Traiter le remboursement maintenant
        try:
            from passenger_refund_manager import process_passenger_refund
            from database.models import Booking
            
            booking = db.query(Booking).filter(
                Booking.id == booking_id,
                Booking.passenger_id == user.id
            ).first()
            
            if not booking:
                await update.message.reply_text("❌ Réservation non trouvée.")
                return
            
            refund_success = await process_passenger_refund(booking_id, context.bot)
            
            if refund_success:
                # Marquer la réservation comme annulée
                booking.status = 'cancelled'
                booking.payment_status = 'refunded'
                db.commit()
                
                message = (
                    f"✅ **Annulation confirmée !**\n\n"
                    f"💰 **Remboursement de {booking.total_price:.2f} CHF traité**\n"
                    f"📧 Envoyé sur: {email}\n\n"
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
                    f"📧 PayPal: {email}\n\n"
                    f"Le remboursement sera traité manuellement."
                )
                
                # Marquer quand même comme annulé
                booking.status = 'cancelled'
                db.commit()
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except ImportError:
            # Fallback si le module n'existe pas
            from database.models import Booking
            
            booking = db.query(Booking).filter(
                Booking.id == booking_id,
                Booking.passenger_id == user.id
            ).first()
            
            if booking:
                booking.status = 'cancelled'
                db.commit()
            
            message = (
                f"✅ **Réservation annulée**\n\n"
                f"💬 **Le remboursement sera traité manuellement**\n"
                f"Contactez le support avec:\n"
                f"📝 Réservation #{booking_id}\n"
                f"📧 PayPal: {email}\n"
                f"💰 Montant: {booking.total_price:.2f} CHF"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'email PayPal: {e}")
        await update.message.reply_text("❌ Erreur lors du traitement.")


# Handler exporté
paypal_email_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    handle_paypal_email_for_refund
)
