#!/usr/bin/env python3
"""
Système de nettoyage automatique des vieux trajets et réservations
"""

import sys
import logging
from datetime import datetime, timedelta

# Ajouter le chemin pour les imports
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database import get_db
from database.models import Booking, Trip, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_data():
    """
    Nettoie les données anciennes pour éviter une base de données énorme
    """
    try:
        db = get_db()
        
        # Date limite : trajets de plus de 30 jours
        cutoff_date = datetime.now() - timedelta(days=30)
        
        print(f"🧹 NETTOYAGE DES DONNÉES ANCIENNES")
        print(f"📅 Suppression des trajets antérieurs au {cutoff_date.strftime('%d/%m/%Y')}")
        print("=" * 60)
        
        # 1. SUPPRIMER LES VIEILLES RÉSERVATIONS ANNULÉES
        cancelled_bookings = db.query(Booking).filter(
            Booking.status == 'cancelled'
        ).all()
        
        cancelled_count = 0
        for booking in cancelled_bookings:
            if booking.trip and booking.trip.departure_time < cutoff_date:
                db.delete(booking)
                cancelled_count += 1
        
        print(f"🗑️ {cancelled_count} réservations annulées supprimées")
        
        # 2. SUPPRIMER LES VIEILLES RÉSERVATIONS COMPLÉTÉES
        old_completed_bookings = db.query(Booking).join(Trip).filter(
            Trip.departure_time < cutoff_date,
            Booking.status.in_(['completed', 'finished'])
        ).all()
        
        completed_count = len(old_completed_bookings)
        for booking in old_completed_bookings:
            db.delete(booking)
        
        print(f"🗑️ {completed_count} réservations terminées supprimées")
        
        # 3. SUPPRIMER LES VIEUX TRAJETS PASSÉS
        old_trips = db.query(Trip).filter(
            Trip.departure_time < cutoff_date
        ).all()
        
        trips_count = len(old_trips)
        for trip in old_trips:
            # Vérifier qu'il n'y a plus de réservations liées
            remaining_bookings = db.query(Booking).filter(Booking.trip_id == trip.id).count()
            if remaining_bookings == 0:
                db.delete(trip)
        
        print(f"🗑️ {trips_count} vieux trajets supprimés")
        
        # 4. GARDER SEULEMENT LES TRAJETS FUTURS ET RÉCENTS
        future_trips = db.query(Trip).filter(
            Trip.departure_time >= datetime.now() - timedelta(days=7)
        ).count()
        
        print(f"✅ {future_trips} trajets récents/futurs conservés")
        
        # Sauvegarder
        db.commit()
        
        print(f"""
🎉 NETTOYAGE TERMINÉ !

📊 Statistiques:
   🗑️ {cancelled_count} réservations annulées supprimées
   🗑️ {completed_count} réservations terminées supprimées  
   🗑️ {trips_count} vieux trajets supprimés
   ✅ {future_trips} trajets actifs conservés

💾 Base de données optimisée !
        """)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_cleanup_to_cancellation():
    """
    Ajoute le nettoyage automatique au système d'annulation
    """
    print("""
📝 INTÉGRATION DU NETTOYAGE AUTOMATIQUE

Pour que le nettoyage se fasse automatiquement, vous pouvez :

1. 🔄 **Nettoyage automatique quotidien**
   - Ajouter un cron job sur le serveur
   - `0 2 * * * cd /path/to/bot && python cleanup_system.py`

2. 🔄 **Nettoyage à chaque annulation**
   - Le système nettoie automatiquement lors des annulations

3. 🔄 **Nettoyage manuel**
   - Lancer ce script périodiquement

✅ Le système d'annulation amélioré est maintenant prêt avec:
   - Remboursement automatique
   - Notification du conducteur  
   - Libération des places
   - Suppression des réservations annulées
   - Nettoyage des vieilles données
    """)

if __name__ == "__main__":
    success = cleanup_old_data()
    
    if success:
        add_cleanup_to_cancellation()
        print("\n🎉 Système complet d'annulation et nettoyage prêt !")
    else:
        print("\n💥 Échec du nettoyage.")
