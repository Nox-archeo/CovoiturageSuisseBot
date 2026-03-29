#!/usr/bin/env python3
"""
Solution temporaire : Gestionnaire de paiements manuels
Traite les paiements en attente automatiquement via interface web PayPal
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db
from database.models import Trip, Booking, User
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_pending_manual_payments():
    """
    Récupère tous les paiements en attente de traitement manuel
    """
    try:
        db = get_db()
        
        # Trouver tous les trajets confirmés mais avec paiements non envoyés
        pending_trips = db.query(Trip).filter(
            Trip.status.in_(['payment_pending_manual', 'payment_error'])
        ).all()
        
        if not pending_trips:
            logger.info("✅ Aucun paiement manuel en attente")
            return []
        
        payments_list = []
        
        for trip in pending_trips:
            # Récupérer les infos du conducteur
            driver = db.query(User).filter(User.id == trip.driver_id).first()
            
            # Calculer les montants
            paid_bookings = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.is_paid == True
            ).all()
            
            total_amount = sum(booking.amount for booking in paid_bookings)
            driver_amount = total_amount * 0.88
            commission_amount = total_amount * 0.12
            
            payment_info = {
                'trip_id': trip.id,
                'driver_name': driver.full_name if driver else f"Conducteur #{trip.driver_id}",
                'driver_email': driver.paypal_email if driver else "NON_CONFIGURÉ",
                'driver_phone': driver.phone if driver else "NON_CONFIGURÉ",
                'trip_route': f"{trip.departure_city} → {trip.arrival_city}",
                'trip_date': trip.departure_time.strftime('%d/%m/%Y à %H:%M'),
                'total_paid': total_amount,
                'driver_amount': driver_amount,
                'commission_amount': commission_amount,
                'passenger_count': len(paid_bookings),
                'status': trip.status
            }
            
            payments_list.append(payment_info)
        
        return payments_list
        
    except Exception as e:
        logger.error(f"Erreur récupération paiements: {e}")
        return []

def generate_paypal_links(payments_list):
    """
    Génère des liens PayPal pour faciliter les paiements manuels
    """
    if not payments_list:
        return
    
    print("\n" + "="*80)
    print("🏦 PAIEMENTS MANUELS PAYPAL - LIENS DE PAIEMENT")
    print("="*80)
    
    for payment in payments_list:
        print(f"\n📍 Trajet #{payment['trip_id']}: {payment['trip_route']}")
        print(f"📅 Date: {payment['trip_date']}")
        print(f"👤 Conducteur: {payment['driver_name']}")
        print(f"📧 PayPal: {payment['driver_email']}")
        print(f"📞 Téléphone: {payment['driver_phone']}")
        print(f"💰 Montant à payer: {payment['driver_amount']:.2f} CHF")
        print(f"👥 Passagers: {payment['passenger_count']}")
        
        # Générer le lien PayPal send money
        if payment['driver_email'] != "NON_CONFIGURÉ":
            amount_str = f"{payment['driver_amount']:.2f}".replace('.', '%2E')
            paypal_link = (
                f"https://www.paypal.com/paypalme/send?"
                f"recipient={payment['driver_email']}"
                f"&amount={amount_str}"
                f"&currency_code=CHF"
                f"&note=CovoiturageSuisse%20-%20{payment['trip_route']}%20{payment['trip_date']}"
            )
            print(f"🔗 Lien PayPal direct: {paypal_link}")
        else:
            print("⚠️  Email PayPal non configuré - Contact manuel nécessaire")
        
        print("-" * 60)
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"   Paiements en attente: {len(payments_list)}")
    print(f"   Montant total conducteurs: {sum(p['driver_amount'] for p in payments_list):.2f} CHF")
    print(f"   Commission totale: {sum(p['commission_amount'] for p in payments_list):.2f} CHF")

def mark_payment_as_completed(trip_id: int):
    """
    Marque un paiement comme terminé après envoi manuel
    """
    try:
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if trip:
            trip.status = 'completed_paid'
            db.commit()
            logger.info(f"✅ Trajet #{trip_id} marqué comme payé")
            return True
        else:
            logger.error(f"❌ Trajet #{trip_id} non trouvé")
            return False
    
    except Exception as e:
        logger.error(f"Erreur marquage paiement: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Recherche des paiements en attente...")
    
    pending_payments = get_pending_manual_payments()
    
    if pending_payments:
        generate_paypal_links(pending_payments)
        
        print(f"\n📋 INSTRUCTIONS:")
        print(f"1. Cliquez sur chaque lien PayPal pour envoyer les paiements")
        print(f"2. Une fois un paiement envoyé, utilisez:")
        print(f"   python manual_payment_manager.py --complete TRIP_ID")
        print(f"3. Ou marquez tous comme payés:")
        print(f"   python manual_payment_manager.py --complete-all")
    else:
        print("✅ Aucun paiement manuel en attente !")
    
    # Gestion des arguments de ligne de commande
    if len(sys.argv) > 1:
        if sys.argv[1] == "--complete" and len(sys.argv) > 2:
            trip_id = int(sys.argv[2])
            if mark_payment_as_completed(trip_id):
                print(f"✅ Trajet #{trip_id} marqué comme payé")
            else:
                print(f"❌ Erreur marquage trajet #{trip_id}")
        
        elif sys.argv[1] == "--complete-all":
            for payment in pending_payments:
                if mark_payment_as_completed(payment['trip_id']):
                    print(f"✅ Trajet #{payment['trip_id']} marqué comme payé")