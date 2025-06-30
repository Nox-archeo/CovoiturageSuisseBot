"""
Migration pour ajouter les champs de double confirmation
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate_add_confirmation_fields():
    """Ajoute les champs de confirmation manquants à la table trips"""
    try:
        conn = sqlite3.connect('covoiturage.db')
        cursor = conn.cursor()
        
        # Vérifier si les colonnes existent déjà
        cursor.execute("PRAGMA table_info(trips)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Ajouter les colonnes manquantes
        if 'confirmed_by_driver' not in columns:
            cursor.execute("ALTER TABLE trips ADD COLUMN confirmed_by_driver BOOLEAN DEFAULT 0")
            logger.info("✅ Colonne confirmed_by_driver ajoutée")
        
        if 'confirmed_by_passengers' not in columns:
            cursor.execute("ALTER TABLE trips ADD COLUMN confirmed_by_passengers BOOLEAN DEFAULT 0")
            logger.info("✅ Colonne confirmed_by_passengers ajoutée")
        
        if 'driver_amount' not in columns:
            cursor.execute("ALTER TABLE trips ADD COLUMN driver_amount REAL NULL")
            logger.info("✅ Colonne driver_amount ajoutée")
        
        if 'commission_amount' not in columns:
            cursor.execute("ALTER TABLE trips ADD COLUMN commission_amount REAL NULL")
            logger.info("✅ Colonne commission_amount ajoutée")
        
        if 'last_paypal_reminder' not in columns:
            cursor.execute("ALTER TABLE trips ADD COLUMN last_paypal_reminder TIMESTAMP NULL")
            logger.info("✅ Colonne last_paypal_reminder ajoutée")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Migration des champs de confirmation terminée")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration : {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_add_confirmation_fields()
