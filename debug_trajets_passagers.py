#!/usr/bin/env python3
"""
Debug des problèmes avec les trajets passagers
"""

def debug_trajets_passagers():
    """Debug complet des trajets passagers"""
    print("🔍 DEBUG - TRAJETS PASSAGERS")
    print("=" * 50)
    
    try:
        from database import get_db
        from database.models import Trip, User, Booking
        from sqlalchemy import inspect
        
        db = get_db()
        
        # 1. Vérifier les colonnes de la table Trip
        print("📊 COLONNES DE LA TABLE TRIP:")
        inspector = inspect(db.bind)
        columns = inspector.get_columns('trips')
        
        available_columns = [col['name'] for col in columns]
        print(f"Colonnes disponibles: {', '.join(available_columns)}")
        
        # 2. Vérifier si les champs problématiques existent
        print(f"\n🔍 CHAMPS RECHERCHÉS:")
        problem_fields = ['passenger_id', 'seats_needed', 'is_request']
        for field in problem_fields:
            if field in available_columns:
                print(f"✅ {field}: EXISTE")
            else:
                print(f"❌ {field}: N'EXISTE PAS!")
        
        # 3. Vérifier les trajets existants
        print(f"\n📊 TRAJETS EXISTANTS:")
        all_trips = db.query(Trip).all()
        print(f"Total trajets: {len(all_trips)}")
        
        for trip in all_trips[-5:]:  # Derniers 5 trajets
            print(f"  ID {trip.id}: {trip.departure_city} → {trip.arrival_city}")
            print(f"    Driver ID: {trip.driver_id}")
            print(f"    Trip role: {getattr(trip, 'trip_role', 'Non défini')}")
            print(f"    Creator ID: {getattr(trip, 'creator_id', 'Non défini')}")
            print()
        
        # 4. Vérifier les bookings (réservations passagers)
        print(f"📊 RÉSERVATIONS PASSAGERS:")
        bookings = db.query(Booking).all()
        print(f"Total réservations: {len(bookings)}")
        
        for booking in bookings[-3:]:  # Dernières 3 réservations
            trip = booking.trip if hasattr(booking, 'trip') else None
            print(f"  Booking ID {booking.id}:")
            print(f"    Trip: {trip.departure_city} → {trip.arrival_city}" if trip else "Trip non trouvé")
            print(f"    Passenger ID: {booking.passenger_id}")
            print(f"    Status: {booking.status}")
            print(f"    Seats: {booking.seats}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_trajets_passagers()
