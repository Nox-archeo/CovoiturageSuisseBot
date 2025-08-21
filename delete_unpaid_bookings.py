#!/usr/bin/env python3
"""
Script pour supprimer DÉFINITIVEMENT toutes les réservations non payées
Les réservations non payées ne devraient jamais apparaître dans "Mes réservations"
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from database.models import Booking, Trip, User
from sqlalchemy import text

def delete_unpaid_bookings():
    """Supprimer toutes les réservations non payées de la base de données"""
    
    print("🚨 SUPPRESSION DES RÉSERVATIONS NON PAYÉES")
    print("=" * 60)
    
    db = get_db()
    
    try:
        # Compter d'abord toutes les réservations
        total_bookings = db.query(Booking).count()
        print(f"📊 Total des réservations dans la base: {total_bookings}")
        
        # Compter les réservations non payées
        unpaid_bookings = db.query(Booking).filter(
            Booking.is_paid != True
        ).all()
        
        print(f"❌ Réservations non payées trouvées: {len(unpaid_bookings)}")
        
        if unpaid_bookings:
            print("\n🔍 DÉTAILS DES RÉSERVATIONS NON PAYÉES:")
            for booking in unpaid_bookings:
                trip = booking.trip
                passenger = booking.passenger
                print(f"   • Réservation #{booking.id}")
                print(f"     Passager: {passenger.full_name if passenger else 'Inconnu'}")
                print(f"     Trajet: {trip.departure_city} → {trip.arrival_city}" if trip else "Trajet inconnu")
                print(f"     Payé: {booking.is_paid}")
                print(f"     Statut paiement: {booking.payment_status}")
                print(f"     PayPal ID: {booking.paypal_order_id}")
                print()
        
        print(f"\n⚠️  ATTENTION: Ceci va supprimer {len(unpaid_bookings)} réservations non payées!")
        input("Appuyez sur Entrée pour continuer ou Ctrl+C pour annuler...")
        
        # Supprimer les réservations non payées
        deleted_count = 0
        for booking in unpaid_bookings:
            trip = booking.trip
            if trip:
                # Restaurer les places si nécessaire
                trip.seats_available = min(trip.seats_available + 1, 4)
                print(f"   🔄 Places restaurées pour trajet #{trip.id}: {trip.seats_available}")
            
            db.delete(booking)
            deleted_count += 1
            print(f"   🗑️  Réservation #{booking.id} supprimée")
        
        db.commit()
        
        print(f"\n✅ SUPPRESSION TERMINÉE!")
        print(f"🗑️  {deleted_count} réservations non payées supprimées")
        
        # Vérification finale
        remaining_bookings = db.query(Booking).count()
        print(f"📊 Réservations restantes: {remaining_bookings}")
        
        # Vérifier qu'il ne reste que des réservations payées
        paid_bookings = db.query(Booking).filter(Booking.is_paid == True).count()
        print(f"✅ Réservations payées: {paid_bookings}")
        
        if remaining_bookings == paid_bookings:
            print("🎉 Parfait! Il ne reste que des réservations payées!")
        else:
            print(f"⚠️  Problème: {remaining_bookings - paid_bookings} réservations non payées restantes")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_unpaid_bookings()
