#!/usr/bin/env python3
"""
Test simple des notifications sans webhook_bot
"""

import asyncio
import logging
import os
from database.models import Booking, Trip, User
from database import get_db
from telegram import Bot

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_notifications():
    """Test simple des notifications"""
    
    print("🧪 TEST SIMPLE DES NOTIFICATIONS")
    print("=" * 40)
    
    # 1. Configuration bot
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN manquant dans .env")
        return
    
    # 2. Charger .env
    from dotenv import load_dotenv
    load_dotenv()
    
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    print(f"🔑 Token chargé: {BOT_TOKEN[:20]}...")
    
    bot = Bot(token=BOT_TOKEN)
    
    # 3. Trouver la dernière réservation (pas la #18 qui n'existe que sur Render)
    db = get_db()
    
    booking = db.query(Booking).order_by(Booking.id.desc()).first()
    
    if not booking:
        print("❌ Aucune réservation trouvée")
        return
    
    print(f"✅ Réservation #{booking.id} trouvée")
    print(f"   Status: {booking.payment_status}")
    print(f"   Trip ID: {booking.trip_id}")
    print(f"   Total price: {booking.total_price}")
    
    # 4. Récupérer les infos
    trip = booking.trip
    passenger = booking.passenger
    driver = trip.driver if trip else None
    
    print(f"\\n📊 DÉTAILS:")
    print(f"   Trajet: {trip.departure_city} → {trip.arrival_city}" if trip else "   Trajet: Inconnu")
    print(f"   Passager: {passenger.username} (ID: {passenger.telegram_id})" if passenger else "   Passager: Inconnu")
    print(f"   Conducteur: {driver.username} (ID: {driver.telegram_id})" if driver else "   Conducteur: Inconnu")
    
    # 5. Test notifications (avec vos vrais IDs)
    print(f"\\n📤 ENVOI NOTIFICATIONS...")
    
    # IMPORTANT: Utiliser votre vrai Telegram ID pour tester
    YOUR_TELEGRAM_ID = 5932296330  # Remplacez par votre ID
    
    # Test notification type passager (à votre ID)
    try:
        message = (
            f"✅ *TEST NOTIFICATION PASSAGER*\\n\\n"
            f"Votre réservation pour le trajet {trip.departure_city} → {trip.arrival_city} "
            f"le {trip.departure_time.strftime('%d/%m/%Y à %H:%M')} est confirmée.\\n\\n"
            f"💰 Montant payé: {booking.total_price:.2f} CHF\\n\\n"
            f"🧪 Ceci est un test des notifications de paiement."
        )
        
        await bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=message,
            parse_mode="Markdown"
        )
        print(f"   ✅ Notification PASSAGER envoyée à votre ID: {YOUR_TELEGRAM_ID}")
    except Exception as e:
        print(f"   ❌ Erreur notification passager: {e}")
    
    # Test notification type conducteur (à votre ID aussi)
    try:
        message = (
            f"💰 *TEST NOTIFICATION CONDUCTEUR*\n\n"
            f"Un passager a payé pour votre trajet {trip.departure_city} → {trip.arrival_city} "
            f"le {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}.\n\n"
            f"👤 Passager: {passenger.username}\n"
            f"💰 Prix payé: {booking.total_price:.2f} CHF\n\n"
            f"🧪 Ceci est un test des notifications de paiement."
        )
        
        await bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=message
        )
        print(f"   ✅ Notification CONDUCTEUR envoyée à votre ID: {YOUR_TELEGRAM_ID}")
    except Exception as e:
        print(f"   ❌ Erreur notification conducteur: {e}")
    
    db.close()
    print(f"\\n🎯 Test terminé")

if __name__ == "__main__":
    asyncio.run(test_simple_notifications())
