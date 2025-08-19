#!/usr/bin/env python3
"""
Investigation de la réservation PayPal en production
"""

import os
import sys
sys.path.append('/Users/margaux/CovoiturageSuisse')

# Simuler l'environnement de production pour la base de données
def investigate_production_payment():
    """Investigue la réservation PayPal de 1 CHF en production"""
    
    print("🕵️ INVESTIGATION PAIEMENT PAYPAL 1 CHF")
    print("=" * 50)
    
    # Utiliser la session de base de données de production
    try:
        from database.db_manager import get_db
        from database.models import Booking, Trip, User
        
        # Obtenir une session de base de données
        db = get_db()
        
        print("🔍 Recherche des dernières réservations...")
        
        # Chercher les réservations récentes (dernières 24h)
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        
        recent_bookings = db.query(Booking).filter(
            Booking.booking_date >= yesterday
        ).order_by(Booking.id.desc()).limit(10).all()
        
        print(f"\n📊 {len(recent_bookings)} réservations récentes trouvées:")
        for booking in recent_bookings:
            print(f"  ID: {booking.id}")
            print(f"  Passenger: {booking.passenger_id}")
            print(f"  Trip: {booking.trip_id}")
            print(f"  Amount: {booking.amount}")
            print(f"  Status: {booking.status}")
            print(f"  Is_Paid: {booking.is_paid}")
            print(f"  PayPal_ID: {booking.paypal_payment_id}")
            print(f"  Payment_Status: {booking.payment_status}")
            print(f"  Date: {booking.booking_date}")
            print("  " + "─" * 40)
        
        # Chercher spécifiquement les paiements avec montant de 1 CHF
        print(f"\n💰 Recherche des paiements de 1 CHF...")
        one_chf_bookings = db.query(Booking).filter(
            Booking.amount == 1.0
        ).order_by(Booking.id.desc()).limit(5).all()
        
        if one_chf_bookings:
            print(f"🎯 {len(one_chf_bookings)} réservation(s) de 1 CHF trouvée(s):")
            for booking in one_chf_bookings:
                print(f"  🔥 RÉSERVATION 1 CHF:")
                print(f"     ID: {booking.id}")
                print(f"     Passenger: {booking.passenger_id}")
                print(f"     Trip: {booking.trip_id}")
                print(f"     Status: {booking.status}")
                print(f"     Is_Paid: {booking.is_paid}")
                print(f"     PayPal_ID: {booking.paypal_payment_id}")
                print(f"     Payment_Status: {booking.payment_status}")
                print(f"     Date: {booking.booking_date}")
        else:
            print("❌ Aucune réservation de 1 CHF trouvée")
        
        # Chercher les paiements PayPal non traités
        print(f"\n🔍 Recherche des paiements PayPal en attente...")
        pending_paypal = db.query(Booking).filter(
            Booking.paypal_payment_id.isnot(None),
            Booking.is_paid == False
        ).order_by(Booking.id.desc()).limit(10).all()
        
        if pending_paypal:
            print(f"⏳ {len(pending_paypal)} paiement(s) PayPal en attente:")
            for booking in pending_paypal:
                print(f"  ID: {booking.id}, PayPal: {booking.paypal_payment_id}, Amount: {booking.amount}")
        else:
            print("✅ Aucun paiement PayPal en attente")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_production_payment()
