#!/usr/bin/env python
"""
Script de migration pour ajouter la colonne 'seats' à la table bookings.
Ce script va résoudre l'erreur "no such column: bookings.seats" en ajoutant
la colonne manquante à la base de données SQLite.
"""
import os
import sqlite3
from sqlalchemy import create_engine, inspect, text
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

def add_seats_column():
    """Ajoute la colonne 'seats' à la table 'bookings' si elle n'existe pas."""
    try:
        db_path = get_db_path()
        logger.info(f"Base de données trouvée à l'emplacement: {db_path}")
        
        # Connexion à la base de données SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'seats' not in columns:
            logger.info("La colonne 'seats' n'existe pas dans la table bookings, ajout en cours...")
            
            # Ajouter la colonne avec une valeur par défaut de 1
            cursor.execute("ALTER TABLE bookings ADD COLUMN seats INTEGER DEFAULT 1")
            conn.commit()
            
            logger.info("Colonne 'seats' ajoutée avec succès à la table bookings")
        else:
            logger.info("La colonne 'seats' existe déjà dans la table bookings")
        
        conn.close()
        return True, "Opération réussie"
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de la colonne 'seats': {str(e)}")
        return False, str(e)

def verify_column_exists():
    """Vérifie que la colonne 'seats' existe maintenant dans la table."""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la colonne existe
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'seats' in columns:
            logger.info("Vérification réussie: la colonne 'seats' existe bien dans la table bookings")
            return True
        else:
            logger.error("Vérification échouée: la colonne 'seats' n'existe pas dans la table bookings")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la vérification: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Début de la migration pour ajouter la colonne 'seats'...")
    success, message = add_seats_column()
    
    if success:
        if verify_column_exists():
            print("✅ Migration réussie: la colonne 'seats' a été ajoutée à la table bookings")
        else:
            print("❌ La vérification a échoué, veuillez vérifier les logs")
    else:
        print(f"❌ La migration a échoué: {message}")
