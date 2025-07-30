#!/usr/bin/env python3
"""Script pour corriger le groupement des trajets."""

from database.db_manager import SessionLocal
from database.models import Trip
import uuid
from datetime import datetime

def fix_grouping():
    with SessionLocal() as session:
        # Trouver tous les trajets créés aujourd'hui
        today = datetime.now().date()
        today_trips = session.query(Trip).filter(
            Trip.departure_time >= today
        ).order_by(Trip.id.desc()).limit(20).all()
        
        print(f"Trajets trouvés: {len(today_trips)}")
        
        # Afficher l'état actuel
        for trip in today_trips:
            print(f"Trip {trip.id}: {trip.departure_city} → {trip.arrival_city}, recurring={trip.recurring}, group_id={trip.group_id}")
        
        # Grouper les trajets similaires
        grouped = {}
        for trip in today_trips:
            key = f"{trip.departure_city}-{trip.arrival_city}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(trip)
        
        # Assigner group_id aux groupes de trajets
        for key, trips in grouped.items():
            if len(trips) > 1:  # Si plusieurs trajets similaires
                group_id = f"group_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                print(f"\nGroupe {key}: {len(trips)} trajets -> group_id: {group_id}")
                for trip in trips:
                    trip.recurring = True
                    trip.group_id = group_id
                    trip.is_published = True
                    print(f"  - Mis à jour trip {trip.id}")
        
        session.commit()
        print("\nTrajets mis à jour!")

if __name__ == "__main__":
    fix_grouping()
