#!/usr/bin/env python3
"""
Test simple du remboursement avec connexion directe à la base PostgreSQL
"""

import asyncio
import psycopg2
import logging
from unittest.mock import AsyncMock, MagicMock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_refund():
    """Test simple avec la vraie base de données"""
    try:
        # Connexion directe à PostgreSQL (comme real_db_check.py)
        conn = psycopg2.connect(
            host="dpg-d26ah2muk2gs73bqjnn0-a.oregon-postgres.render.com",
            database="covoiturage_qw9c",
            user="covoiturage_qw9c_user", 
            password="fnDhW4g3Mv9aFIJdJO46lJKYhOJJl4i8",
            port=5432,
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        # Vérifier la réservation #23
        cursor.execute("""
            SELECT id, passenger_id, total_price, paypal_payment_id, is_paid, status, payment_status
            FROM bookings 
            WHERE id = 23
        """)
        
        booking = cursor.fetchone()
        
        if not booking:
            print("❌ Réservation #23 non trouvée")
            return False
            
        print(f"✅ Réservation trouvée: {booking}")
        
        # Récupérer les infos du passager
        cursor.execute("""
            SELECT id, telegram_id, paypal_email 
            FROM users 
            WHERE id = %s
        """, (booking[1],))
        
        passenger = cursor.fetchone()
        print(f"👤 Passager: {passenger}")
        
        # Test PayPal seulement
        from paypal_utils import PayPalManager
        
        paypal = PayPalManager()
        print(f"💳 Test PayPal avec payment_id: {booking[3]}")
        
        # Tester find_payment
        success, payment_details = paypal.find_payment(booking[3])
        
        if success:
            print("✅ PayPal find_payment fonctionne!")
            print(f"🔍 Détails: {payment_details}")
            
            # Extraire capture_id
            capture_id = None
            if 'purchase_units' in payment_details:
                for unit in payment_details['purchase_units']:
                    if 'payments' in unit and 'captures' in unit['payments']:
                        for capture in unit['payments']['captures']:
                            if capture.get('status') == 'COMPLETED':
                                capture_id = capture['id']
                                break
            
            if capture_id:
                print(f"💡 Capture ID trouvé: {capture_id}")
                
                # Tester le remboursement 
                success_refund, refund_data = paypal.refund_payment(
                    capture_id=capture_id,
                    amount=1.0,
                    currency="CHF"
                )
                
                if success_refund:
                    print("🎉 REMBOURSEMENT RÉUSSI!")
                    print(f"💰 Données remboursement: {refund_data}")
                    return True
                else:
                    print("❌ Échec remboursement")
                    return False
            else:
                print("❌ Capture ID non trouvé")
                return False
        else:
            print("❌ PayPal find_payment a échoué")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    result = asyncio.run(test_simple_refund())
    if result:
        print("\n🎉 LE REMBOURSEMENT FONCTIONNE!")
    else:
        print("\n💥 Échec du remboursement")
