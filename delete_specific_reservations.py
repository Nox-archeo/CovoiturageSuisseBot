#!/usr/bin/env python3
"""
Script pour supprimer les 3 réservations spécifiques que tu vois dans le bot
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import Booking, Trip, User
from database.db_manager import get_db
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_production_db():
    """Connexion à la base de données de production (PostgreSQL sur Render)"""
    try:
        # URL de la base PostgreSQL (la vraie utilisée par le bot)
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL non trouvée dans les variables d'environnement")
            return None
            
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        logger.error(f"❌ Erreur connexion base de données: {e}")
        return None

def delete_specific_reservations():
    """Supprimer les 3 réservations spécifiques avec PayPal IDs"""
    
    paypal_ids_to_delete = [
        "4TV74502NL",  # Réservation 1 non payée
        "9LM59635J7",  # Réservation 2 non payée  
        # Note: On garde la 3ème (payée) pour l'instant pour tests
    ]
    
    db = get_db()  # Utilise la même connexion que le bot
    if not db:
        return False
        
    try:
        logger.info("🔍 Recherche des réservations à supprimer...")
        
        # Chercher toutes les réservations avec ces PayPal IDs
        bookings_to_delete = db.query(Booking).filter(
            Booking.paypal_payment_id.in_(paypal_ids_to_delete)
        ).all()
        
        logger.info(f"📋 Trouvé {len(bookings_to_delete)} réservations à supprimer")
        
        for booking in bookings_to_delete:
            logger.info(f"🗑️ Suppression réservation:")
            logger.info(f"   - ID: {booking.id}")
            logger.info(f"   - PayPal: {booking.paypal_payment_id}")
            logger.info(f"   - Payé: {booking.is_paid}")
            logger.info(f"   - Montant: {booking.amount} CHF")
            
            # Restaurer les places dans le trajet si la réservation était payée
            if booking.is_paid and booking.trip:
                booking.trip.seats_available += 1
                logger.info(f"   - Places restaurées: {booking.trip.seats_available}")
            
            # Supprimer la réservation
            db.delete(booking)
        
        # Valider les changements
        db.commit()
        logger.info("✅ Réservations supprimées avec succès!")
        
        # Vérifier qu'il ne reste plus de réservations non payées
        remaining_unpaid = db.query(Booking).filter(
            Booking.is_paid == False
        ).count()
        
        remaining_paid = db.query(Booking).filter(
            Booking.is_paid == True
        ).count()
        
        logger.info(f"📊 Réservations restantes:")
        logger.info(f"   - Payées: {remaining_paid}")
        logger.info(f"   - Non payées: {remaining_unpaid}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🧹 Suppression des réservations spécifiques...")
    print("PayPal IDs à supprimer: 4TV74502NL, 9LM59635J7")
    
    if delete_specific_reservations():
        print("✅ Nettoyage terminé avec succès!")
    else:
        print("❌ Erreur lors du nettoyage")
