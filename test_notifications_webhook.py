#!/usr/bin/env python3
"""
Test des notifications webhook PayPal
Simule un paiement complété pour tester les notifications
"""

import asyncio
import logging
import os
from database.models import Booking, Trip, User
from database import get_db
from webhook_bot import handle_payment_completed
from telegram import Bot

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_notifications():
    """Test des notifications de paiement"""
    
    print("🧪 TEST DES NOTIFICATIONS WEBHOOK")
    print("=" * 50)
    
    # 1. Trouver une réservation récente
    db = get_db()
    
    recent_booking = db.query(Booking).order_by(Booking.id.desc()).first()
    
    if not recent_booking:
        print("❌ Aucune réservation trouvée")
        return
    
    print(f"🔍 Réservation trouvée: ID {recent_booking.id}")
    print(f"   Status: {recent_booking.payment_status}")
    print(f"   Trip ID: {recent_booking.trip_id}")
    print(f"   PayPal ID: {recent_booking.paypal_payment_id}")
    
    # 2. Récupérer les infos du trajet
    trip = recent_booking.trip
    passenger = recent_booking.passenger
    driver = trip.driver if trip else None
    
    print(f"\n📊 INFOS TRAJET:")
    print(f"   Trajet: {trip.departure_city} → {trip.arrival_city}" if trip else "   Trajet: Inconnu")
    print(f"   Passager ID: {passenger.telegram_id}" if passenger else "   Passager: Inconnu")
    print(f"   Conducteur ID: {driver.telegram_id}" if driver else "   Conducteur: Inconnu")
    
    # 3. Test direct de l'envoi de message
    try:
        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN manquant")
            return
        
        bot = Bot(token=BOT_TOKEN)
        
        # Test message au passager
        if passenger and passenger.telegram_id:
            print(f"\n📤 Test notification passager...")
            try:
                await bot.send_message(
                    chat_id=passenger.telegram_id,
                    text="🧪 **Test notification passager**\n\nCeci est un test des notifications de paiement.",
                    parse_mode="Markdown"
                )
                print("   ✅ Notification passager envoyée")
            except Exception as e:
                print(f"   ❌ Erreur notification passager: {e}")
        
        # Test message au conducteur
        if driver and driver.telegram_id:
            print(f"\n📤 Test notification conducteur...")
            try:
                await bot.send_message(
                    chat_id=driver.telegram_id,
                    text="🧪 **Test notification conducteur**\n\nCeci est un test des notifications de paiement.",
                    parse_mode="Markdown"
                )
                print("   ✅ Notification conducteur envoyée")
            except Exception as e:
                print(f"   ❌ Erreur notification conducteur: {e}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test Bot: {e}")
    
    # 4. Test du webhook avec données simulées
    print(f"\n🎯 Test webhook handle_payment_completed...")
    
    # Simuler des données PayPal
    test_data = {
        'resource': {
            'id': recent_booking.paypal_payment_id or 'test_payment_id',
            'custom_id': str(recent_booking.id),
            'amount': {
                'value': str(recent_booking.total_price or 10.0)
            }
        }
    }
    
    try:
        # Appeler directement la fonction webhook
        await handle_payment_completed(test_data)
        print("   ✅ Fonction webhook exécutée sans erreur")
    except Exception as e:
        print(f"   ❌ Erreur fonction webhook: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
    print(f"\n🎯 Test terminé")

if __name__ == "__main__":
    asyncio.run(test_notifications())
