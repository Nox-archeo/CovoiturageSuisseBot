#!/usr/bin/env python3
"""
Correction de la réservation #28 via le système de DB existant
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database import get_db
from database.models import Booking
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_booking_28_via_orm():
    """Corrige la réservation #28 via l'ORM"""
    try:
        db = get_db()
        
        print("🔧 Recherche de la réservation #28...")
        booking = db.query(Booking).filter(Booking.id == 28).first()
        
        if not booking:
            print("❌ Réservation #28 non trouvée")
            return False
        
        print(f"📋 Réservation trouvée: ID={booking.id}")
        print(f"   Avant: total_price={booking.total_price}, status={booking.status}")
        
        # Correction des données
        booking.total_price = 1.0
        booking.is_paid = True
        booking.payment_status = 'completed'
        booking.status = 'confirmed'
        
        db.commit()
        
        print(f"   Après: total_price={booking.total_price}, status={booking.status}")
        print("✅ Réservation #28 corrigée avec succès!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_booking_28_via_orm()
    if success:
        print("\n🎉 Correction réussie!")
        print("💡 Maintenant testons les boutons de communication...")
    else:
        print("\n💥 Correction échouée.")
