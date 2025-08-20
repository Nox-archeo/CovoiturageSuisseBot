#!/usr/bin/env python3
"""
Script pour supprimer les réservations de test
"""
import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, '/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db
from database.models import Booking, Trip, User

def clean_test_reservations():
    """Supprime toutes les réservations de test"""
    
    # Utiliser la VRAIE URL de production (celle du bot)
    # D'après les logs: postgresql://covoiturage_qw9c_user:UT15TWaumLIVkmH...
    print("🔍 Récupération de la vraie URL de base de données depuis les variables Render...")
    
    # On va utiliser la même méthode que le bot pour récupérer DATABASE_URL
    from database.db_manager import get_db
    
    try:
        db = get_db()
        
        # Compter les réservations avant suppression
        total_bookings = db.query(Booking).count()
        print(f"📊 Total réservations dans la vraie base: {total_bookings}")
        
        # Afficher les réservations de l'utilisateur ID 1 (vous)
        user_bookings = db.query(Booking).filter(Booking.passenger_id == 1).all()
        print(f"📋 Vos réservations (User ID 1): {len(user_bookings)}")
        
        # Afficher quelques réservations pour confirmation
        sample_bookings = db.query(Booking).limit(5).all()
        print(f"\n📋 Premières réservations:")
        for booking in sample_bookings:
            trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
            if trip:
                print(f"  - ID {booking.id}: {trip.departure_city} → {trip.arrival_city} le {trip.departure_time}")
        
        # Demander confirmation
        print(f"\n🗑️  VOULEZ-VOUS SUPPRIMER TOUTES LES {total_bookings} RÉSERVATIONS ?")
        response = input("Tapez 'OUI' en majuscules pour confirmer: ")
        
        if response == "OUI":
            # Supprimer toutes les réservations
            deleted_count = db.query(Booking).delete()
            db.commit()
            print(f"✅ {deleted_count} réservations supprimées avec succès!")
            
            # Vérification
            remaining = db.query(Booking).count()
            print(f"📊 Réservations restantes: {remaining}")
            
        else:
            print("❌ Suppression annulée")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_test_reservations()
