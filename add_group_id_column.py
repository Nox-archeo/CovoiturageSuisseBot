#!/usr/bin/env python3
"""
Script pour ajouter la colonne group_id à la table trips
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from database.db_manager import engine
from sqlalchemy import text

def add_group_id_column():
    """Ajoute la colonne group_id à la table trips si elle n'existe pas déjà."""
    
    try:
        with engine.connect() as conn:
            # Vérifier si la colonne existe déjà
            result = conn.execute(text("""
                PRAGMA table_info(trips);
            """))
            
            columns = [row[1] for row in result.fetchall()]
            
            if 'group_id' not in columns:
                print("Ajout de la colonne group_id à la table trips...")
                
                # Ajouter la colonne group_id
                conn.execute(text("""
                    ALTER TABLE trips ADD COLUMN group_id VARCHAR;
                """))
                
                conn.commit()
                print("✅ Colonne group_id ajoutée avec succès!")
            else:
                print("✅ La colonne group_id existe déjà.")
                
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Migration de la base de données...")
    
    if add_group_id_column():
        print("🎉 Migration terminée avec succès!")
    else:
        print("❌ Échec de la migration.")
        sys.exit(1)
