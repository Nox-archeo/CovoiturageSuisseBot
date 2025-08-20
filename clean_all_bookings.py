#!/usr/bin/env python3
"""
Script pour nettoyer TOUTES les réservations et remettre les places à jour
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database import get_db
from database.models import Booking, Trip
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_all_bookings_and_reset_seats():
    """Supprime toutes les réservations et remet les places à jour"""
    try:
        db = get_db()
        
        print("🧹 NETTOYAGE COMPLET DES RÉSERVATIONS")
        print("=" * 50)
        
        # 1. Lister toutes les réservations avant suppression
        all_bookings = db.query(Booking).all()
        print(f"📋 Réservations trouvées: {len(all_bookings)}")
        
        for booking in all_bookings:
            print(f"   • Booking #{booking.id}: Trip {booking.trip_id}, Status: {booking.status}, Payé: {booking.is_paid}")
        
        # 2. Supprimer TOUTES les réservations
        deleted_count = db.query(Booking).delete()
        print(f"🗑️ {deleted_count} réservations supprimées")
        
        # 3. Remettre toutes les places disponibles des trajets
        trips = db.query(Trip).all()
        print(f"\n🚗 Remise à jour des places pour {len(trips)} trajets:")
        
        for trip in trips:
            print(f"   • Trajet #{trip.id}: {trip.departure_city} → {trip.arrival_city}")
            print(f"     Avant: {trip.seats_available} places disponibles")
            
            # Remettre le nombre de places à la capacité maximale
            # Par défaut, on met 4 places pour tous les trajets
            trip.seats_available = 4
            
            print(f"     Après: {trip.seats_available} places disponibles")
        
        # 4. Sauvegarder les changements
        db.commit()
        
        print("\n✅ NETTOYAGE TERMINÉ!")
        print("💡 Base de données remise à zéro.")
        print("🎯 Prête pour de nouvelles réservations propres.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        return False

def verify_cleanup():
    """Vérifie que le nettoyage a bien fonctionné"""
    try:
        db = get_db()
        
        bookings_count = db.query(Booking).count()
        trips_count = db.query(Trip).count()
        
        print(f"\n🔍 VÉRIFICATION POST-NETTOYAGE:")
        print(f"   📋 Réservations restantes: {bookings_count}")
        print(f"   🚗 Trajets actifs: {trips_count}")
        
        if bookings_count == 0:
            print("✅ Toutes les réservations ont été supprimées")
        else:
            print("⚠️ Il reste des réservations")
        
        # Afficher l'état des trajets
        trips = db.query(Trip).all()
        for trip in trips:
            print(f"   • Trajet #{trip.id}: {trip.seats_available} places disponibles")
        
        return bookings_count == 0
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚨 ATTENTION: Ceci va supprimer TOUTES les réservations!")
    print("Appuyez sur Entrée pour continuer ou Ctrl+C pour annuler...")
    input()
    
    success = clean_all_bookings_and_reset_seats()
    
    if success:
        print("\n" + "="*50)
        verify_cleanup()
        print("\n🎉 Nettoyage réussi!")
        print("💡 Vous pouvez maintenant faire de nouvelles réservations propres.")
    else:
        print("\n💥 Nettoyage échoué.")
