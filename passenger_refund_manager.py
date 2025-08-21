#!/usr/bin/env python3
"""
Gestionnaire de remboursements automatiques pour les annulations de passagers
"""

import logging
from datetime import datetime
from database.models import Booking, User
from database import get_db
from paypal_utils import paypal_manager

logger = logging.getLogger(__name__)

async def process_passenger_refund(booking_id: int, bot=None) -> bool:
    """
    Traite le remboursement automatique d'une réservation annulée par un passager
    
    Args:
        booking_id: ID de la réservation à rembourser
        bot: Instance du bot Telegram pour les notifications
        
    Returns:
        bool: True si le remboursement a réussi, False sinon
    """
    try:
        db = get_db()
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking:
            logger.error(f"❌ Réservation {booking_id} non trouvée")
            return False
        
        if not booking.is_paid:
            logger.error(f"❌ Réservation {booking_id} non payée")
            return False
        
        if booking.status == 'cancelled':
            logger.warning(f"⚠️ Réservation {booking_id} déjà annulée")
            return False
        
        # Récupérer l'utilisateur passager
        passenger = db.query(User).filter(User.id == booking.passenger_id).first()
        if not passenger:
            logger.error(f"❌ Passager non trouvé pour la réservation {booking_id}")
            return False
        
        if not passenger.paypal_email:
            logger.error(f"❌ Email PayPal manquant pour le passager {passenger.id}")
            return False
        
        # Calculer le montant du remboursement (montant total payé)
        refund_amount = booking.total_price
        
        logger.info(f"🔄 Traitement remboursement: {refund_amount:.2f} CHF pour réservation #{booking_id}")
        
        # Traiter le remboursement via PayPal
        refund_result = await paypal_manager.process_refund(
            payment_id=booking.paypal_payment_id,
            refund_amount=refund_amount,
            recipient_email=passenger.paypal_email,
            reason=f"Annulation réservation #{booking_id}"
        )
        
        if refund_result['success']:
            # Enregistrer les détails du remboursement
            booking.refund_id = refund_result.get('refund_id')
            booking.refund_amount = refund_amount
            booking.refund_date = datetime.utcnow()
            booking.status = 'cancelled'
            booking.payment_status = 'refunded'
            
            # CORRECTION CRITIQUE: Remettre la place disponible
            trip = booking.trip
            if trip:
                trip.seats_available += 1
                logger.info(f"🔼 Place remise: {trip.seats_available - 1} → {trip.seats_available} pour trajet {trip.id}")
            
            db.commit()
            
            logger.info(f"✅ Remboursement réussi: {refund_amount:.2f} CHF vers {passenger.paypal_email}")
            
            # Envoyer une notification au passager
            if bot and passenger.telegram_id:
                try:
                    # Utiliser la méthode correcte selon le type de bot
                    if hasattr(bot, 'send_message'):
                        await bot.send_message(
                            chat_id=passenger.telegram_id,
                            text=f"💰 **Remboursement confirmé !**\n\n"
                                 f"Votre remboursement de {refund_amount:.2f} CHF "
                                 f"a été traité avec succès.\n\n"
                                 f"📧 Envoyé sur: {passenger.paypal_email}\n"
                                 f"🆔 Référence: {refund_result.get('refund_id', 'N/A')}\n\n"
                                 f"⏱️ Le montant apparaîtra sur votre compte PayPal "
                                 f"dans les minutes qui suivent.",
                            parse_mode='Markdown'
                        )
                    elif hasattr(bot, 'bot') and hasattr(bot.bot, 'send_message'):
                        await bot.bot.send_message(
                            chat_id=passenger.telegram_id,
                            text=f"💰 **Remboursement confirmé !**\n\n"
                                 f"Votre remboursement de {refund_amount:.2f} CHF "
                                 f"a été traité avec succès.\n\n"
                                 f"📧 Envoyé sur: {passenger.paypal_email}\n"
                                 f"🆔 Référence: {refund_result.get('refund_id', 'N/A')}\n\n"
                                 f"⏱️ Le montant apparaîtra sur votre compte PayPal "
                                 f"dans les minutes qui suivent.",
                            parse_mode='Markdown'
                        )
                    logger.info(f"✅ Notification remboursement envoyée au passager {passenger.telegram_id}")
                except Exception as e:
                    logger.error(f"❌ Erreur notification passager: {e}")
            
            # NOUVEAU: Notifier le conducteur de l'annulation
            trip = booking.trip
            if bot and trip and trip.driver and trip.driver.telegram_id:
                try:
                    driver_message = (
                        f"⚠️ **Annulation de réservation**\n\n"
                        f"**Passager:** {passenger.full_name or passenger.username or 'Nom non disponible'}\n"
                        f"**Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
                        f"**Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                        f"**Montant remboursé:** {refund_amount:.2f} CHF\n\n"
                        f"📍 **Places disponibles:** {trip.seats_available + 1} → {trip.seats_available + 1}\n"
                        f"💡 La place est à nouveau disponible pour d'autres passagers."
                    )
                    
                    if hasattr(bot, 'send_message'):
                        await bot.send_message(
                            chat_id=trip.driver.telegram_id,
                            text=driver_message,
                            parse_mode='Markdown'
                        )
                    elif hasattr(bot, 'bot') and hasattr(bot.bot, 'send_message'):
                        await bot.bot.send_message(
                            chat_id=trip.driver.telegram_id,
                            text=driver_message,
                            parse_mode='Markdown'
                        )
                    
                    logger.info(f"✅ Notification annulation envoyée au conducteur {trip.driver.telegram_id}")
                except Exception as e:
                    logger.error(f"❌ Erreur notification conducteur: {e}")
            
            return True
        
        else:
            error_msg = refund_result.get('error', 'Erreur inconnue')
            logger.error(f"❌ Échec remboursement: {error_msg}")
            
            # Envoyer une notification d'échec
            if bot and passenger.telegram_id:
                try:
                    # Utiliser la méthode correcte selon le type de bot
                    if hasattr(bot, 'send_message'):
                        await bot.send_message(
                            chat_id=passenger.telegram_id,
                            text=f"⚠️ **Problème de remboursement**\n\n"
                                 f"Le remboursement automatique de {refund_amount:.2f} CHF "
                                 f"a échoué.\n\n"
                                 f"🔧 **Raison:** {error_msg}\n\n"
                                 f"💬 **Action requise:** Contactez le support avec "
                                 f"le numéro de réservation #{booking_id}.\n\n"
                                 f"📧 Votre email PayPal: {passenger.paypal_email}",
                            parse_mode='Markdown'
                        )
                    elif hasattr(bot, 'bot') and hasattr(bot.bot, 'send_message'):
                        await bot.bot.send_message(
                            chat_id=passenger.telegram_id,
                            text=f"⚠️ **Problème de remboursement**\n\n"
                                 f"Le remboursement automatique de {refund_amount:.2f} CHF "
                                 f"a échoué.\n\n"
                                 f"🔧 **Raison:** {error_msg}\n\n"
                                 f"💬 **Action requise:** Contactez le support avec "
                                 f"le numéro de réservation #{booking_id}.\n\n"
                                 f"📧 Votre email PayPal: {passenger.paypal_email}",
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logger.error(f"❌ Erreur notification échec: {e}")
            
            return False
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement du remboursement {booking_id}: {e}")
        import traceback
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        return False


async def validate_paypal_email(email: str) -> bool:
    """
    Valide une adresse email PayPal
    
    Args:
        email: Adresse email à valider
        
    Returns:
        bool: True si l'email est valide
    """
    import re
    
    # Validation basique d'email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False
    
    # Vérifications supplémentaires PayPal
    email = email.lower().strip()
    
    # PayPal n'accepte pas certains domaines temporaires
    blocked_domains = [
        '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
        'mailinator.com', 'yopmail.com'
    ]
    
    domain = email.split('@')[1]
    if domain in blocked_domains:
        return False
    
    return True


async def get_refund_history(user_id: int) -> list:
    """
    Récupère l'historique des remboursements pour un utilisateur
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        list: Liste des remboursements
    """
    try:
        db = get_db()
        
        refunds = db.query(Booking).filter(
            Booking.passenger_id == user_id,
            Booking.payment_status == 'refunded',
            Booking.refund_id.isnot(None)
        ).order_by(Booking.refund_date.desc()).all()
        
        refund_history = []
        for booking in refunds:
            refund_history.append({
                'booking_id': booking.id,
                'trip_route': f"{booking.trip.departure_city} → {booking.trip.arrival_city}",
                'trip_date': booking.trip.departure_time,
                'refund_amount': booking.refund_amount,
                'refund_date': booking.refund_date,
                'refund_id': booking.refund_id
            })
        
        return refund_history
    
    except Exception as e:
        logger.error(f"Erreur récupération historique remboursements: {e}")
        return []
