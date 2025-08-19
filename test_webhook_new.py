#!/usr/bin/env python3
"""
Test du webhook PayPal avec la nouvelle réservation
"""

import asyncio
import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from paypal_webhook_handler import handle_payment_completion

async def test_new_payment():
    """Test avec la nouvelle réservation"""
    print("🧪 Test webhook avec nouvelle réservation")
    
    # Test avec payment_id de la nouvelle réservation
    print(f"\n🔥 Test traitement paiement: test_payment_new")
    result = await handle_payment_completion("test_payment_new", bot=None)
    print(f"   Résultat: {'✅ Succès' if result else '❌ Échec'}")
    
    # Vérifier l'état après traitement
    import sqlite3
    conn = sqlite3.connect('/Users/margaux/CovoiturageSuisse/covoiturage.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, is_paid, status, payment_status FROM bookings WHERE paypal_payment_id = ?', ("test_payment_new",))
    booking = cursor.fetchone()
    if booking:
        print(f"   État après: ID={booking[0]}, Paid={booking[1]}, Status={booking[2]}, PayStatus={booking[3]}")
    conn.close()

if __name__ == "__main__":
    asyncio.run(test_new_payment())
