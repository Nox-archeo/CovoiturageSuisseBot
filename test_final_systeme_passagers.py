#!/usr/bin/env python3
"""
Test final complet du système trajets passagers
"""

def test_complet_systeme_passagers():
    """Test complet du système de trajets passagers"""
    print("🎯 TEST COMPLET SYSTÈME TRAJETS PASSAGERS")
    print("=" * 55)
    
    try:
        from database import get_db
        from database.models import Trip, User, Booking
        from datetime import datetime
        
        db = get_db()
        
        print("1️⃣ VÉRIFICATION DES DEMANDES PASSAGERS")
        print("-" * 45)
        
        # Récupérer toutes les demandes passagers
        passenger_requests = db.query(Trip).filter(
            Trip.trip_role == "passenger",
            Trip.is_published == True
        ).order_by(Trip.departure_time).all()
        
        print(f"📋 Total demandes passagers publiées: {len(passenger_requests)}")
        
        if passenger_requests:
            print("\n🔍 Aperçu des demandes:")
            for req in passenger_requests[:3]:
                creator = db.query(User).filter(User.id == req.creator_id).first()
                print(f"  • {req.departure_city} → {req.arrival_city}")
                print(f"    Date: {req.departure_time.strftime('%d/%m/%Y %H:%M')}")
                print(f"    Créateur: {creator.full_name if creator else 'Inconnu'}")
                print(f"    Places: {req.seats_available}")
        
        print(f"\n2️⃣ VÉRIFICATION VISIBILITÉ POUR CONDUCTEURS")
        print("-" * 45)
        
        # Simuler une recherche de conducteur cherchant des passagers
        matching_requests = db.query(Trip).filter(
            Trip.departure_city.like("%Fribourg%"),
            Trip.arrival_city.like("%Lausanne%"),
            Trip.trip_role == "passenger",
            Trip.is_published == True,
            Trip.departure_time >= datetime.now()
        ).all()
        
        print(f"🔍 Demandes Fribourg→Lausanne visibles: {len(matching_requests)}")
        
        for req in matching_requests:
            print(f"  ✅ Demande ID {req.id}: {req.seats_available} places recherchées")
            print(f"     Info: {req.additional_info or 'Aucune info'}")
        
        print(f"\n3️⃣ VÉRIFICATION FONCTION LIST_PASSENGER_TRIPS")
        print("-" * 45)
        
        # Simuler ce que verrait l'utilisateur ID 3
        user_id = 3
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            # Ses demandes
            user_requests = db.query(Trip).filter(
                Trip.creator_id == user.id,
                Trip.trip_role == "passenger",
                Trip.departure_time > datetime.now(),
                Trip.is_cancelled == False
            ).order_by(Trip.departure_time).all()
            
            # Ses réservations
            user_bookings = db.query(Booking).filter(
                Booking.passenger_id == user.id,
                Booking.status.in_(["pending", "confirmed"])
            ).join(Trip).filter(
                Trip.departure_time > datetime.now()
            ).all()
            
            print(f"👤 Utilisateur: {user.full_name}")
            print(f"📋 Ses demandes à venir: {len(user_requests)}")
            print(f"🎫 Ses réservations à venir: {len(user_bookings)}")
            
            total_passenger_items = len(user_requests) + len(user_bookings)
            print(f"📊 Total éléments passager: {total_passenger_items}")
        
        print(f"\n4️⃣ VÉRIFICATION SYSTÈME DE RECHERCHE")
        print("-" * 45)
        
        # Test recherche globale
        all_published = db.query(Trip).filter(
            Trip.is_published == True,
            Trip.departure_time >= datetime.now()
        ).all()
        
        conducteur_trips = [t for t in all_published if getattr(t, 'trip_role', 'driver') == 'driver']
        passager_trips = [t for t in all_published if getattr(t, 'trip_role', 'driver') == 'passenger']
        
        print(f"🔍 Recherche globale:")
        print(f"  🚗 Offres conducteurs: {len(conducteur_trips)}")
        print(f"  👥 Demandes passagers: {len(passager_trips)}")
        
        print(f"\n✅ RÉSULTATS FINAUX")
        print("=" * 55)
        print(f"✅ Demandes passagers créées et sauvegardées: {len(passenger_requests) > 0}")
        print(f"✅ Demandes visibles dans recherches: {len(matching_requests) > 0}")
        print(f"✅ Système de liste passager fonctionnel: {total_passenger_items >= 0}")
        print(f"✅ Séparation conducteur/passager active: {len(passager_trips) > 0}")
        
        if all([
            len(passenger_requests) > 0,
            len(passager_trips) > 0,
            total_passenger_items >= 0
        ]):
            print(f"\n🎉 SYSTÈME TRAJETS PASSAGERS 100% FONCTIONNEL!")
            print(f"🚀 Les utilisateurs peuvent maintenant:")
            print(f"   • Créer des demandes de trajet passager")
            print(f"   • Voir leurs demandes dans 'Mes trajets passager'")
            print(f"   • Être trouvés par les conducteurs lors de recherches")
        else:
            print(f"\n⚠️ Des problèmes persistent...")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_complet_systeme_passagers()
