#!/usr/bin/env python3
"""
Solution temporaire: notification manuelle des paiements
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db
from database.models import Trip, Booking, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def manual_payment_notification():
    """Notifie manuellement le paiement requis"""
    try:
        db = get_db()
        
        # Traiter le trajet 8
        trip = db.query(Trip).filter(Trip.id == 8).first()
        driver = db.query(User).filter(User.id == trip.driver_id).first()
        bookings = db.query(Booking).filter(
            Booking.trip_id == 8,
            Booking.is_paid == True
        ).all()
        
        total_amount = sum(booking.amount for booking in bookings)
        driver_amount = total_amount * 0.88
        commission = total_amount * 0.12
        
        # Marquer comme paiement manuel requis
        trip.status = 'payment_pending_manual'
        trip.driver_amount = driver_amount
        trip.commission_amount = commission
        db.commit()
        
        print("📧 === NOTIFICATION PAIEMENT MANUEL ===")
        print()
        print(f"🚗 TRAJET: {trip.departure_city} → {trip.arrival_city}")
        print(f"📅 DATE: {trip.departure_time.strftime('%d/%m/%Y')}")
        print(f"👤 CONDUCTEUR: {driver.paypal_email}")
        print(f"💰 MONTANT À PAYER: {driver_amount:.2f} CHF")
        print(f"🏦 COMMISSION: {commission:.2f} CHF")
        print()
        print("✅ Action requise: Effectuer le paiement manuellement via PayPal")
        print(f"📧 Envoyer {driver_amount:.2f} CHF à: {driver.paypal_email}")
        print(f"📝 Description: Paiement conducteur - {trip.departure_city} → {trip.arrival_city}")
        print()
        
        # Créer un fichier de suivi
        with open('/Users/margaux/CovoiturageSuisse/paiements_manuels.txt', 'a') as f:
            f.write(f"[{trip.departure_time.strftime('%d/%m/%Y %H:%M')}] "
                   f"Trajet {trip.id}: {driver_amount:.2f} CHF → {driver.paypal_email} "
                   f"({trip.departure_city} → {trip.arrival_city})\\n")
        
        print("📄 Paiement ajouté au fichier paiements_manuels.txt")
        
    except Exception as e:
        logger.error(f"Erreur manual_payment_notification: {e}")

if __name__ == "__main__":
    manual_payment_notification()
