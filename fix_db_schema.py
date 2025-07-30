#!/usr/bin/env python3
"""
Script pour ajouter les colonnes manquantes à la base de données
"""

import sqlite3
import os

def add_missing_columns():
    """Ajouter les colonnes age et paypal_email à la table users"""
    
    db_path = "/Users/margaux/CovoiturageSuisse/database/covoiturage.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si les colonnes existent déjà
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Colonnes actuelles dans users: {columns}")
        
        # Ajouter la colonne age si elle n'existe pas
        if 'age' not in columns:
            print("Ajout de la colonne 'age'...")
            cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER")
            print("✅ Colonne 'age' ajoutée")
        else:
            print("✅ Colonne 'age' existe déjà")
        
        # Ajouter la colonne paypal_email si elle n'existe pas
        if 'paypal_email' not in columns:
            print("Ajout de la colonne 'paypal_email'...")
            cursor.execute("ALTER TABLE users ADD COLUMN paypal_email TEXT")
            print("✅ Colonne 'paypal_email' ajoutée")
        else:
            print("✅ Colonne 'paypal_email' existe déjà")
        
        conn.commit()
        conn.close()
        
        print("✅ Base de données mise à jour avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        return False

if __name__ == "__main__":
    print("=== MISE À JOUR DE LA BASE DE DONNÉES ===")
    success = add_missing_columns()
    
    if success:
        print("\n🎉 Tu peux maintenant redémarrer ton bot!")
    else:
        print("\n❌ Problème lors de la mise à jour")
