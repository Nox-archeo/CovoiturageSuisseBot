#!/usr/bin/env python3
"""
Migration pour ajouter les colonnes co-drivers en production
IMPORTANT: À exécuter quand les serveurs peuvent être arrêtés
"""

import logging
from database import get_db

logger = logging.getLogger(__name__)

def add_co_driver_columns_safely():
    """
    Ajoute les colonnes co-drivers de manière sécurisée
    """
    try:
        db = get_db()
        
        # Vérifier si on est en PostgreSQL (production)
        if 'postgresql' in str(db.bind.url):
            print("🔄 Ajout des colonnes co-drivers en PostgreSQL...")
            
            # Ajouter les colonnes si elles n'existent pas
            sqls = [
                "ALTER TABLE trips ADD COLUMN IF NOT EXISTS max_co_drivers INTEGER DEFAULT 1;",
                "ALTER TABLE trips ADD COLUMN IF NOT EXISTS current_co_drivers INTEGER DEFAULT 1;"
            ]
            
            for sql in sqls:
                try:
                    db.execute(sql)
                    print(f"✅ {sql}")
                except Exception as e:
                    print(f"⚠️ {sql} - {e}")
            
            db.commit()
            print("✅ Colonnes co-drivers ajoutées avec succès !")
            
        else:
            print("ℹ️ Base SQLite détectée - pas de migration nécessaire")
            
    except Exception as e:
        logger.error(f"Erreur migration co-drivers: {e}")
        print(f"❌ Erreur: {e}")

def enable_co_driver_columns_in_model():
    """
    Instructions pour réactiver les colonnes dans le modèle
    """
    print("\n📋 ÉTAPES POUR RÉACTIVER LES COLONNES:")
    print("1. Exécuter ce script en production")
    print("2. Dans database/models.py, décommenter:")
    print("   # max_co_drivers = Column(Integer, default=1)")
    print("   # current_co_drivers = Column(Integer, default=1)")
    print("3. Commit et redéployer")
    print("4. Tester le profil")

if __name__ == "__main__":
    print("🔧 MIGRATION CO-DRIVERS")
    print("=" * 40)
    add_co_driver_columns_safely()
    enable_co_driver_columns_in_model()
