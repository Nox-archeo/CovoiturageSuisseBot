#!/usr/bin/env python
"""
Script de correction urgente pour les relations SQLAlchemy.
Corrige les problèmes de relations ambiguës après l'ajout du système dual-role.
"""

import logging
from database import get_db
from database.db_manager import engine
from database.models import Base
from sqlalchemy import text

logger = logging.getLogger(__name__)

def fix_database_relations():
    """Corrige les relations de base de données et ajoute les colonnes manquantes."""
    
    db = get_db()
    
    try:
        logger.info("Début de la correction des relations de base de données...")
        
        # 1. Ajouter les colonnes manquantes à la table bookings
        try:
            result = db.execute(text("PRAGMA table_info(bookings)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'booking_status' not in columns:
                logger.info("Ajout de la colonne booking_status à la table bookings...")
                db.execute(text("ALTER TABLE bookings ADD COLUMN booking_status VARCHAR(50) DEFAULT 'pending'"))
                db.commit()
                logger.info("✅ Colonne booking_status ajoutée")
            
            if 'seats_booked' not in columns:
                logger.info("Ajout de la colonne seats_booked à la table bookings...")
                db.execute(text("ALTER TABLE bookings ADD COLUMN seats_booked INTEGER DEFAULT 1"))
                db.commit()
                logger.info("✅ Colonne seats_booked ajoutée")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des colonnes à bookings: {e}")
            db.rollback()
            raise
        
        # 2. Ajouter les colonnes manquantes à la table driver_proposals
        try:
            result = db.execute(text("PRAGMA table_info(driver_proposals)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'accepted_at' not in columns:
                logger.info("Ajout de la colonne accepted_at à la table driver_proposals...")
                db.execute(text("ALTER TABLE driver_proposals ADD COLUMN accepted_at DATETIME"))
                db.commit()
                logger.info("✅ Colonne accepted_at ajoutée")
            
            if 'rejected_at' not in columns:
                logger.info("Ajout de la colonne rejected_at à la table driver_proposals...")
                db.execute(text("ALTER TABLE driver_proposals ADD COLUMN rejected_at DATETIME"))
                db.commit()
                logger.info("✅ Colonne rejected_at ajoutée")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des colonnes à driver_proposals: {e}")
            db.rollback()
            raise
        
        # 3. Mettre à jour les données existantes
        try:
            logger.info("Mise à jour des données existantes...")
            
            # Copier seats vers seats_booked pour les réservations existantes
            db.execute(text("UPDATE bookings SET seats_booked = seats WHERE seats_booked IS NULL"))
            
            # S'assurer que booking_status a une valeur par défaut
            db.execute(text("UPDATE bookings SET booking_status = 'pending' WHERE booking_status IS NULL"))
            
            db.commit()
            logger.info("✅ Données existantes mises à jour")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données: {e}")
            db.rollback()
            raise
        
        # 4. Recréer les tables avec les bonnes relations
        try:
            logger.info("Recréation des tables avec relations corrigées...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tables recreées avec relations corrigées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la recréation des tables: {e}")
            raise
        
        # 5. Vérification finale
        try:
            logger.info("Vérification de la correction...")
            
            # Vérifier les tables principales
            trips_count = db.execute(text("SELECT COUNT(*) FROM trips")).scalar()
            bookings_count = db.execute(text("SELECT COUNT(*) FROM bookings")).scalar()
            proposals_count = db.execute(text("SELECT COUNT(*) FROM driver_proposals")).scalar()
            
            logger.info(f"✅ Trajets: {trips_count}")
            logger.info(f"✅ Réservations: {bookings_count}")
            logger.info(f"✅ Propositions: {proposals_count}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            raise
        
        logger.info("🎉 Correction des relations terminée avec succès !")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction: {e}")
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🔧 Correction des relations de base de données...")
    success = fix_database_relations()
    
    if success:
        print("✅ Correction terminée avec succès")
        print("Le bot peut maintenant redémarrer normalement.")
    else:
        print("❌ Correction échouée")
        print("Vérifiez les logs pour plus de détails.")
