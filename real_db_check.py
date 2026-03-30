#!/usr/bin/env python3
"""
Script pour accéder à la VRAIE base PostgreSQL de production
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import User, Booking, Trip

# Forcer l'utilisation de PostgreSQL (même URL que le bot sur Render)
POSTGRES_URL = os.getenv('DATABASE_URL')  # Utiliser variable d'environnement

def connect_to_production_db():
    """Se connecter à la vraie base PostgreSQL"""
    print("🔌 CONNEXION À LA BASE POSTGRESQL DE PRODUCTION")
    print("=" * 60)
    
    try:
        # Créer moteur PostgreSQL avec SSL
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
        
        # Test de connexion
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connexion PostgreSQL réussie")
            print(f"📊 Version: {version[:50]}...")
        
        # Créer session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        return session, engine
        
    except Exception as e:
        print(f"❌ Erreur connexion PostgreSQL: {e}")
        return None, None

def check_real_reservations():
    """Vérifier les réservations dans la vraie base"""
    
    session, engine = connect_to_production_db()
    if not session:
        return
    
    try:
        print(f"\n🔍 ANALYSE DE LA VRAIE BASE POSTGRESQL:")
        print("=" * 60)
        
        # Votre telegram_id
        user_telegram_id = 5932296330
        
        # Trouver votre utilisateur
        user = session.query(User).filter(User.telegram_id == user_telegram_id).first()
        
        if user:
            print(f"👤 UTILISATEUR TROUVÉ:")
            print(f"   ID: {user.id}")
            print(f"   telegram_id: {user.telegram_id}")
            print(f"   paypal_email: {getattr(user, 'paypal_email', 'None')}")
            
            # Chercher VOS réservations
            bookings = session.query(Booking).filter(Booking.passenger_id == user.id).all()
            
            print(f"\n📋 VOS RÉSERVATIONS ({len(bookings)}):")
            
            if bookings:
                for booking in bookings:
                    trip = booking.trip
                    print(f"\n🎫 Booking #{booking.id}:")
                    print(f"   Status: {booking.status}")
                    print(f"   Is_paid: {booking.is_paid}")
                    print(f"   Total_price: {booking.total_price}")
                    print(f"   Payment_status: {getattr(booking, 'payment_status', 'None')}")
                    print(f"   PayPal_payment_id: {getattr(booking, 'paypal_payment_id', 'None')}")
                    
                    if trip:
                        print(f"   Trajet: {trip.departure_city} → {trip.arrival_city}")
                        print(f"   Date: {trip.departure_time}")
                        print(f"   Trip ID: {trip.id}")
                    else:
                        print(f"   ❌ Trip: None")
            else:
                print("   Aucune réservation trouvée")
        else:
            print(f"❌ Utilisateur avec telegram_id {user_telegram_id} non trouvé")
        
        # Statistiques générales
        total_users = session.query(User).count()
        total_bookings = session.query(Booking).count()
        total_trips = session.query(Trip).count()
        
        print(f"\n📊 STATISTIQUES GÉNÉRALES:")
        print(f"   👥 Total utilisateurs: {total_users}")
        print(f"   📋 Total réservations: {total_bookings}")
        print(f"   🚗 Total trajets: {total_trips}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
    finally:
        session.close()

def delete_reservation_if_exists(booking_id):
    """Supprimer une réservation spécifique"""
    
    session, engine = connect_to_production_db()
    if not session:
        return False
    
    try:
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        
        if booking:
            print(f"\n🗑️ SUPPRESSION RÉSERVATION #{booking_id}")
            trip = booking.trip
            if trip:
                print(f"   Trajet: {trip.departure_city} → {trip.arrival_city}")
            print(f"   Montant: {booking.total_price} CHF")
            
            session.delete(booking)
            session.commit()
            print(f"✅ Réservation #{booking_id} supprimée")
            return True
        else:
            print(f"❌ Réservation #{booking_id} non trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur suppression: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("🎯 ACCÈS À LA VRAIE BASE POSTGRESQL")
    check_real_reservations()
    
    # Proposer de supprimer une réservation
    print(f"\n" + "=" * 60)
    print("💡 Pour supprimer une réservation, utilisez:")
    print("   python real_db_check.py --delete BOOKING_ID")
