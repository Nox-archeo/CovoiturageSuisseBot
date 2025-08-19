#!/usr/bin/env python3
"""
Migration pour ajouter le support des co-conducteurs et partage des frais
"""

import sqlite3
import os

def add_co_driver_columns():
    """
    Ajoute les colonnes pour gérer plusieurs conducteurs et partage des frais
    """
    db_path = "/Users/margaux/CovoiturageSuisse/covoiturage.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Migration: Ajout du support des co-conducteurs")
        
        # Nouvelles colonnes pour la table trips
        trip_columns = [
            ("max_co_drivers", "INTEGER DEFAULT 1"),
            ("current_co_drivers", "INTEGER DEFAULT 1"),
            ("shared_fuel_cost", "FLOAT"),
            ("cost_per_driver", "FLOAT")
        ]
        
        for column_name, column_type in trip_columns:
            try:
                cursor.execute(f"ALTER TABLE trips ADD COLUMN {column_name} {column_type}")
                print(f"✅ Colonne trips.{column_name} ajoutée")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️  Colonne trips.{column_name} existe déjà")
                else:
                    print(f"❌ Erreur ajout trips.{column_name}: {e}")
        
        # Créer la table co_drivers
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS co_drivers (
                    id INTEGER PRIMARY KEY,
                    trip_id INTEGER NOT NULL,
                    driver_id INTEGER NOT NULL,
                    join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'confirmed',
                    amount_to_pay FLOAT,
                    has_paid BOOLEAN DEFAULT FALSE,
                    paypal_payment_id VARCHAR(255),
                    payment_status VARCHAR(20) DEFAULT 'unpaid',
                    FOREIGN KEY (trip_id) REFERENCES trips (id),
                    FOREIGN KEY (driver_id) REFERENCES users (id)
                )
            """)
            print("✅ Table co_drivers créée")
        except Exception as e:
            print(f"❌ Erreur création table co_drivers: {e}")
        
        conn.commit()
        print("✅ Migration terminée avec succès")
        
        # Vérification
        cursor.execute("PRAGMA table_info(trips)")
        columns = cursor.fetchall()
        co_driver_columns = [col[1] for col in columns if col[1] in ['max_co_drivers', 'current_co_drivers', 'shared_fuel_cost', 'cost_per_driver']]
        print(f"🔍 Colonnes co-conducteurs trouvées: {co_driver_columns}")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='co_drivers'")
        table_exists = cursor.fetchone()
        if table_exists:
            print("🔍 Table co_drivers confirmée")
        else:
            print("❌ Table co_drivers non trouvée")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    add_co_driver_columns()
