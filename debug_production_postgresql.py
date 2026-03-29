#!/usr/bin/env python3
"""
Script pour diagnostiquer le problème de paiement en production PostgreSQL
"""

import os
import sys
import logging
from datetime import date, datetime

# Forcer l'utilisation de PostgreSQL en production
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://...')  # Mettre la vraie URL

sys.path.append('/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db
from database.models import Trip, Booking, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_production_issue():
    """Debug du problème de paiement en production PostgreSQL"""
    try:
        print("🔍 === DIAGNOSTIC PRODUCTION POSTGRESQL ===")
        print()
        
        db = get_db()
        
        # 1. Vérifier la connexion
        print("🔗 Test connexion PostgreSQL...")
        try:
            # Test simple
            result = db.execute("SELECT 1").fetchone()
            print("  ✅ Connexion PostgreSQL OK")
        except Exception as e:
            print(f"  ❌ Erreur connexion: {e}")
            return
        
        # 2. Chercher les trajets d'aujourd'hui (22/08/2025)
        today = date(2025, 8, 22)
        print(f"📅 Recherche trajets du {today}...")
        
        all_trips_today = db.query(Trip).filter(
            Trip.departure_time >= datetime(2025, 8, 22, 0, 0),
            Trip.departure_time < datetime(2025, 8, 23, 0, 0)
        ).all()
        
        print(f"  Trouvé {len(all_trips_today)} trajets aujourd'hui")
        
        for trip in all_trips_today:
            print(f"    Trip {trip.id}: {trip.departure_city} → {trip.arrival_city}")
            print(f"      Heure: {trip.departure_time.strftime('%H:%M')}")
            print(f"      Driver ID: {trip.driver_id}")
            print(f"      Status: {trip.status}")
            
            # Vérifier les confirmations
            driver_confirmed = getattr(trip, 'driver_confirmed_completion', False)
            print(f"      Driver confirmed: {driver_confirmed}")
            
            # Vérifier les réservations
            bookings = db.query(Booking).filter(Booking.trip_id == trip.id).all()
            print(f"      Réservations: {len(bookings)}")
            
            for booking in bookings:
                passenger_confirmed = getattr(booking, 'passenger_confirmed_completion', False)
                print(f"        Booking {booking.id}: passenger_id={booking.passenger_id}, paid={booking.is_paid}, passenger_confirmed={passenger_confirmed}")
            
            print()
        
        # 3. Chercher spécifiquement le trajet Posieux → Corpataux-Magnedens
        print("🎯 Recherche trajet Posieux → Corpataux-Magnedens...")
        posieux_trips = db.query(Trip).filter(
            Trip.departure_city.ilike('%posieux%'),
            Trip.arrival_city.ilike('%corpataux%')
        ).all()
        
        print(f"  Trouvé {len(posieux_trips)} trajets Posieux → Corpataux")
        
        for trip in posieux_trips:
            if trip.departure_time.date() == today:
                print(f"    *** TRAJET CIBLE TROUVE: Trip {trip.id} ***")
                
                # Analyse complète
                driver = db.query(User).filter(User.id == trip.driver_id).first()
                bookings = db.query(Booking).filter(Booking.trip_id == trip.id).all()
                
                print(f"      Conducteur: {driver.full_name if driver and driver.full_name else 'INCONNU'}")
                print(f"      Email PayPal: {getattr(driver, 'paypal_email', 'NON DEFINI') if driver else 'DRIVER NON TROUVE'}")
                print(f"      Driver confirmed: {getattr(trip, 'driver_confirmed_completion', False)}")
                print(f"      Status: {trip.status}")
                
                total_paid = 0
                for booking in bookings:
                    if booking.is_paid:
                        total_paid += booking.amount or 0
                    passenger_confirmed = getattr(booking, 'passenger_confirmed_completion', False)
                    print(f"        Réservation {booking.id}: {booking.amount} CHF, payée={booking.is_paid}, confirmée={passenger_confirmed}")
                
                print(f"      Total payé: {total_paid} CHF")
                print(f"      Montant conducteur (88%): {total_paid * 0.88:.2f} CHF")
                
                # Diagnostic final
                if getattr(trip, 'driver_confirmed_completion', False) and any(getattr(b, 'passenger_confirmed_completion', False) for b in bookings if b.is_paid):
                    print("      🎉 TOUTES LES CONDITIONS REMPLIES POUR PAIEMENT")
                    if trip.status == 'payment_failed':
                        print("      ❌ MAIS STATUS = payment_failed (erreur PayPal)")
                    elif trip.status == 'payment_pending_manual':
                        print("      ⏳ STATUS = payment_pending_manual (paiement manuel requis)")
                    else:
                        print(f"      ❓ STATUS = {trip.status}")
                else:
                    print("      ❌ Conditions non remplies pour paiement")
                
                return trip.id
        
        print("❌ Aucun trajet Posieux → Corpataux-Magnedens trouvé pour aujourd'hui")
        return None
        
    except Exception as e:
        logger.error(f"Erreur debug_production_issue: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_production_issue()
