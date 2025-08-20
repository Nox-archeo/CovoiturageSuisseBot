#!/usr/bin/env python3
"""
Script pour envoyer manuellement les boutons de communication à l'utilisateur réel
Utilise le vrai bot Telegram et les vraies données
"""

import asyncio
import sys
import os
import logging

# Configuration du chemin
sys.path.append('/Users/margaux/CovoiturageSuisse')

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_real_communication_buttons():
    """Envoie les vrais boutons de communication à l'utilisateur"""
    try:
        from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
        
        # Configuration du bot
        BOT_TOKEN = os.getenv('BOT_TOKEN') or "7773059520:AAFz06Ak-2vFUCsaMD-y9dT5mQkRU7HInKs"
        bot = Bot(token=BOT_TOKEN)
        
        # ID Telegram de l'utilisateur (Margaux)
        user_telegram_id = 5932296330
        
        print("🔄 Envoi des boutons de communication à l'utilisateur...")
        
        # Boutons pour le passager (vous)
        passenger_keyboard = [
            [InlineKeyboardButton("💬 Contacter le conducteur", callback_data="contact_driver:8")],
            [InlineKeyboardButton("📍 Point de rendez-vous", callback_data="meeting_point:8")],
            [InlineKeyboardButton("❌ Annuler avec remboursement", callback_data="cancel_booking:28")],
            [InlineKeyboardButton("ℹ️ Détails du trajet", callback_data="trip_details:8")]
        ]
        
        passenger_message = (
            f"🎉 **Réservation confirmée #28**\n\n"
            f"📍 **Trajet:** Corpataux-Magnedens → Posieux\n"
            f"📅 **Date:** 21/08/2025 à 14:00\n"
            f"💰 **Montant payé:** 1.0 CHF\n\n"
            f"👤 **Conducteur:** Contact disponible via les boutons\n\n"
            f"🔽 **Actions disponibles:**"
        )
        
        # Envoyer le message avec les boutons
        await bot.send_message(
            chat_id=user_telegram_id,
            text=passenger_message,
            reply_markup=InlineKeyboardMarkup(passenger_keyboard),
            parse_mode='Markdown'
        )
        
        print("✅ Boutons envoyés avec succès!")
        print(f"📱 Message envoyé à: {user_telegram_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(send_real_communication_buttons())
    if success:
        print("\n🎉 Boutons envoyés!")
        print("📱 Vérifiez votre bot Telegram pour voir les boutons de communication.")
        print("💡 Vous pouvez maintenant tester l'annulation avec remboursement.")
    else:
        print("\n💥 Échec de l'envoi.")
