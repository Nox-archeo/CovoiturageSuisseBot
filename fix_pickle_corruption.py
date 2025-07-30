#!/usr/bin/env python3
"""
Script pour corriger la corruption du fichier pickle de persistance.
"""

import os
import logging
from pathlib import Path

def fix_pickle_corruption():
    """Supprime les fichiers pickle corrompus."""
    
    pickle_files = [
        "bot_data.pickle",
        "conversations.pickle", 
        "user_data.pickle",
        "chat_data.pickle"
    ]
    
    print("🔧 Nettoyage des fichiers pickle corrompus...")
    
    for pickle_file in pickle_files:
        if os.path.exists(pickle_file):
            try:
                os.remove(pickle_file)
                print(f"✅ Supprimé: {pickle_file}")
            except Exception as e:
                print(f"❌ Erreur lors de la suppression de {pickle_file}: {e}")
        else:
            print(f"ℹ️  Fichier inexistant: {pickle_file}")
    
    print("\n🎉 Nettoyage terminé !")
    print("Le bot peut maintenant redémarrer normalement.")
    print("Les données de conversation seront réinitialisées.")
    print("\n📋 Ce qui est préservé :")
    print("✅ Tous vos trajets (base SQLite)")
    print("✅ Tous vos utilisateurs (base SQLite)")
    print("✅ Toutes vos réservations (base SQLite)")
    print("✅ Tous les profils PayPal (base SQLite)")
    print("✅ Toutes les nouvelles communes ajoutées")
    print("✅ Le système dual-role conducteur/passager")
    print("✅ Les distances routières améliorées")

if __name__ == "__main__":
    fix_pickle_corruption()
