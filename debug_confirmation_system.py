#!/usr/bin/env python3
"""
Debug du système de confirmation en production
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db
from database.models import Trip, Booking, User
from trip_confirmation_system import get_trip_confirmation_state
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_trip_8():
    """Debug spécifique du trajet 8"""
    try:
        db = get_db()
        
        print("🔍 === DEBUG TRAJET 8 === 🔍")
        print()
        
        # 1. État du trajet
        trip = db.query(Trip).filter(Trip.id == 8).first()
        if not trip:
            print("❌ Trajet 8 non trouvé")
            return
            
        print(f"🚗 TRAJET 8:")
        print(f"  Status: {trip.status}")
        print(f"  Driver ID: {trip.driver_id}")
        print(f"  Driver confirmed: {getattr(trip, 'driver_confirmed_completion', 'NON DEFINI')}")
        print(f"  Payment released: {getattr(trip, 'payment_released', 'NON DEFINI')}")
        print(f"  Route: {trip.departure_city} → {trip.arrival_city}")
        print(f"  Date: {trip.departure_time}")
        print()
        
        # 2. Conducteur
        driver = db.query(User).filter(User.id == trip.driver_id).first()
        if driver:
            print(f"🧑‍💼 CONDUCTEUR:")
            print(f"  User ID: {driver.id}")
            print(f"  Telegram ID: {driver.telegram_id}")
            print(f"  PayPal: {getattr(driver, 'paypal_email', 'NON DEFINI')}")
        print()
        
        # 3. TOUTES les réservations (pas seulement payées)
        all_bookings = db.query(Booking).filter(Booking.trip_id == 8).all()
        print(f"📋 TOUTES LES RESERVATIONS ({len(all_bookings)}):")
        for booking in all_bookings:
            passenger = db.query(User).filter(User.id == booking.passenger_id).first()
            print(f"  Booking {booking.id}:")
            print(f"    Passenger ID: {booking.passenger_id}")
            print(f"    Telegram ID: {passenger.telegram_id if passenger else 'INCONNU'}")
            print(f"    Status: {booking.status}")
            print(f"    Is paid: {booking.is_paid}")
            print(f"    Amount: {booking.amount}")
            print(f"    Passenger confirmed: {getattr(booking, 'passenger_confirmed_completion', 'NON DEFINI')}")
            print()
        
        # 4. Réservations payées ET confirmées uniquement
        paid_bookings = db.query(Booking).filter(
            Booking.trip_id == 8,
            Booking.is_paid == True,
            Booking.status == 'confirmed'
        ).all()
        print(f"💰 RESERVATIONS PAYEES + CONFIRMEES ({len(paid_bookings)}):")
        for booking in paid_bookings:
            print(f"  Booking {booking.id}: passenger_id={booking.passenger_id}, amount={booking.amount}")
        print()
        
        # 5. Test de l'état de confirmation
        confirmation_state = get_trip_confirmation_state(8, db)
        print(f"🔐 ETAT DES CONFIRMATIONS:")
        print(f"  Driver confirmed: {confirmation_state['driver_confirmed']}")
        print(f"  Passenger confirmations: {confirmation_state['passenger_confirmations']}")
        print(f"  All confirmed: {confirmation_state['all_confirmed']}")
        print()
        
        # 6. Diagnostics
        print("🩺 DIAGNOSTICS:")
        if not confirmation_state['driver_confirmed']:
            print("  ❌ Le conducteur n'a PAS confirmé")
        else:
            print("  ✅ Le conducteur a confirmé")
            
        if len(paid_bookings) == 0:
            print("  ❌ AUCUNE réservation payée + confirmée trouvée")
            print("  💡 C'est la raison principale pourquoi le paiement ne se déclenche pas !")
        else:
            print(f"  ✅ {len(paid_bookings)} réservations payées trouvées")
            
        if not getattr(driver, 'paypal_email', None):
            print("  ❌ Le conducteur n'a PAS d'email PayPal configuré")
        else:
            print(f"  ✅ Email PayPal conducteur: {driver.paypal_email}")
            
        print()
        print("🎯 CONCLUSION:")
        if len(paid_bookings) == 0:
            print("   Le système n'effectue AUCUN paiement car il n'y a AUCUNE réservation")
            print("   payée avec status='confirmed' pour ce trajet.")
            print("   Les confirmations dans les logs concernent probablement des réservations")
            print("   non-payées ou avec un autre statut.")
        elif not confirmation_state['all_confirmed']:
            print("   Les confirmations ne sont pas complètes.")
        else:
            print("   Toutes les conditions sont remplies pour le paiement!")
            
    except Exception as e:
        logger.error(f"Erreur debug_trip_8: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_trip_8()
