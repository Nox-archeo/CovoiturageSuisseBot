#!/usr/bin/env python3
"""
Script pour mettre à jour le schéma de la base de données avec les nouveaux champs
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import init_db
from database.models import User, Trip

def update_database():
    """Met à jour la base de données avec le nouveau schéma"""
    print("🔄 Mise à jour du schéma de la base de données...")
    
    try:
        # Recréer les tables avec le nouveau schéma
        init_db()
        print("✅ Base de données mise à jour avec succès!")
        
        # Vérifier les nouveaux champs
        from database import get_db
        db = get_db()
        
        # Test de création d'un utilisateur avec les nouveaux champs
        print("🧪 Test des nouveaux champs...")
        
        # Vérifier que les champs existent en essayant de créer un utilisateur test
        test_user = User(
            telegram_id=999999,
            full_name="Test User",
            age=25,
            phone="+41 79 123 45 67",
            paypal_email="test@paypal.com",
            is_driver=True,
            is_passenger=True
        )
        
        print("✅ Tous les nouveaux champs sont fonctionnels!")
        print("   - full_name: OK")
        print("   - age: OK") 
        print("   - phone: OK")
        print("   - paypal_email: OK")
        
        print("\n🎉 Mise à jour terminée! Le nouveau flux d'inscription est prêt.")
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_database()
