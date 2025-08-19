#!/usr/bin/env python3
"""
Endpoint d'administration pour forcer le traitement des paiements PayPal
"""

import os
import sys
import asyncio
from datetime import datetime
sys.path.append('/Users/margaux/CovoiturageSuisse')

from database.db_manager import get_db
from database.models import Booking
from paypal_webhook_handler import handle_payment_completion

async def force_process_payment(payment_id: str = None, booking_id: int = None):
    """
    Force le traitement d'un paiement PayPal
    
    Args:
        payment_id: ID du paiement PayPal
        booking_id: ID de la réservation
    """
    
    print("🔧 FORCE TRAITEMENT PAIEMENT PAYPAL")
    print("=" * 50)
    
    try:
        db = get_db()
        
        if booking_id:
            # Recherche par ID de réservation
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                print(f"❌ Réservation {booking_id} non trouvée")
                return False
            
            payment_id = booking.paypal_payment_id
            if not payment_id:
                print(f"❌ Aucun payment_id PayPal pour la réservation {booking_id}")
                return False
                
            print(f"🔍 Réservation trouvée: {booking_id}")
            print(f"   PayPal ID: {payment_id}")
            print(f"   Status actuel: {booking.status}")
            print(f"   Is_Paid: {booking.is_paid}")
            print(f"   Payment_Status: {booking.payment_status}")
        
        elif payment_id:
            # Recherche par payment_id PayPal
            booking = db.query(Booking).filter(Booking.paypal_payment_id == payment_id).first()
            if booking:
                print(f"🔍 Réservation trouvée pour PayPal {payment_id}: {booking.id}")
            else:
                print(f"⚠️ Aucune réservation trouvée pour PayPal {payment_id}")
                print("   Traitement du webhook quand même...")
        
        else:
            print("❌ Il faut spécifier soit payment_id soit booking_id")
            return False
        
        # Forcer le traitement du webhook
        print(f"\n🚀 Force traitement webhook pour payment_id: {payment_id}")
        result = await handle_payment_completion(payment_id, bot=None)
        
        if result:
            print("✅ Traitement réussi !")
            
            # Vérifier l'état après traitement
            if booking_id:
                booking_after = db.query(Booking).filter(Booking.id == booking_id).first()
                if booking_after:
                    print(f"\n📊 État après traitement:")
                    print(f"   Status: {booking_after.status}")
                    print(f"   Is_Paid: {booking_after.is_paid}")
                    print(f"   Payment_Status: {booking_after.payment_status}")
        else:
            print("❌ Échec du traitement")
            
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors du force traitement: {e}")
        import traceback
        traceback.print_exc()
        return False

async def search_recent_payments():
    """Recherche les paiements récents non traités"""
    
    print("\n🔍 RECHERCHE PAIEMENTS NON TRAITÉS")
    print("=" * 40)
    
    try:
        db = get_db()
        
        # Paiements PayPal non confirmés
        unconfirmed = db.query(Booking).filter(
            Booking.paypal_payment_id.isnot(None),
            Booking.is_paid == False
        ).order_by(Booking.id.desc()).limit(10).all()
        
        if unconfirmed:
            print(f"⏳ {len(unconfirmed)} paiement(s) non confirmé(s):")
            for booking in unconfirmed:
                print(f"   ID: {booking.id}, PayPal: {booking.paypal_payment_id}, Amount: {booking.amount}, Status: {booking.status}")
                
                # Proposer de traiter automatiquement
                if booking.paypal_payment_id:
                    print(f"   🔧 Pour traiter: python3 force_payment_processing.py --payment-id {booking.paypal_payment_id}")
        else:
            print("✅ Aucun paiement en attente")
            
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")

async def main():
    """Fonction principale"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--payment-id" and len(sys.argv) > 2:
            payment_id = sys.argv[2]
            await force_process_payment(payment_id=payment_id)
        elif sys.argv[1] == "--booking-id" and len(sys.argv) > 2:
            booking_id = int(sys.argv[2])
            await force_process_payment(booking_id=booking_id)
        else:
            print("Usage:")
            print("  python3 force_payment_processing.py --payment-id <paypal_payment_id>")
            print("  python3 force_payment_processing.py --booking-id <booking_id>")
    else:
        # Recherche automatique
        await search_recent_payments()

if __name__ == "__main__":
    asyncio.run(main())
