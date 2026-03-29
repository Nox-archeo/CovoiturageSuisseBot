#!/usr/bin/env python3
"""
Test du paiement PayPal pour le trajet 8
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db
from database.models import Trip, Booking, User
from paypal_utils import PayPalManager
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_paypal_payout():
    """Test du paiement PayPal pour le trajet 8"""
    try:
        db = get_db()
        
        # Récupérer le trajet 8
        trip = db.query(Trip).filter(Trip.id == 8).first()
        driver = db.query(User).filter(User.id == trip.driver_id).first()
        bookings = db.query(Booking).filter(
            Booking.trip_id == 8,
            Booking.is_paid == True
        ).all()
        
        total_amount = sum(booking.amount for booking in bookings)
        driver_amount = total_amount * 0.88  # 88% pour le conducteur
        
        print(f"💰 Test paiement PayPal:")
        print(f"  Montant total: {total_amount} CHF")
        print(f"  Montant conducteur (88%): {driver_amount:.2f} CHF")
        print(f"  Email PayPal: {driver.paypal_email}")
        print()
        
        # Initialiser PayPal
        paypal = PayPalManager()
        
        # Test 1: Vérifier le token d'accès
        print("🔐 Test 1: Token d'accès PayPal...")
        token = paypal.get_access_token()
        if token:
            print(f"  ✅ Token obtenu: {token[:20]}...")
        else:
            print("  ❌ Impossible d'obtenir le token")
            return
        
        print()
        
        # Test 2: Tenter le paiement
        print("💸 Test 2: Tentative de paiement...")
        trip_description = f"{trip.departure_city} → {trip.arrival_city} ({trip.departure_time.strftime('%d/%m/%Y')})"
        
        success, payout_details = paypal.payout_to_driver(
            driver_email=driver.paypal_email,
            amount=driver_amount,
            trip_description=trip_description
        )
        
        if success and payout_details:
            print("  ✅ PAIEMENT RÉUSSI !")
            print(f"  Batch ID: {payout_details.get('batch_id')}")
            print(f"  Détails: {payout_details}")
            
            # Mettre à jour le trajet
            trip.status = 'completed_paid'
            trip.payout_batch_id = payout_details.get('batch_id')
            trip.driver_amount = driver_amount
            db.commit()
            
        else:
            print("  ❌ PAIEMENT ÉCHOUÉ")
            print(f"  Détails: {payout_details}")
            
    except Exception as e:
        logger.error(f"Erreur test_paypal_payout: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_paypal_payout())
