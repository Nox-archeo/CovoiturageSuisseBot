#!/usr/bin/env python3
"""
Test pour identifier l'erreur du profil
"""
import sys
sys.path.insert(0, '/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db
from database.models import User

def test_profile():
    try:
        db = get_db()
        user = db.query(User).filter(User.id == 1).first()
        if user:
            print(f"✅ Utilisateur trouvé: {user.first_name} {user.last_name}")
        else:
            print("❌ Utilisateur ID 1 non trouvé")
        
        # Test import de get_user_stats
        from handlers.profile_handler import get_user_stats
        print("✅ Import get_user_stats réussi")
        
        # Test exécution get_user_stats
        stats = get_user_stats(db, user)
        print(f"✅ Stats calculées: {stats}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_profile()
