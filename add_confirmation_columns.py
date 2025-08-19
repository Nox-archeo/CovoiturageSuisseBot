#!/usr/bin/env python3
"""
Migration pour ajouter les colonnes de confirmation de trajet
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db, engine
from database.models import Trip, Booking
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def add_confirmation_columns():
    """Ajoute les colonnes de confirmation dans les tables"""
    
    try:
        # Ajouter colonnes à la table trips
        with engine.connect() as conn:
            try:
                # Colonne pour confirmation conducteur
                conn.execute(text("ALTER TABLE trips ADD COLUMN driver_confirmed_completion BOOLEAN DEFAULT FALSE"))
                print("✅ Colonne driver_confirmed_completion ajoutée à trips")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print("ℹ️ Colonne driver_confirmed_completion existe déjà")
                else:
                    raise e
            
            try:
                # Colonne pour indiquer si le paiement a été libéré
                conn.execute(text("ALTER TABLE trips ADD COLUMN payment_released BOOLEAN DEFAULT FALSE"))
                print("✅ Colonne payment_released ajoutée à trips")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print("ℹ️ Colonne payment_released existe déjà")
                else:
                    raise e
            
            # Ajouter colonne à la table bookings
            try:
                # Colonne pour confirmation passager
                conn.execute(text("ALTER TABLE bookings ADD COLUMN passenger_confirmed_completion BOOLEAN DEFAULT FALSE"))
                print("✅ Colonne passenger_confirmed_completion ajoutée à bookings")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print("ℹ️ Colonne passenger_confirmed_completion existe déjà")
                else:
                    raise e
            
            conn.commit()
            
        print("🎉 Migration des colonnes de confirmation terminée !")
        
    except Exception as e:
        logger.error(f"Erreur lors de la migration: {e}")
        print(f"❌ Erreur migration: {e}")

if __name__ == "__main__":
    add_confirmation_columns()
