#!/usr/bin/env python3
"""
Script pour démarrer le bot et tester les corrections
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Démarre le bot avec les corrections"""
    print("🚀 Démarrage du bot avec les corrections...")
    print("=" * 60)
    
    print("✅ Corrections appliquées:")
    print("  - Bouton 'Créer un trajet' → redirige vers création")
    print("  - Bouton 'Mes trajets' → fonction unifiée")
    print("  - Annulation de trajets → fonctionne pour tous les utilisateurs")
    print("  - Ordre des handlers optimisé")
    
    print("\n🧪 Pour tester:")
    print("  1. Tapez /start")
    print("  2. Cliquez sur 'Créer un trajet' → doit vous demander conducteur/passager")
    print("  3. Allez sur votre profil → 'Mes trajets' → doit afficher vos trajets")
    print("  4. Testez l'annulation d'un trajet → doit fonctionner")
    
    print("\n⚠️  Si un bouton ne fonctionne pas, vérifiez les logs pour voir les callbacks.")
    print("=" * 60)
    
    # Import and start the bot
    try:
        from bot import main as start_bot
        start_bot()
    except KeyboardInterrupt:
        print("\n👋 Bot arrêté par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
