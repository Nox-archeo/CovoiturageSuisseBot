#!/usr/bin/env python3
"""
Script pour nettoyer les réservations dans la base PostgreSQL de production
"""

import os
import psycopg2
from urllib.parse import urlparse

# URL de la base PostgreSQL depuis les variables d'environnement
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://covoiturage_user:LonePumpkin321@dpg-crt6bt5umphs73ah6700-a.oregon-postgres.render.com/covoiturage')

def clean_postgresql_bookings():
    try:
        # Parser l'URL de la base
        parsed = urlparse(DATABASE_URL)
        
        # Connexion à PostgreSQL
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Enlever le / au début
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        
        print("🔍 Connexion à PostgreSQL réussie")
        
        # Voir toutes les réservations actuelles
        cursor.execute("SELECT id, paypal_payment_id, is_paid, payment_status FROM bookings ORDER BY id")
        bookings = cursor.fetchall()
        
        print(f"📊 {len(bookings)} réservations trouvées:")
        for booking in bookings:
            print(f"  ID: {booking[0]}, PayPal: {booking[1]}, Payé: {booking[2]}, Status: {booking[3]}")
        
        if bookings:
            # Supprimer TOUTES les réservations
            cursor.execute("DELETE FROM bookings")
            deleted = cursor.rowcount
            print(f"🗑️ {deleted} réservations supprimées")
            
            # Vérifier que c'est vide
            cursor.execute("SELECT COUNT(*) FROM bookings")
            remaining = cursor.fetchone()[0]
            print(f"✅ Réservations restantes: {remaining}")
            
            # Commit les changements
            conn.commit()
            print("💾 Changements sauvegardés")
        else:
            print("ℹ️ Aucune réservation à supprimer")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧹 Nettoyage des réservations PostgreSQL...")
    success = clean_postgresql_bookings()
    if success:
        print("✅ Nettoyage terminé avec succès")
    else:
        print("❌ Erreur lors du nettoyage")
