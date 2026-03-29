#!/usr/bin/env python3
"""
Script pour corriger la réservation avec total_price None
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import User, Booking, Trip

# URL PostgreSQL correcte
POSTGRES_URL = "postgresql://covoiturage_qw9c_user:UT15TWaumLIVkmHOOakrhSpFhmKH5vaX@dpg-d26ah2muk2gs73bqjnn0-a.oregon-postgres.render.com/covoiturage_qw9c"

def fix_booking_total_price():
    """Corriger le total_price de la réservation #23"""
    
    try:
        # Connexion PostgreSQL
        engine = create_engine(
            POSTGRES_URL, 
            pool_pre_ping=True,
            connect_args={
                "sslmode": "require",
                "sslcert": None,
                "sslkey": None,
                "sslrootcert": None
            }
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        print("🔧 CORRECTION DE LA RÉSERVATION #23")
        print("=" * 50)
        
        # Récupérer la réservation #23
        booking = session.query(Booking).filter(Booking.id == 23).first()
        
        if booking:
            trip = booking.trip
            print(f"📋 Réservation trouvée:")
            print(f"   ID: {booking.id}")
            print(f"   Trajet: {trip.departure_city} → {trip.arrival_city}")
            print(f"   Total_price AVANT: {booking.total_price}")
            print(f"   PayPal ID: {booking.paypal_payment_id}")
            
            # Fixer le total_price à 1.0 CHF (montant que vous avez payé)
            booking.total_price = 1.0
            
            session.commit()
            
            print(f"   Total_price APRÈS: {booking.total_price}")
            print(f"✅ Réservation #23 corrigée !")
            
            return True
        else:
            print("❌ Réservation #23 non trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        session.close()

def delete_booking_23():
    """Supprimer complètement la réservation #23"""
    
    try:
        # Connexion PostgreSQL
        engine = create_engine(
            POSTGRES_URL, 
            pool_pre_ping=True,
            connect_args={
                "sslmode": "require",
                "sslcert": None,
                "sslkey": None,
                "sslrootcert": None
            }
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        print("🗑️ SUPPRESSION DE LA RÉSERVATION #23")
        print("=" * 50)
        
        # Récupérer la réservation #23
        booking = session.query(Booking).filter(Booking.id == 23).first()
        
        if booking:
            trip = booking.trip
            print(f"📋 Réservation à supprimer:")
            print(f"   ID: {booking.id}")
            print(f"   Trajet: {trip.departure_city} → {trip.arrival_city}")
            print(f"   Total_price: {booking.total_price}")
            print(f"   PayPal ID: {booking.paypal_payment_id}")
            
            # Supprimer la réservation
            session.delete(booking)
            session.commit()
            
            print(f"✅ Réservation #23 supprimée !")
            
            return True
        else:
            print("❌ Réservation #23 non trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--delete":
        # Supprimer la réservation
        delete_booking_23()
    else:
        # Corriger la réservation
        fix_booking_total_price()
    
    print(f"\n💡 UTILISATION:")
    print(f"   python fix_booking.py        # Corriger total_price")
    print(f"   python fix_booking.py --delete  # Supprimer la réservation")
