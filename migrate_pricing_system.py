#!/usr/bin/env python3
"""
Migration de la base de données pour le nouveau système de prix dynamique
"""

import logging
from sqlalchemy import text
from database import get_db
from database.models import Trip, Booking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_pricing_system():
    """
    Migre la base de données pour le nouveau système de prix dynamique
    """
    try:
        db = get_db()
        
        # 1. Ajouter les nouvelles colonnes si elles n'existent pas
        logger.info("🔄 Ajout des nouvelles colonnes...")
        
        # Colonnes pour Trip
        try:
            db.execute(text("ALTER TABLE trips ADD COLUMN total_trip_price FLOAT"))
        except Exception:
            logger.info("Colonne total_trip_price existe déjà")
        
        # Colonnes pour Booking
        try:
            db.execute(text("ALTER TABLE bookings ADD COLUMN refund_id VARCHAR(255)"))
        except Exception:
            logger.info("Colonne refund_id existe déjà")
            
        try:
            db.execute(text("ALTER TABLE bookings ADD COLUMN refund_amount FLOAT"))
        except Exception:
            logger.info("Colonne refund_amount existe déjà")
            
        try:
            db.execute(text("ALTER TABLE bookings ADD COLUMN refund_date DATETIME"))
        except Exception:
            logger.info("Colonne refund_date existe déjà")
            
        try:
            db.execute(text("ALTER TABLE bookings ADD COLUMN original_price FLOAT"))
        except Exception:
            logger.info("Colonne original_price existe déjà")
        
        db.commit()
        
        # 2. Migrer les données existantes
        logger.info("🔄 Migration des données existantes...")
        
        # Calculer le prix total des trajets existants
        trips = db.query(Trip).filter(Trip.total_trip_price.is_(None)).all()
        
        for trip in trips:
            # Calculer le prix total basé sur l'ancien système
            if trip.price_per_seat and trip.seats_available:
                # Recalculer le prix total depuis la distance si possible
                try:
                    from handlers.trip_handlers import compute_price_auto
                    total_price, _ = compute_price_auto(trip.departure_city, trip.arrival_city)
                    if total_price:
                        trip.total_trip_price = total_price
                    else:
                        # Fallback: utiliser l'ancien système
                        trip.total_trip_price = trip.price_per_seat * trip.seats_available
                except Exception as e:
                    logger.warning(f"Impossible de recalculer le prix pour le trajet {trip.id}: {e}")
                    trip.total_trip_price = trip.price_per_seat * trip.seats_available
        
        # Sauvegarder les prix originaux des réservations
        bookings = db.query(Booking).filter(Booking.original_price.is_(None)).all()
        
        for booking in bookings:
            if booking.total_price:
                booking.original_price = booking.total_price
        
        db.commit()
        
        # 3. Corriger les status de paiement
        logger.info("🔄 Correction des statuts de paiement...")
        
        # Standardiser les statuts de paiement
        db.execute(text("UPDATE bookings SET payment_status = 'completed' WHERE payment_status = 'paid'"))
        db.commit()
        
        logger.info("✅ Migration terminée avec succès!")
        
        # 4. Statistiques
        trips_count = db.query(Trip).count()
        bookings_count = db.query(Booking).count()
        migrated_trips = db.query(Trip).filter(Trip.total_trip_price.isnot(None)).count()
        
        logger.info(f"📊 Statistiques:")
        logger.info(f"   - Trajets totaux: {trips_count}")
        logger.info(f"   - Trajets migrés: {migrated_trips}")
        logger.info(f"   - Réservations totales: {bookings_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {e}")
        db.rollback()
        return False

def verify_migration():
    """
    Vérifie que la migration s'est bien passée
    """
    try:
        db = get_db()
        
        # Vérifier les colonnes
        result = db.execute(text("PRAGMA table_info(trips)")).fetchall()
        trip_columns = [row[1] for row in result]
        
        result = db.execute(text("PRAGMA table_info(bookings)")).fetchall()
        booking_columns = [row[1] for row in result]
        
        logger.info("🔍 Vérification des colonnes:")
        logger.info(f"   - total_trip_price: {'✅' if 'total_trip_price' in trip_columns else '❌'}")
        logger.info(f"   - refund_id: {'✅' if 'refund_id' in booking_columns else '❌'}")
        logger.info(f"   - refund_amount: {'✅' if 'refund_amount' in booking_columns else '❌'}")
        logger.info(f"   - refund_date: {'✅' if 'refund_date' in booking_columns else '❌'}")
        logger.info(f"   - original_price: {'✅' if 'original_price' in booking_columns else '❌'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MIGRATION DU SYSTÈME DE PRIX DYNAMIQUE")
    print("=" * 50)
    
    success = migrate_pricing_system()
    
    if success:
        print("\n🔍 Vérification de la migration...")
        verify_migration()
        print("\n✅ Migration terminée avec succès!")
        print("\n💡 Le nouveau système de prix dynamique est maintenant actif:")
        print("   - Prix par passager = Prix total ÷ Nombre de passagers")
        print("   - Remboursements automatiques via PayPal")
        print("   - Arrondi au 0.05 CHF supérieur")
    else:
        print("\n❌ Échec de la migration!")
