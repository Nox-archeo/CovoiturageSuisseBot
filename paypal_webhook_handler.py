#!/usr/bin/env python3
"""
Webhook PayPal pour détecter les nouveaux paiements et déclencher les remboursements automatiques
"""

import logging
from datetime import datetime
from database.models import Booking, Trip
from database import get_db
from auto_refund_manager import trigger_automatic_refunds

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
        db = get_db()
        
        # Trouver la réservation correspondante
        booking = db.query(Booking).filter(
            Booking.paypal_payment_id == payment_id
        ).first()
        
        if not booking:
            logger.warning(f"Aucune réservation trouvée pour le paiement {payment_id}")
            return False
        
        # Marquer le paiement comme complété
        booking.payment_status = 'completed'
        booking.status = 'confirmed'
        db.commit()
        
        logger.info(f"Paiement complété pour la réservation {booking.id}")
        
        # Vérifier s'il faut déclencher des remboursements automatiques
        trip_id = booking.trip_id
        
        # Compter le nombre de passagers payants
        paid_passengers_count = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.payment_status == 'completed'
        ).count()
        
        logger.info(f"Trajet {trip_id}: {paid_passengers_count} passagers payants")
        
        # Si c'est le 2ème passager ou plus, déclencher les remboursements
        if paid_passengers_count >= 2:
            logger.info(f"Déclenchement des remboursements automatiques pour le trajet {trip_id}")
            success = await trigger_automatic_refunds(trip_id, bot)
            
            if success:
                logger.info(f"Remboursements automatiques traités avec succès pour le trajet {trip_id}")
            else:
                logger.error(f"Erreur lors des remboursements automatiques pour le trajet {trip_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la completion de paiement {payment_id}: {e}")
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
