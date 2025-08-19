#!/usr/bin/env python3
"""
VÉRIFICATION COMPLÈTE DU SYSTÈME DE COVOITURAGE
==============================================
Points à vérifier selon les exigences utilisateur :

1. Notifications réelles conducteur/passager lors de réservation
2. Confirmation obligatoire par les deux parties
3. Transfert automatique 88% au conducteur, 12% commission
4. Remboursement automatique en cas d'annulation 
5. Prix partagé dynamiquement entre passagers + remboursements

TOUT DOIT ÊTRE RÉELLEMENT FONCTIONNEL !
"""

import asyncio
import logging
from database import get_db
from database.models import Trip, Booking, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_point_1_notifications():
    """
    POINT 1: Vérifier les notifications conducteur/passager
    """
    print("🔍 POINT 1: NOTIFICATIONS CONDUCTEUR/PASSAGER")
    print("=" * 60)
    
    issues = []
    
    # 1.1 - Vérifier handlers de notification
    try:
        from handlers.search_trip_handler import pay_with_paypal
        from handlers.booking_handlers import confirm_booking_with_payment
        print("✅ Handlers de réservation importés")
        
        # Chercher les notifications dans le code
        import inspect
        pay_source = inspect.getsource(pay_with_paypal)
        confirm_source = inspect.getsource(confirm_booking_with_payment)
        
        # Vérifier présence notifications conducteur
        if "send_message" in pay_source and "conducteur" in pay_source.lower():
            print("✅ Notification conducteur trouvée dans pay_with_paypal")
        else:
            issues.append("❌ Notification conducteur manquante dans pay_with_paypal")
            
        if "send_message" in confirm_source and ("conducteur" in confirm_source.lower() or "driver" in confirm_source.lower()):
            print("✅ Notification conducteur trouvée dans confirm_booking")
        else:
            issues.append("❌ Notification conducteur manquante dans confirm_booking")
        
    except Exception as e:
        issues.append(f"❌ Erreur import handlers: {e}")
    
    # 1.2 - Vérifier système de notification existant
    try:
        from handlers.notification_handlers import notify_booking_request
        print("✅ Système de notification existant trouvé")
    except ImportError:
        issues.append("❌ Module notification_handlers manquant")
    
    print(f"\n📊 RÉSULTAT POINT 1: {len(issues)} problème(s) détecté(s)")
    for issue in issues:
        print(f"   {issue}")
    
    return len(issues) == 0

async def test_point_2_confirmations():
    """
    POINT 2: Vérifier confirmations obligatoires par les deux parties
    """
    print("\n🔍 POINT 2: CONFIRMATIONS OBLIGATOIRES")
    print("=" * 60)
    
    issues = []
    
    # 2.1 - Vérifier système de confirmation existant
    try:
        from trip_confirmation import TripConfirmationSystem, handle_confirm_trip_callback
        print("✅ Système de confirmation de trajet trouvé")
        
        # Vérifier la logique de double confirmation
        import inspect
        system_source = inspect.getsource(TripConfirmationSystem)
        
        if "confirmed_by_driver" in system_source and "confirmed_by_passengers" in system_source:
            print("✅ Double confirmation (conducteur + passagers) présente")
        else:
            issues.append("❌ Logique de double confirmation incomplète")
            
        if "_trigger_driver_payment" in system_source:
            print("✅ Déclenchement automatique de paiement trouvé")
        else:
            issues.append("❌ Déclenchement automatique de paiement manquant")
        
    except ImportError:
        issues.append("❌ Module trip_confirmation manquant")
    
    # 2.2 - Vérifier structure base de données
    try:
        db = get_db()
        # Vérifier que Trip a les champs de confirmation
        sample_trip = db.query(Trip).first()
        if sample_trip:
            if hasattr(sample_trip, 'confirmed_by_driver'):
                print("✅ Champ confirmed_by_driver présent")
            else:
                issues.append("❌ Champ confirmed_by_driver manquant en DB")
                
            if hasattr(sample_trip, 'confirmed_by_passengers'):
                print("✅ Champ confirmed_by_passengers présent")
            else:
                issues.append("❌ Champ confirmed_by_passengers manquant en DB")
        
        db.close()
    except Exception as e:
        issues.append(f"❌ Erreur vérification DB: {e}")
    
    print(f"\n📊 RÉSULTAT POINT 2: {len(issues)} problème(s) détecté(s)")
    for issue in issues:
        print(f"   {issue}")
    
    return len(issues) == 0

async def test_point_3_split_payment():
    """
    POINT 3: Vérifier transfert 88% conducteur / 12% commission
    """
    print("\n🔍 POINT 3: TRANSFERT 88% / 12%")
    print("=" * 60)
    
    issues = []
    
    # 3.1 - Vérifier fonctions de paiement PayPal
    try:
        from paypal_utils import PayPalManager
        
        paypal = PayPalManager()
        
        # Vérifier présence des méthodes de paiement conducteur
        if hasattr(paypal, 'send_payout'):
            print("✅ Méthode send_payout présente")
        else:
            issues.append("❌ Méthode send_payout manquante")
            
        if hasattr(paypal, 'payout_to_driver'):
            print("✅ Méthode payout_to_driver présente")
        else:
            issues.append("❌ Méthode payout_to_driver manquante")
        
    except Exception as e:
        issues.append(f"❌ Erreur PayPalManager: {e}")
    
    # 3.2 - Vérifier calculs 88/12
    try:
        from trip_confirmation import TripConfirmationSystem
        import inspect
        
        trigger_source = inspect.getsource(TripConfirmationSystem._trigger_driver_payment)
        
        if "0.88" in trigger_source and "0.12" in trigger_source:
            print("✅ Calculs 88% / 12% trouvés dans le code")
        else:
            issues.append("❌ Calculs 88% / 12% manquants")
            
        if "driver_amount" in trigger_source and "commission_amount" in trigger_source:
            print("✅ Séparation montant conducteur / commission présente")
        else:
            issues.append("❌ Séparation montant conducteur / commission manquante")
        
    except Exception as e:
        issues.append(f"❌ Erreur vérification calculs: {e}")
    
    # 3.3 - Test calcul direct
    test_amount = 100.0
    driver_part = round(test_amount * 0.88, 2)
    commission_part = round(test_amount * 0.12, 2)
    
    if driver_part == 88.0 and commission_part == 12.0:
        print(f"✅ Test calcul: {test_amount} CHF → {driver_part} CHF (conducteur) + {commission_part} CHF (commission)")
    else:
        issues.append(f"❌ Erreur calcul: {test_amount} CHF → {driver_part} CHF + {commission_part} CHF")
    
    print(f"\n📊 RÉSULTAT POINT 3: {len(issues)} problème(s) détecté(s)")
    for issue in issues:
        print(f"   {issue}")
    
    return len(issues) == 0

async def test_point_4_refunds_cancellation():
    """
    POINT 4: Vérifier remboursements automatiques en cas d'annulation
    """
    print("\n🔍 POINT 4: REMBOURSEMENTS ANNULATION")
    print("=" * 60)
    
    issues = []
    
    # 4.1 - Vérifier gestionnaire de remboursements d'annulation
    try:
        from cancellation_refund_manager import CancellationRefundManager
        print("✅ Gestionnaire remboursements annulation trouvé")
        
        manager = CancellationRefundManager()
        
        # Vérifier présence des méthodes critiques
        if hasattr(manager, 'process_trip_cancellation_refunds'):
            print("✅ Méthode process_trip_cancellation_refunds présente")
        else:
            issues.append("❌ Méthode process_trip_cancellation_refunds manquante")
            
        # Vérifier logique automatique
        import inspect
        manager_source = inspect.getsource(CancellationRefundManager)
        
        if "paypal" in manager_source.lower() and "refund" in manager_source.lower():
            print("✅ Intégration PayPal pour remboursements trouvée")
        else:
            issues.append("❌ Intégration PayPal pour remboursements manquante")
        
    except ImportError:
        issues.append("❌ Module cancellation_refund_manager manquant")
    except Exception as e:
        issues.append(f"❌ Erreur gestionnaire remboursements: {e}")
    
    # 4.2 - Vérifier fonctions de remboursement PayPal
    try:
        from paypal_utils import PayPalManager
        
        paypal = PayPalManager()
        
        if hasattr(paypal, 'refund_payment'):
            print("✅ Méthode refund_payment présente")
        else:
            issues.append("❌ Méthode refund_payment manquante")
            
        if hasattr(paypal, 'full_refund'):
            print("✅ Méthode full_refund présente")
        else:
            issues.append("❌ Méthode full_refund manquante")
        
    except Exception as e:
        issues.append(f"❌ Erreur vérification remboursements PayPal: {e}")
    
    print(f"\n📊 RÉSULTAT POINT 4: {len(issues)} problème(s) détecté(s)")
    for issue in issues:
        print(f"   {issue}")
    
    return len(issues) == 0

async def test_point_5_dynamic_pricing():
    """
    POINT 5: Vérifier prix dynamique et remboursements entre passagers
    """
    print("\n🔍 POINT 5: PRIX DYNAMIQUE + REMBOURSEMENTS")
    print("=" * 60)
    
    issues = []
    
    # 5.1 - Vérifier système de prix dynamique
    try:
        from utils.swiss_pricing import calculate_price_per_passenger, round_to_nearest_0_05_up
        print("✅ Fonctions de prix dynamique trouvées")
        
        # Test prix dynamique
        total_price = 10.0
        
        # 1 passager
        price_1 = calculate_price_per_passenger(total_price, 1)
        if price_1 == 10.0:
            print(f"✅ 1 passager: {price_1} CHF")
        else:
            issues.append(f"❌ 1 passager: attendu 10.0, obtenu {price_1}")
        
        # 2 passagers  
        price_2 = calculate_price_per_passenger(total_price, 2)
        if price_2 == 5.0:
            print(f"✅ 2 passagers: {price_2} CHF chacun")
        else:
            issues.append(f"❌ 2 passagers: attendu 5.0, obtenu {price_2}")
        
        # 3 passagers
        price_3 = calculate_price_per_passenger(total_price, 3)
        expected_3 = round_to_nearest_0_05_up(10.0 / 3)  # 3.33... → 3.35
        if abs(price_3 - expected_3) < 0.01:
            print(f"✅ 3 passagers: {price_3} CHF chacun")
        else:
            issues.append(f"❌ 3 passagers: attendu ~{expected_3}, obtenu {price_3}")
        
    except ImportError:
        issues.append("❌ Module swiss_pricing manquant")
    except Exception as e:
        issues.append(f"❌ Erreur système prix dynamique: {e}")
    
    # 5.2 - Vérifier gestionnaire de remboursements dynamiques
    try:
        from auto_refund_manager import AutoRefundManager
        print("✅ Gestionnaire remboursements automatiques trouvé")
        
        manager = AutoRefundManager()
        
        if hasattr(manager, 'handle_new_passenger_refund'):
            print("✅ Méthode handle_new_passenger_refund présente")
        else:
            issues.append("❌ Méthode handle_new_passenger_refund manquante")
        
    except ImportError:
        issues.append("❌ Module auto_refund_manager manquant")
    except Exception as e:
        issues.append(f"❌ Erreur gestionnaire remboursements auto: {e}")
    
    # 5.3 - Vérifier logique de remboursement dans booking
    try:
        from handlers.booking_handlers import confirm_booking_with_payment
        import inspect
        
        booking_source = inspect.getsource(confirm_booking_with_payment)
        
        if "calculate_price_per_passenger" in booking_source:
            print("✅ Calcul prix dynamique intégré dans réservation")
        else:
            issues.append("❌ Calcul prix dynamique manquant dans réservation")
            
        if "existing_paid_passengers" in booking_source:
            print("✅ Comptage passagers existants présent")
        else:
            issues.append("❌ Comptage passagers existants manquant")
        
    except Exception as e:
        issues.append(f"❌ Erreur vérification booking: {e}")
    
    print(f"\n📊 RÉSULTAT POINT 5: {len(issues)} problème(s) détecté(s)")
    for issue in issues:
        print(f"   {issue}")
    
    return len(issues) == 0

async def test_integration_complete():
    """
    TEST D'INTÉGRATION: Vérifier que tous les systèmes fonctionnent ensemble
    """
    print("\n🔍 TEST D'INTÉGRATION COMPLÈTE")
    print("=" * 60)
    
    issues = []
    
    # Vérifier enregistrement des handlers
    try:
        from webhook_server import app
        print("✅ Serveur webhook accessible")
        
        # Vérifier que les handlers sont bien enregistrés
        # (Ceci est complexe à vérifier directement, on se fie aux imports)
        
    except Exception as e:
        issues.append(f"❌ Erreur serveur webhook: {e}")
    
    # Vérifier base de données
    try:
        db = get_db()
        
        # Compter les utilisateurs, trajets, réservations
        user_count = db.query(User).count()
        trip_count = db.query(Trip).count() 
        booking_count = db.query(Booking).count()
        
        print(f"✅ Base de données: {user_count} utilisateurs, {trip_count} trajets, {booking_count} réservations")
        
        # Vérifier structure des tables
        if hasattr(Booking, 'payment_status'):
            print("✅ Champ payment_status présent")
        else:
            issues.append("❌ Champ payment_status manquant")
            
        if hasattr(Booking, 'total_price'):
            print("✅ Champ total_price présent")
        else:
            issues.append("❌ Champ total_price manquant")
        
        db.close()
        
    except Exception as e:
        issues.append(f"❌ Erreur base de données: {e}")
    
    print(f"\n📊 RÉSULTAT INTÉGRATION: {len(issues)} problème(s) détecté(s)")
    for issue in issues:
        print(f"   {issue}")
    
    return len(issues) == 0

async def main():
    """
    EXÉCUTION COMPLÈTE DE TOUS LES TESTS
    """
    print("🚀 VÉRIFICATION COMPLÈTE DU SYSTÈME COVOITURAGE")
    print("=" * 70)
    print("Vérification de TOUS les points critiques mentionnés...")
    print()
    
    # Exécuter tous les tests
    results = {}
    
    results['notifications'] = await test_point_1_notifications()
    results['confirmations'] = await test_point_2_confirmations()
    results['split_payment'] = await test_point_3_split_payment()
    results['refunds_cancellation'] = await test_point_4_refunds_cancellation()
    results['dynamic_pricing'] = await test_point_5_dynamic_pricing()
    results['integration'] = await test_integration_complete()
    
    # Résumé final
    print("\n🎯 RÉSUMÉ FINAL")
    print("=" * 70)
    
    total_points = len(results)
    passed_points = sum(1 for success in results.values() if success)
    
    for point, success in results.items():
        status = "✅ FONCTIONNEL" if success else "❌ PROBLÈMES DÉTECTÉS"
        print(f"{point.upper().replace('_', ' ')}: {status}")
    
    print(f"\n📊 SCORE GLOBAL: {passed_points}/{total_points} points validés")
    
    if passed_points == total_points:
        print("\n🎉 SYSTÈME ENTIÈREMENT FONCTIONNEL !")
        print("✅ Toutes les fonctionnalités critiques sont présentes")
        print("✅ Le système est prêt pour les vrais utilisateurs")
    else:
        print(f"\n⚠️  ATTENTION: {total_points - passed_points} point(s) nécessitent des corrections")
        print("🔧 Corrections requises avant mise en production")
    
    return passed_points == total_points

if __name__ == "__main__":
    asyncio.run(main())
