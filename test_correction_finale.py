#!/usr/bin/env python3
"""
Test final de validation des corrections de messages passagers
"""

def test_correction_finale():
    """Test final pour valider que tous les messages sont corrigés"""
    print("🎯 TEST FINAL - CORRECTION MESSAGES TRAJETS PASSAGERS")
    print("=" * 60)
    
    try:
        with open('handlers/create_trip_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Chercher les messages hardcodés (pas dans des variables)
        lignes = content.split('\n')
        messages_hardcodes = []
        
        for i, ligne in enumerate(lignes):
            # Chercher les lignes qui contiennent le message directement (pas dans une variable)
            if '"Étape 6️⃣ - Combien de places disponibles? (1-8)"' in ligne and 'seats_message =' not in ligne:
                messages_hardcodes.append(f"Ligne {i+1}: {ligne.strip()}")
        
        print(f"📊 VÉRIFICATION DES MESSAGES HARDCODÉS")
        if len(messages_hardcodes) == 0:
            print("✅ AUCUN message hardcodé trouvé - Parfait !")
            correction_1 = True
        else:
            print(f"❌ {len(messages_hardcodes)} message(s) hardcodé(s) trouvé(s):")
            for msg in messages_hardcodes:
                print(f"   {msg}")
            correction_1 = False
        
        # Vérifier la présence des adaptations de rôle
        adaptations_role = content.count("trip_role = context.user_data.get('trip_type', 'driver')")
        conditions_passager = content.count("if trip_role == 'passenger':")
        
        print(f"\n📊 VÉRIFICATION DES ADAPTATIONS DE RÔLE")
        print(f"🔍 Récupérations du rôle: {adaptations_role}")
        print(f"🔀 Conditions passager: {conditions_passager}")
        
        if adaptations_role >= 5 and conditions_passager >= 5:
            print("✅ Adaptations de rôle correctement implémentées")
            correction_2 = True
        else:
            print("❌ Adaptations de rôle insuffisantes")
            correction_2 = False
        
        # Vérifier les messages adaptatifs
        messages_passager = content.count('"Étape 6️⃣ - Combien de places voulez-vous réserver? (1-4)"')
        messages_conducteur = content.count('"Étape 6️⃣ - Combien de places disponibles? (1-8)"')
        
        print(f"\n📊 VÉRIFICATION DES MESSAGES ADAPTATIFS")
        print(f"👥 Messages passager: {messages_passager}")
        print(f"🚗 Messages conducteur: {messages_conducteur}")
        
        if messages_passager >= 5 and messages_conducteur >= 5:
            print("✅ Messages adaptatifs correctement implémentés")
            correction_3 = True
        else:
            print("❌ Messages adaptatifs insuffisants")
            correction_3 = False
        
        # Résumé final
        corrections_validees = sum([correction_1, correction_2, correction_3])
        
        print(f"\n🎯 RÉSULTATS FINALS")
        print(f"✅ Corrections validées: {corrections_validees}/3")
        
        if corrections_validees == 3:
            print("\n🎉 TOUTES LES CORRECTIONS SONT PARFAITES !")
            print("✅ Plus de messages hardcodés")
            print("✅ Adaptations de rôle fonctionnelles") 
            print("✅ Messages différents pour conducteur/passager")
            print("\n💡 RÉSULTAT:")
            print("   🚗 Conducteur: 'Combien de places disponibles? (1-8)'")
            print("   👥 Passager: 'Combien de places voulez-vous réserver? (1-4)'")
            return True
        else:
            print(f"\n⚠️ {3 - corrections_validees} correction(s) manquante(s)")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    success = test_correction_finale()
    if success:
        print(f"\n✅ CORRECTION 100% TERMINÉE !")
        print(f"🚀 Les messages s'adaptent maintenant correctement selon le rôle")
    else:
        print(f"\n❌ CORRECTION INCOMPLÈTE")
        print(f"📝 Quelques ajustements restent nécessaires")
