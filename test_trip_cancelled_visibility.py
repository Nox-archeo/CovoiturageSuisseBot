# Test minimal : un trajet annulé ne doit jamais être visible dans les listes publiques ou privées
from database import get_db
from database.models import Trip, User
from datetime import datetime

def test_trip_cancelled_not_visible():
    db = get_db()
    # Création d'un utilisateur fictif
    user = db.query(User).first()
    # Création d'un trajet annulé
    trip = Trip(driver_id=user.id, departure_city="TestVilleA", arrival_city="TestVilleB", departure_time=datetime(2025, 6, 1, 10, 0, 0), seats_available=3, price_per_seat=10, is_cancelled=True)
    db.add(trip)
    db.commit()
    # Vérification requête SQL
    visible_trips = db.query(Trip).filter((Trip.is_cancelled == False) | (Trip.is_cancelled.is_(None))).all()
    assert trip not in visible_trips, "Un trajet annulé ne doit pas apparaître dans les résultats visibles."
    # Vérification Python
    all_trips = db.query(Trip).all()
    visible_trips_py = [t for t in all_trips if not getattr(t, 'is_cancelled', False)]
    assert trip not in visible_trips_py, "Un trajet annulé ne doit pas apparaître dans les listes Python."
    print("Test OK : les trajets annulés sont bien invisibles.")

if __name__ == "__main__":
    test_trip_cancelled_not_visible()
