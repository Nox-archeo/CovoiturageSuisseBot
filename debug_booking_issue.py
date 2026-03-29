#!/usr/bin/env python3
"""
Script pour diagnostiquer et corriger les incohérences de réservations
"""

from database.models import Booking, Trip, User
from database import get_db

def diagnose_booking_issue():
    """Diagnostique les problèmes de réservation"""
    
    db = get_db()
    
    print("🔍 DIAGNOSTIC COMPLET DES RÉSERVATIONS")
    print("=" * 50)
    
    # 1. Vérifier l'utilisateur
    user_telegram_id = 5932296330
    user = db.query(User).filter(User.telegram_id == user_telegram_id).first()
    
    if user:
        print(f"✅ Utilisateur trouvé:")
        print(f"   ID: {user.id}")
        print(f"   telegram_id: {user.telegram_id}")
        print(f"   paypal_email: {getattr(user, 'paypal_email', 'None')}")
    else:
        print("❌ Utilisateur non trouvé")
        return
    
    # 2. Vérifier les réservations avec différentes requêtes
    print(f"\n📋 RECHERCHE RÉSERVATIONS:")
    
    # Par passenger_id
    bookings_by_passenger = db.query(Booking).filter(Booking.passenger_id == user.id).all()
    print(f"   Par passenger_id ({user.id}): {len(bookings_by_passenger)}")
    
    # Toutes les réservations
    all_bookings = db.query(Booking).all()
    print(f"   Toutes les réservations: {len(all_bookings)}")
    
    # Par relation passenger
    try:
        bookings_by_relation = db.query(Booking).join(User, Booking.passenger_id == User.id).filter(User.telegram_id == user_telegram_id).all()
        print(f"   Par relation passenger: {len(bookings_by_relation)}")
    except Exception as e:
        print(f"   Erreur relation: {e}")
    
    # 3. Vérifier les trajets disponibles
    all_trips = db.query(Trip).all()
    print(f"\n🚗 TRAJETS DISPONIBLES: {len(all_trips)}")
    
    for trip in all_trips[:3]:
        print(f"   Trip #{trip.id}: {trip.departure_city} → {trip.arrival_city}")
    
    # 4. Créer une réservation de test si nécessaire
    if len(all_trips) > 0 and len(bookings_by_passenger) == 0:
        print(f"\n🧪 CRÉATION RÉSERVATION DE TEST")
        
        # Prendre le premier trajet disponible
        test_trip = all_trips[0]
        
        # Créer une réservation de test
        test_booking = Booking(
            trip_id=test_trip.id,
            passenger_id=user.id,
            status='pending',
            total_price=1.0,
            is_paid=True,
            payment_status='completed',
            paypal_payment_id='TEST_PAYMENT_ID_123'
        )
        
        try:
            db.add(test_booking)
            db.commit()
            db.refresh(test_booking)
            
            print(f"✅ Réservation de test créée:")
            print(f"   Booking ID: {test_booking.id}")
            print(f"   Montant: {test_booking.total_price} CHF")
            print(f"   Trajet: {test_trip.departure_city} → {test_trip.arrival_city}")
            print(f"   Status: {test_booking.status}")
            
            return test_booking.id
            
        except Exception as e:
            print(f"❌ Erreur création réservation: {e}")
            db.rollback()
            return None
    else:
        print(f"\n⚠️ Pas besoin de créer de réservation de test")
        return None

if __name__ == "__main__":
    booking_id = diagnose_booking_issue()
    if booking_id:
        print(f"\n🎯 RÉSERVATION DE TEST PRÊTE!")
        print(f"   ID: {booking_id}")
        print(f"   Vous pouvez maintenant tester l'annulation dans /profile")
    else:
        print(f"\n🤔 Pas de réservation de test créée")
