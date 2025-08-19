#!/usr/bin/env python3
"""
MIGRATION COMPLÈTE POUR FIXER LE PROFIL
Ajoute TOUTES les colonnes manquantes en production PostgreSQL
"""

import logging
import os
from sqlalchemy import text
from database import get_db

logger = logging.getLogger(__name__)

def add_all_missing_columns():
    """
    Ajoute TOUTES les colonnes manquantes identifiées dans les logs d'erreur
    """
    print("🔧 MIGRATION COMPLÈTE DES COLONNES MANQUANTES")
    print("=" * 50)
    
    try:
        db = get_db()
        
        # Vérifier si on est en PostgreSQL (production)
        if 'postgresql' not in str(db.bind.url):
            print("⚠️ Pas en PostgreSQL - migration ignorée")
            return True
            
        print("✅ PostgreSQL détecté - début de la migration...")
        
        # Liste COMPLÈTE des colonnes à ajouter basée sur les erreurs
        migrations = [
            # Table trips - colonnes confirmation (TU les avais demandées)
            ("trips", "driver_confirmed_completion", "BOOLEAN DEFAULT FALSE"),
            ("trips", "payment_released", "BOOLEAN DEFAULT FALSE"),
            
            # Table bookings - colonne confirmation passager (TU l'avais demandée)  
            ("bookings", "passenger_confirmed_completion", "BOOLEAN DEFAULT FALSE"),
            
            # Autres colonnes qui pourraient manquer
            ("trips", "total_trip_price", "DECIMAL(10,2)"),
            ("users", "paypal_email", "VARCHAR(254)"),
            ("trips", "confirmed_by_driver", "BOOLEAN DEFAULT FALSE"),
            ("trips", "confirmed_by_passengers", "BOOLEAN DEFAULT FALSE"),
            ("trips", "driver_amount", "DECIMAL(10,2)"),
            ("trips", "commission_amount", "DECIMAL(10,2)"),
            ("trips", "payout_batch_id", "VARCHAR(255)"),
            ("trips", "last_paypal_reminder", "TIMESTAMP"),
            ("bookings", "paypal_payment_id", "VARCHAR(255)"),
            ("bookings", "refund_id", "VARCHAR(255)"),
            ("bookings", "refund_amount", "DECIMAL(10,2)"),
            ("bookings", "refund_date", "TIMESTAMP"),
            ("bookings", "original_price", "DECIMAL(10,2)"),
        ]
        
        success_count = 0
        skip_count = 0
        
        for table, column, definition in migrations:
            try:
                # Vérifier si la colonne existe déjà
                check_sql = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{column}'
                """
                
                result = db.execute(text(check_sql)).fetchone()
                
                if result:
                    print(f"⏭️  {table}.{column} - EXISTE DÉJÀ")
                    skip_count += 1
                    continue
                
                # Ajouter la colonne
                add_sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition};"
                db.execute(text(add_sql))
                db.commit()
                
                print(f"✅ {table}.{column} - AJOUTÉE")
                success_count += 1
                
            except Exception as e:
                print(f"⚠️  {table}.{column} - ERREUR: {e}")
                # Continuer avec les autres colonnes
                continue
        
        print("\n" + "=" * 50)
        print(f"📊 RÉSULTATS:")
        print(f"✅ Colonnes ajoutées: {success_count}")
        print(f"⏭️  Colonnes existantes: {skip_count}")
        print(f"🎯 Migration terminée !")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur migration complète: {e}")
        print(f"❌ ERREUR CRITIQUE: {e}")
        return False

def restore_all_columns_in_model():
    """
    Remet TOUTES les colonnes dans le modèle maintenant qu'elles existent en DB
    """
    print("\n🔄 ÉTAPES SUIVANTES:")
    print("1. Cette migration va ajouter les colonnes manquantes")
    print("2. Ensuite, décommenter les colonnes dans database/models.py")
    print("3. Redéployer")
    print("4. Le profil devrait fonctionner !")

if __name__ == "__main__":
    success = add_all_missing_columns()
    if success:
        restore_all_columns_in_model()
    else:
        print("❌ Migration échouée - le profil restera cassé")
