#!/usr/bin/env python3
"""
Test le remboursement automatique avec les vraies données de l'utilisateur
"""

import asyncio
import os
import sys
import logging
from unittest.mock import AsyncMock, MagicMock

# Configuration du chemin
sys.path.append('/Users/margaux/CovoiturageSuisse')

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_refund():
    """Test le remboursement avec les vraies données utilisateur"""
    try:
        # Import des modules
        from passenger_refund_manager import process_passenger_refund
        from database.db_manager import db_session
        from database.models import Booking, User
        
        # Vérifier si la réservation existe d'abord
        db = db_session()
        booking = db.query(Booking).filter(Booking.id == 23).first()
        if not booking:
            print("❌ Réservation #23 non trouvée dans la base de données")
            return False
        
        passenger = db.query(User).filter(User.id == booking.passenger_id).first()
        if not passenger:
            print("❌ Passager non trouvé")
            return False
        
        print(f"📋 Réservation trouvée:")
        print(f"   ID: {booking.id}")
        print(f"   Status: {booking.status}")
        print(f"   Is_paid: {booking.is_paid}")
        print(f"   Total_price: {booking.total_price}")
        print(f"   PayPal_payment_id: {booking.paypal_payment_id}")
        print(f"   Passenger email: {passenger.paypal_email}")
        db.close()
        
        # Configuration bot mock pour les notifications
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        
        print("\n🔄 Test du remboursement automatique pour la réservation #23...")
        print(f"💳 PayPal Payment ID: {booking.paypal_payment_id}")
        print(f"💰 Montant: {booking.total_price} CHF")
        print(f"📧 Email PayPal: {passenger.paypal_email}")
        
        # Traiter le remboursement
        success = await process_passenger_refund(
            booking_id=23,
            bot=mock_bot
        )
        
        if success:
            print("✅ Remboursement traité avec succès!")
            print("💡 Vérifiez votre compte PayPal pour confirmer le remboursement.")
        else:
            print("❌ Échec du remboursement.")
            print("🔍 Vérifiez les logs pour plus de détails.")
        
        # Vérifier si une notification a été envoyée
        if mock_bot.send_message.called:
            print("📱 Notification envoyée avec succès")
            print(f"📞 Appels de notification: {mock_bot.send_message.call_count}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_real_refund())
    if result:
        print("\n🎉 Test réussi! Le système de remboursement automatique fonctionne.")
    else:
        print("\n💥 Test échoué. Vérifiez les logs d'erreur.")
