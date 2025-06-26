#!/usr/bin/env python
"""
Script de migration pour ajouter la colonne 'booking_date' à la table bookings.
Ce script va résoudre l'erreur "no such column: bookings.booking_date" en ajoutant
la colonne manquante à la base de données SQLite.
"""
import os
import sqlite3
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def get_db_path():
    """Récupère le chemin de la base de données."""
    # Chercher le fichier covoiturage.db dans les répertoires courants
    possible_paths = [
        '/Users/margaux/CovoiturageSuisse/covoiturage.db',
        '/Users/margaux/CovoiturageSuisse/database/covoiturage.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError("Base de données non trouvée")

def add_missing_columns():
    """Ajoute les colonnes manquantes à la table 'bookings'."""
    try:
        db_path = get_db_path()
        logger.info(f"Base de données trouvée à l'emplacement: {db_path}")
        
        # Connexion à la base de données SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier quelles colonnes existent déjà
        cursor.execute("PRAGMA table_info(bookings)")
        existing_columns = {column[1] for column in cursor.fetchall()}
        
        # Liste des colonnes à vérifier/ajouter avec leurs types et valeurs par défaut
        columns_to_check = {
            'booking_date': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'is_paid': 'BOOLEAN DEFAULT 0',
            'amount': 'FLOAT DEFAULT 0.0',
            'stripe_session_id': 'TEXT DEFAULT NULL',
            'stripe_payment_intent_id': 'TEXT DEFAULT NULL'
        }
        
        # Ajouter les colonnes manquantes
        for column_name, column_def in columns_to_check.items():
            if column_name not in existing_columns:
                logger.info(f"Ajout de la colonne '{column_name}' à la table bookings...")
                cursor.execute(f"ALTER TABLE bookings ADD COLUMN {column_name} {column_def}")
                logger.info(f"Colonne '{column_name}' ajoutée avec succès")
        
        conn.commit()
        logger.info("Migration des colonnes terminée avec succès")
        
        conn.close()
        return True, "Opération réussie"
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout des colonnes: {str(e)}")
        return False, str(e)

def verify_columns_exist():
    """Vérifie que toutes les colonnes nécessaires existent maintenant dans la table."""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si les colonnes existent
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        columns_to_check = ['seats', 'booking_date', 'is_paid', 'amount', 
                           'stripe_session_id', 'stripe_payment_intent_id']
        
        missing_columns = [col for col in columns_to_check if col not in columns]
        
        if not missing_columns:
            logger.info("Vérification réussie: toutes les colonnes nécessaires existent dans la table bookings")
            return True
        else:
            logger.error(f"Vérification échouée: les colonnes suivantes sont manquantes: {missing_columns}")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la vérification: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Début de la migration pour ajouter les colonnes manquantes à la table bookings...")
    success, message = add_missing_columns()
    
    if success:
        if verify_columns_exist():
            print("✅ Migration réussie: toutes les colonnes nécessaires ont été ajoutées à la table bookings")
        else:
            print("❌ La vérification a échoué, veuillez vérifier les logs")
    else:
        print(f"❌ La migration a échoué: {message}")
