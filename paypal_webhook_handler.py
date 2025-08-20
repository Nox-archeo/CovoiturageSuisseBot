#!/usr/bin/env python3
"""
Webhook PayPal pour détecter les nouveaux paiements et déclencher les remboursements automatiques
"""

import logging
from datetime import datetime
from database.models import Booking, Trip, User
from database import get_db
from fixed_auto_refund_manager import trigger_automatic_refunds_fixed

logger = logging.getLogger(__name__)

async def handle_payment_completion(payment_id: str, bot=None) -> bool:
    """
    Gère la completion d'un paiement et déclenche les remboursements si nécessaire
    
    Args:
        payment_id: ID du paiement PayPal
        bot: Instance du bot Telegram
        
    Returns:
        True si le traitement a réussi
    """
    try:
        logger.info(f"🔥 Traitement de la completion du paiement: {payment_id}")
        
        # Obtenir la session SQLAlchemy
        db = get_db()
        
        # Essayer de récupérer les détails complets du paiement PayPal pour obtenir custom_id
        paypal_payment_details = None
        try:
            import requests
            from paypal_utils import PayPalManager
            
            paypal_manager = PayPalManager()
            access_token = paypal_manager.get_access_token()
            if access_token:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}'
                }
                response = requests.get(
                    f"https://api.paypal.com/v2/payments/captures/{payment_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    paypal_payment_details = response.json()
                    logger.info(f"✅ Détails PayPal récupérés pour: {payment_id}")
                else:
                    logger.warning(f"⚠️ Impossible de récupérer les détails PayPal: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la récupération des détails PayPal: {e}")
        
        # Rechercher la réservation par custom_id si disponible
        booking = None
        custom_id = None
        
        if paypal_payment_details:
            custom_id = paypal_payment_details.get('custom_id')
            if custom_id:
                try:
                    booking = db.query(Booking).filter(Booking.id == int(custom_id)).first()
                    logger.info(f"🔍 Recherche par custom_id={custom_id}: {'Trouvé' if booking else 'Non trouvé'}")
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ custom_id invalide: {custom_id}")
        
        # Fallback: rechercher par payment_id
        if not booking:
            booking = db.query(Booking).filter(
                Booking.paypal_payment_id == payment_id
            ).first()
            logger.info(f"🔍 Recherche par payment_id={payment_id}: {'Trouvé' if booking else 'Non trouvé'}")
        
        if not booking:
            logger.error(f"❌ Aucune réservation trouvée pour payment_id={payment_id}, custom_id={custom_id}")
            return False
        
        logger.info(f"✅ Réservation trouvée: ID={booking.id}, Trip={booking.trip_id}")
        
        # Marquer le paiement comme confirmé
        booking.is_paid = True
        booking.payment_status = "completed"
        booking.status = "confirmed"
        
        if not booking.paypal_payment_id:
            booking.paypal_payment_id = payment_id
        
        db.commit()
        logger.info(f"✅ Réservation {booking.id} marquée comme payée et confirmée")
        
        # Envoyer notifications
        if bot:
            # Notification au passager - CORRECTION: utiliser telegram_id
            try:
                # Si c'est une Application, utiliser bot.bot, sinon utiliser bot directement
                telegram_bot = bot.bot if hasattr(bot, 'bot') else bot
                
                # Récupérer l'utilisateur passager pour avoir son telegram_id
                passenger = db.query(User).filter(User.id == booking.passenger_id).first()
                if passenger and passenger.telegram_id:
                    await telegram_bot.send_message(
                        chat_id=passenger.telegram_id,
                        text=f"✅ *Réservation confirmée !*\n\n"
                             f"Votre paiement a été traité avec succès.\n"
                             f"Détails de votre réservation #{booking.id}",
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ Notification envoyée au passager telegram_id={passenger.telegram_id}")
                else:
                    logger.error(f"❌ Passager non trouvé ou telegram_id manquant: passenger_id={booking.passenger_id}")
            except Exception as e:
                logger.error(f"❌ Erreur notification passager: {e}")
            
            # Notification au conducteur - CORRECTION: utiliser telegram_id
            trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
            if trip:
                try:
                    telegram_bot = bot.bot if hasattr(bot, 'bot') else bot
                    
                    # Récupérer l'utilisateur conducteur pour avoir son telegram_id
                    driver = db.query(User).filter(User.id == trip.driver_id).first()
                    if driver and driver.telegram_id:
                        await telegram_bot.send_message(
                            chat_id=driver.telegram_id,
                            text=f"🎉 *Nouvelle réservation confirmée !*\n\n"
                                 f"Un passager a confirmé sa réservation pour votre trajet.\n"
                                 f"Réservation #{booking.id}",
                            parse_mode='Markdown'
                        )
                        logger.info(f"✅ Notification envoyée au conducteur telegram_id={driver.telegram_id}")
                    else:
                        logger.error(f"❌ Conducteur non trouvé ou telegram_id manquant: driver_id={trip.driver_id}")
                except Exception as e:
                    logger.error(f"❌ Erreur notification conducteur: {e}")
        
        # Déclencher les remboursements automatiques si nécessaire
        await trigger_automatic_refunds_fixed(booking.trip_id, bot)
        
        logger.info(f"✅ Traitement du paiement {payment_id} terminé avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement du paiement {payment_id}: {e}")
        import traceback
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        return False

async def handle_paypal_webhook(webhook_data: dict, bot=None) -> bool:
    """
    Traite les webhooks PayPal
    
    Args:
        webhook_data: Données du webhook PayPal
        bot: Instance du bot Telegram
        
    Returns:
        True si le webhook a été traité avec succès
    """
    try:
        event_type = webhook_data.get('event_type')
        
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            # Paiement complété
            resource = webhook_data.get('resource', {})
            payment_id = resource.get('id')
            
            if payment_id:
                return await handle_payment_completion(payment_id, bot)
        
        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            # Paiement refusé
            resource = webhook_data.get('resource', {})
            payment_id = resource.get('id')
            
            logger.warning(f"Paiement refusé: {payment_id}")
            # TODO: Gérer les paiements refusés
        
        # Autres types d'événements peuvent être ajoutés ici
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook PayPal: {e}")
        return False
