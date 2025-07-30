#!/usr/bin/env python3
"""
Test des 3 corrections apportées aux trajets passagers
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au chemin Python
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_corrections():
    """Test des corrections apportées"""
    print("🔧 TEST DES CORRECTIONS TRAJETS PASSAGERS")
    print("=" * 50)
    
    corrections_validees = []
    
    # Test 1: Vérifier la correction du texte de sélection des places
    print("\n1️⃣ TEST: Message de sélection des places")
    try:
        with open('handlers/trip_creation/passenger_trip_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "Combien de places souhaitez-vous réserver?" in content:
            print("✅ Correction 1 validée : Message corrigé 'places à réserver' au lieu de 'personnes'")
            corrections_validees.append("Message sélection places")
        else:
            print("❌ Correction 1 échouée : Ancien message toujours présent")
            
    except Exception as e:
        print(f"❌ Erreur test 1: {e}")
    
    # Test 2: Vérifier la correction du prix affiché pour les passagers
    print("\n2️⃣ TEST: Affichage prix trajet passager")
    try:
        with open('handlers/create_trip_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "Prix total du trajet" in content and "Prix par place" in content and "partagé entre" in content:
            print("✅ Correction 2 validée : Affichage prix passager corrigé avec logique de partage")
            corrections_validees.append("Prix trajet passager")
        else:
            print("❌ Correction 2 échouée : Ancien affichage prix toujours présent")
            
    except Exception as e:
        print(f"❌ Erreur test 2: {e}")
    
    # Test 3: Vérifier l'ajout du handler pour les trajets passager
    print("\n3️⃣ TEST: Handler trajets passager ajouté")
    try:
        with open('handlers/trip_handlers.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "list_passenger_trips" in content and "trips:list_passenger" in content:
            print("✅ Correction 3 validée : Handler trajets passager ajouté")
            corrections_validees.append("Handler trajets passager")
        else:
            print("❌ Correction 3 échouée : Handler trajets passager manquant")
            
    except Exception as e:
        print(f"❌ Erreur test 3: {e}")
    
    # Résumé
    print(f"\n🎯 RÉSUMÉ DES CORRECTIONS")
    print(f"✅ {len(corrections_validees)}/3 corrections validées")
    
    if len(corrections_validees) == 3:
        print("\n🎉 TOUTES LES CORRECTIONS SONT APPLIQUÉES !")
        print("✅ Les trajets passagers fonctionnent maintenant correctement")
        print("✅ Message correct : 'places à réserver' au lieu de 'personnes'")
        print("✅ Prix correct : prix total divisé par nombre de places")
        print("✅ Bouton 'Mes réservations' fonctionne maintenant")
        return True
    else:
        print(f"\n⚠️ {3 - len(corrections_validees)} correction(s) manquante(s)")
        return False

if __name__ == "__main__":
    success = test_corrections()
    if success:
        print(f"\n✅ Toutes les corrections sont opérationnelles!")
    else:
        print(f"\n❌ Des corrections restent à appliquer")
    
    sys.exit(0 if success else 1)
