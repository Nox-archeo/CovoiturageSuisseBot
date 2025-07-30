#!/usr/bin/env python
"""
Script de migration pour le système de propositions de conducteurs.
Ajoute les champs nécessaires aux modèles existants et crée la nouvelle table DriverProposal.
"""

import logging
from database import get_db, Base
from database.db_manager import engine
from database.models import Trip, DriverProposal
from sqlalchemy import text

logger = logging.getLogger(__name__)

def migrate_database():
    """Effectue la migration de la base de données pour le système de propositions."""
    
    db = get_db()
    
    try:
        logger.info("Début de la migration de la base de données...")
        
        # 1. Ajouter les colonnes trip_role et creator_id à la table trips si elles n'existent pas
        try:
            # Vérifier si la colonne trip_role existe
            result = db.execute(text("PRAGMA table_info(trips)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'trip_role' not in columns:
                logger.info("Ajout de la colonne trip_role à la table trips...")
                db.execute(text("ALTER TABLE trips ADD COLUMN trip_role VARCHAR(20) DEFAULT 'driver'"))
                db.commit()
                logger.info("✅ Colonne trip_role ajoutée")
            else:
                logger.info("✅ Colonne trip_role déjà présente")
            
            if 'creator_id' not in columns:
                logger.info("Ajout de la colonne creator_id à la table trips...")
                db.execute(text("ALTER TABLE trips ADD COLUMN creator_id INTEGER"))
                db.commit()
                logger.info("✅ Colonne creator_id ajoutée")
            else:
                logger.info("✅ Colonne creator_id déjà présente")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des colonnes à trips: {e}")
            db.rollback()
            raise
        
        # 2. Mettre à jour les données existantes
        try:
            logger.info("Mise à jour des données existantes...")
            
            # Définir trip_role = 'driver' pour tous les trajets existants
            db.execute(text("UPDATE trips SET trip_role = 'driver' WHERE trip_role IS NULL"))
            
            # Définir creator_id = driver_id pour tous les trajets existants
            db.execute(text("UPDATE trips SET creator_id = driver_id WHERE creator_id IS NULL AND driver_id IS NOT NULL"))
            
            db.commit()
            logger.info("✅ Données existantes mises à jour")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données: {e}")
            db.rollback()
            raise
        
        # 3. Créer la table driver_proposals si elle n'existe pas
        try:
            logger.info("Création de la table driver_proposals...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Table driver_proposals créée ou vérifiée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la table driver_proposals: {e}")
            raise
        
        # 4. Vérification finale
        try:
            logger.info("Vérification de la migration...")
            
            # Compter les trajets par rôle
            driver_trips = db.execute(text("SELECT COUNT(*) FROM trips WHERE trip_role = 'driver'")).scalar()
            passenger_trips = db.execute(text("SELECT COUNT(*) FROM trips WHERE trip_role = 'passenger'")).scalar()
            
            logger.info(f"✅ Trajets conducteur: {driver_trips}")
            logger.info(f"✅ Trajets passager: {passenger_trips}")
            
            # Vérifier la table driver_proposals
            proposals_count = db.execute(text("SELECT COUNT(*) FROM driver_proposals")).scalar()
            logger.info(f"✅ Propositions de conducteurs: {proposals_count}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            raise
        
        logger.info("🎉 Migration terminée avec succès !")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {e}")
        return False
    
    finally:
        db.close()

def rollback_migration():
    """Annule la migration (fonction de sécurité)."""
    
    db = get_db()
    
    try:
        logger.info("Début du rollback de la migration...")
        
        # Supprimer la table driver_proposals
        try:
            db.execute(text("DROP TABLE IF EXISTS driver_proposals"))
            db.commit()
            logger.info("✅ Table driver_proposals supprimée")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de driver_proposals: {e}")
        
        # Note: On ne peut pas supprimer les colonnes avec SQLite
        # Elles resteront mais ne seront pas utilisées
        logger.warning("⚠️ Les colonnes trip_role et creator_id ne peuvent pas être supprimées avec SQLite")
        logger.warning("   Elles resteront dans la base mais ne seront pas utilisées")
        
        logger.info("🔄 Rollback terminé")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du rollback: {e}")
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        print("🔄 Rollback de la migration...")
        success = rollback_migration()
    else:
        print("🚀 Lancement de la migration...")
        success = migrate_database()
    
    if success:
        print("✅ Opération terminée avec succès")
        sys.exit(0)
    else:
        print("❌ Opération échouée")
        sys.exit(1)
