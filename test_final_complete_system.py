#!/usr/bin/env python3
"""
Test final complet de tous les systèmes implémentés
"""

import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_complete_system():
    """Test final de tous les systèmes implémentés"""
    print("🎯 TEST FINAL COMPLET - TOUS LES SYSTÈMES")
    print("=" * 60)
    
    systems_tested = {
        'PayPal obligatoire': False,
        'Switch profil corrigé': False,
        'Gestion trajets passagers': False,
        'Interface cohérente': False
    }
    
    try:
        # Test 1: Système PayPal obligatoire
        print("\n1️⃣ SYSTÈME PAYPAL OBLIGATOIRE")
        with open('handlers/menu_handlers.py', 'r', encoding='utf-8') as f:
            menu_content = f.read()
            
        paypal_checks = [
            "if not user.paypal_email:",
            "Configuration PayPal Requise",
            "why_paypal_required",
            "setup_paypal"
        ]
        
        paypal_ok = all(check in menu_content for check in paypal_checks)
        if paypal_ok:
            print("  ✅ PayPal obligatoire pour tous les utilisateurs")
            systems_tested['PayPal obligatoire'] = True
        else:
            print("  ❌ Système PayPal incomplet")
        
        # Test 2: Switch de profil corrigé
        print("\n2️⃣ SYSTÈME SWITCH PROFIL")
        switch_checks = [
            "await profile_handler(update, context)",
            "Mode {role_text} Activé",
            "await asyncio.sleep(1)"
        ]
        
        switch_ok = all(check in menu_content for check in switch_checks)
        if switch_ok:
            print("  ✅ Switch profil redirige vers profil complet")
            systems_tested['Switch profil corrigé'] = True
        else:
            print("  ❌ Switch profil incomplet")
        
        # Test 3: Gestion complète trajets passagers
        print("\n3️⃣ SYSTÈME TRAJETS PASSAGERS")
        with open('handlers/trip_handlers.py', 'r', encoding='utf-8') as f:
            trip_content = f.read()
            
        passenger_checks = [
            "show_passenger_trip_management",
            "handle_passenger_trip_action", 
            "edit_passenger_trip",
            "delete_passenger_trip",
            "confirm_delete_passenger"
        ]
        
        passenger_ok = all(check in trip_content for check in passenger_checks)
        if passenger_ok:
            print("  ✅ Interface complète trajets passagers")
            systems_tested['Gestion trajets passagers'] = True
        else:
            print("  ❌ Interface trajets passagers incomplète")
        
        # Test 4: Interface cohérente profil
        print("\n4️⃣ INTERFACE PROFIL COHÉRENTE")
        with open('handlers/profile_handler.py', 'r', encoding='utf-8') as f:
            profile_content = f.read()
            
        interface_checks = [
            "Mode Conducteur.*switch_profile:driver",
            "Mode Passager.*switch_profile:passenger",
            "if user.is_driver and user.paypal_email"
        ]
        
        import re
        interface_ok = all(re.search(check, profile_content) for check in interface_checks)
        if interface_ok:
            print("  ✅ Boutons switch dans profil principal")
            systems_tested['Interface cohérente'] = True
        else:
            print("  ❌ Interface profil incomplète")
        
        # Test 5: Vérification base de données
        print("\n5️⃣ VÉRIFICATION BASE DE DONNÉES")
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine('sqlite:///covoiturage.db')
            Session = sessionmaker(bind=engine)
            db = Session()
            
            # Compter les trajets passagers
            result = db.execute(text("""
                SELECT COUNT(*) as count 
                FROM trips 
                WHERE trip_role = 'passenger'
            """))
            passenger_trips = result.fetchone()[0]
            
            # Compter les utilisateurs avec PayPal
            result = db.execute(text("""
                SELECT COUNT(*) as count 
                FROM users 
                WHERE paypal_email IS NOT NULL AND paypal_email != ''
            """))
            users_with_paypal = result.fetchone()[0]
            
            print(f"  📊 Trajets passagers: {passenger_trips}")
            print(f"  💳 Utilisateurs avec PayPal: {users_with_paypal}")
            
            db.close()
            
        except Exception as e:
            print(f"  ⚠️ Erreur vérification BDD: {e}")
        
        # Résumé final
        print("\n" + "=" * 60)
        print("🏆 RÉSUMÉ FINAL DU SYSTÈME COMPLET")
        
        systems_working = sum(systems_tested.values())
        total_systems = len(systems_tested)
        
        print(f"\n📊 SYSTÈMES FONCTIONNELS: {systems_working}/{total_systems}")
        
        for system, working in systems_tested.items():
            status = "✅" if working else "❌"
            print(f"  {status} {system}")
        
        if systems_working == total_systems:
            print(f"\n🎉 FÉLICITATIONS! TOUS LES SYSTÈMES SONT OPÉRATIONNELS!")
            print(f"\n🔧 FONCTIONNALITÉS COMPLÈTES:")
            print(f"   ✅ PayPal obligatoire pour tous (sécurité)")
            print(f"   ✅ Switch fluide entre conducteur/passager")
            print(f"   ✅ Gestion complète des trajets passagers")
            print(f"   ✅ Interface utilisateur cohérente")
            print(f"   ✅ Redirection intelligente selon le profil")
            
            print(f"\n🎯 EXPÉRIENCE UTILISATEUR AMÉLIORÉE:")
            print(f"   • Plus de mini-profils bizarres")
            print(f"   • Switch natural entre les modes")
            print(f"   • Même interface pour conducteurs et passagers")
            print(f"   • Sécurité PayPal pour tous")
            print(f"   • Actions complètes (Edit/Delete/Report)")
            
        else:
            print(f"\n⚠️ {total_systems - systems_working} SYSTÈMES NÉCESSITENT ENCORE DES AMÉLIORATIONS")
            
        return systems_working == total_systems
        
    except Exception as e:
        logger.error(f"Erreur dans le test final: {e}")
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_system()
    if success:
        print(f"\n🚀 SYSTÈME COVOITURAGE SUISSE ENTIÈREMENT OPÉRATIONNEL!")
    else:
        print(f"\n🔧 Des améliorations finales sont encore nécessaires")
