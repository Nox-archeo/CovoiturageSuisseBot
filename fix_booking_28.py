#!/usr/bin/env python3
"""
Correction des données manquantes pour la réservation #28
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

import psycopg2
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_booking_28():
    """Corrige les données manquantes de la réservation #28"""
    try:
        # Connexion directe à PostgreSQL
        conn = psycopg2.connect(
            host="dpg-d26ah2muk2gs73bqjnn0-a.oregon-postgres.render.com",
            database="covoiturage_qw9c",
            user="covoiturage_qw9c_user",
            password="M1h4WWYQ5uVVGKCW8xKJCZSIpKAXnGy9",
            port="5432",
            sslmode="require"
        )
        cursor = conn.cursor()
        
        print("🔧 Correction de la réservation #28...")
        
        # Mettre à jour total_price à 1.0 CHF (comme prévu)
        cursor.execute("""
            UPDATE bookings 
            SET total_price = 1.0,
                is_paid = true,
                payment_status = 'completed',
                status = 'confirmed'
            WHERE id = 28
        """)
        
        # Vérifier la mise à jour
        cursor.execute("SELECT * FROM bookings WHERE id = 28")
        booking = cursor.fetchone()
        
        if booking:
            print("✅ Réservation #28 corrigée:")
            print(f"   Total price: {booking[7]} CHF")  # total_price est colonne 7
            print(f"   Is paid: {booking[4]}")
            print(f"   Payment status: {booking[5]}")
            print(f"   Status: {booking[6]}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Correction réussie!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = fix_booking_28()
    if success:
        print("\n✅ Réservation #28 corrigée!")
        print("💡 Vous pouvez maintenant tester les boutons de communication.")
    else:
        print("\n❌ Échec de la correction.")
