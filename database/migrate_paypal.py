"""
Migration pour ajouter les champs PayPal aux modèles
"""

import sqlite3
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_paypal_fields():
    """
    Ajoute les champs PayPal aux tables existantes
    """
    # Utiliser la même base de données que les modèles (à la racine du projet)
    db_path = Path(__file__).parent.parent / "covoiturage.db"
    
    if not db_path.exists():
        logger.error(f"Base de données non trouvée : {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Migration pour la table users
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN paypal_email TEXT")
            logger.info("✅ Colonne paypal_email ajoutée à la table users")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Colonne paypal_email déjà présente dans users")
            else:
                logger.error(f"Erreur lors de l'ajout de paypal_email à users : {e}")
        
        # Migration pour la table bookings
        paypal_columns = [
            ("paypal_payment_id", "TEXT"),
            ("payment_status", "TEXT DEFAULT 'unpaid'"),
            ("total_price", "REAL")
        ]
        
        for column_name, column_type in paypal_columns:
            try:
                cursor.execute(f"ALTER TABLE bookings ADD COLUMN {column_name} {column_type}")
                logger.info(f"✅ Colonne {column_name} ajoutée à la table bookings")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info(f"ℹ️ Colonne {column_name} déjà présente dans bookings")
                else:
                    logger.error(f"Erreur lors de l'ajout de {column_name} à bookings : {e}")
        
        # Migration pour la table trips
        trip_columns = [
            ("status", "TEXT DEFAULT 'active'"),
            ("payout_batch_id", "TEXT")
        ]
        
        for column_name, column_type in trip_columns:
            try:
                cursor.execute(f"ALTER TABLE trips ADD COLUMN {column_name} {column_type}")
                logger.info(f"✅ Colonne {column_name} ajoutée à la table trips")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info(f"ℹ️ Colonne {column_name} déjà présente dans trips")
                else:
                    logger.error(f"Erreur lors de l'ajout de {column_name} à trips : {e}")
        
        # Mise à jour des valeurs par défaut pour les enregistrements existants
        cursor.execute("UPDATE bookings SET payment_status = 'unpaid' WHERE payment_status IS NULL")
        cursor.execute("UPDATE trips SET status = 'active' WHERE status IS NULL")
        
        conn.commit()
        logger.info("✅ Migration PayPal terminée avec succès")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la migration : {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔄 Début de la migration PayPal...")
    success = migrate_paypal_fields()
    
    if success:
        print("✅ Migration PayPal terminée avec succès !")
        print("\nNouveaux champs ajoutés :")
        print("  - users.paypal_email : Email PayPal du conducteur")
        print("  - bookings.paypal_payment_id : ID du paiement PayPal")
        print("  - bookings.payment_status : Statut du paiement")
        print("  - bookings.total_price : Montant total")
        print("  - trips.status : Statut du trajet")
        print("  - trips.payout_batch_id : ID du paiement au conducteur")
    else:
        print("❌ Erreur lors de la migration PayPal")
