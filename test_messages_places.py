#!/usr/bin/env python3
"""
Test de vérification des messages de sélection des places
"""

def test_messages_places():
    """Vérifie que tous les messages sont correctement adaptés selon le rôle"""
    print("🔧 TEST DES MESSAGES DE SÉLECTION DES PLACES")
    print("=" * 60)
    
    corrections_validees = []
    
    try:
        with open('handlers/create_trip_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Compter les occurrences de l'ancien message (incorrect)
        ancien_message_count = content.count("Combien de places disponibles? (1-8)")
        
        # Compter les occurrences du nouveau message conducteur
        nouveau_message_conducteur = content.count("seats_message = \"Étape 6️⃣ - Combien de places disponibles? (1-8)\"")
        
        # Compter les occurrences du nouveau message passager
        nouveau_message_passager = content.count("seats_message = \"Étape 6️⃣ - Combien de places voulez-vous réserver? (1-4)\"")
        
        # Compter les vérifications de rôle
        verifications_role = content.count("trip_role = context.user_data.get('trip_type', 'driver')")
        
        print(f"📊 STATISTIQUES DES MESSAGES:")
        print(f"❌ Anciens messages fixes: {ancien_message_count}")
        print(f"✅ Messages conducteur adaptés: {nouveau_message_conducteur}")
        print(f"✅ Messages passager adaptés: {nouveau_message_passager}")
        print(f"🔍 Vérifications de rôle: {verifications_role}")
        
        # Validation
        tests_passes = []
        
        if ancien_message_count == 0:
            print("\n✅ TEST 1 RÉUSSI: Aucun ancien message fixe trouvé")
            tests_passes.append("Anciens messages supprimés")
        else:
            print(f"\n❌ TEST 1 ÉCHOUÉ: {ancien_message_count} ancien(s) message(s) fixe(s) trouvé(s)")
        
        if nouveau_message_conducteur >= 5:  # On s'attend à 5 occurrences
            print("✅ TEST 2 RÉUSSI: Messages conducteur correctement adaptés")
            tests_passes.append("Messages conducteur")
        else:
            print(f"❌ TEST 2 ÉCHOUÉ: Seulement {nouveau_message_conducteur} message(s) conducteur adapté(s)")
        
        if nouveau_message_passager >= 5:  # On s'attend à 5 occurrences
            print("✅ TEST 3 RÉUSSI: Messages passager correctement adaptés")
            tests_passes.append("Messages passager")
        else:
            print(f"❌ TEST 3 ÉCHOUÉ: Seulement {nouveau_message_passager} message(s) passager adapté(s)")
        
        if verifications_role >= 5:  # On s'attend à 5 vérifications
            print("✅ TEST 4 RÉUSSI: Vérifications de rôle ajoutées")
            tests_passes.append("Vérifications rôle")
        else:
            print(f"❌ TEST 4 ÉCHOUÉ: Seulement {verifications_role} vérification(s) de rôle")
            
        # Résumé
        print(f"\n🎯 RÉSUMÉ DES CORRECTIONS")
        print(f"✅ {len(tests_passes)}/4 tests réussis")
        
        if len(tests_passes) == 4:
            print("\n🎉 TOUTES LES CORRECTIONS SONT VALIDÉES !")
            print("✅ Conducteur: 'Combien de places disponibles? (1-8)'")
            print("✅ Passager: 'Combien de places voulez-vous réserver? (1-4)'")
            print("✅ Messages adaptés dynamiquement selon le rôle")
            return True
        else:
            print(f"\n⚠️ {4 - len(tests_passes)} test(s) échoué(s)")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    success = test_messages_places()
    if success:
        print(f"\n✅ CORRECTION COMPLÈTE: Messages adaptés selon le rôle!")
    else:
        print(f"\n❌ CORRECTION INCOMPLÈTE: Certains messages restent à corriger")
    
    print(f"\n💡 NOTE: Cette correction touche le fichier 'create_trip_handler.py'")
    print(f"📝 Les messages s'adaptent maintenant selon que l'utilisateur soit conducteur ou passager")
