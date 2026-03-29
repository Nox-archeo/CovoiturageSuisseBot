#!/usr/bin/env python3
"""
Test système de messagerie - Diagnostic complet
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

async def test_message_system():
    """Test complet du système de messagerie"""
    try:
        from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
        from database.db_manager import get_db
        from database.models import Trip, User, Booking
        
        # Configuration du bot
        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not BOT_TOKEN:
            print("❌ Token bot non trouvé")
            return False
        
        bot = Bot(token=BOT_TOKEN)
        print(f"✅ Bot configuré: {BOT_TOKEN[:10]}...")
        
        # Test connexion base de données
        db = get_db()
        
        # Récupérer vos données (Margaux)
        user_telegram_id = 5932296330
        user = db.query(User).filter(User.telegram_id == user_telegram_id).first()
        if not user:
            print("❌ Utilisateur non trouvé")
            return False
        
        print(f"✅ Utilisateur trouvé: {user.full_name or user.username}")
        
        # Récupérer le trajet 8 (Corpataux → Posieux)
        trip = db.query(Trip).filter(Trip.id == 8).first()
        if not trip:
            print("❌ Trajet 8 non trouvé")
            return False
        
        print(f"✅ Trajet trouvé: {trip.departure_city} → {trip.arrival_city}")
        
        # Récupérer le conducteur
        driver = trip.driver
        if not driver:
            print("❌ Conducteur non trouvé")
            return False
        
        print(f"✅ Conducteur trouvé: {driver.full_name or driver.username} (ID: {driver.telegram_id})")
        
        # Test 1: Notification RDV gare
        print("\n🧪 TEST 1: Notification RDV gare au conducteur")
        try:
            rdv_keyboard = [
                [InlineKeyboardButton("✅ Confirmer gare", callback_data=f"confirm_rdv_station:8:{user_telegram_id}")],
                [InlineKeyboardButton("📝 Proposer autre lieu", callback_data=f"suggest_rdv:8:{user_telegram_id}")],
                [InlineKeyboardButton("💬 Contacter passager", callback_data=f"contact_passenger_rdv:8:{user_telegram_id}")]
            ]
            
            await bot.send_message(
                chat_id=driver.telegram_id,
                text=f"📍 **TEST: Point de rendez-vous choisi**\n\n"
                     f"👤 **Passager:** {user.full_name or user.username}\n"
                     f"🚉 **Point de RDV:** Gare de départ\n\n"
                     f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
                     f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                     f"⚠️ **Veuillez confirmer ce lieu de rendez-vous ou proposer une alternative.**\n\n"
                     f"🧪 **CECI EST UN TEST DU SYSTÈME**",
                reply_markup=InlineKeyboardMarkup(rdv_keyboard),
                parse_mode='Markdown'
            )
            print("✅ Notification RDV envoyée au conducteur")
        except Exception as e:
            print(f"❌ Erreur notification RDV: {e}")
        
        # Test 2: Message passager vers conducteur
        print("\n🧪 TEST 2: Message passager vers conducteur")
        try:
            message_keyboard = [
                [InlineKeyboardButton("💬 Répondre", callback_data=f"reply_to_passenger:{user_telegram_id}:8")]
            ]
            
            await bot.send_message(
                chat_id=driver.telegram_id,
                text=f"💬 **TEST: Message de {user.full_name or user.username}**\n\n"
                     f"📍 **Trajet:** Trip #8\n\n"
                     f"💭 \"Salut ! Test du système de messagerie. J'espère que vous recevez bien ce message !\"\n\n"
                     f"👆 Utilisez le bouton ci-dessous pour répondre\n\n"
                     f"🧪 **CECI EST UN TEST DU SYSTÈME**",
                reply_markup=InlineKeyboardMarkup(message_keyboard),
                parse_mode='Markdown'
            )
            print("✅ Message test envoyé au conducteur")
        except Exception as e:
            print(f"❌ Erreur message test: {e}")
        
        # Test 3: Boutons de communication pour passager
        print("\n🧪 TEST 3: Envoi boutons communication au passager")
        try:
            passenger_keyboard = [
                [InlineKeyboardButton("💬 Contacter le conducteur", callback_data="contact_driver:8")],
                [InlineKeyboardButton("📍 Point de rendez-vous", callback_data="meeting_point:8")],
                [InlineKeyboardButton("📋 Détails trajet", callback_data="trip_details:8")]
            ]
            
            await bot.send_message(
                chat_id=user_telegram_id,
                text=f"🧪 **TEST: Boutons de communication**\n\n"
                     f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
                     f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
                     f"Testez les boutons ci-dessous :\n\n"
                     f"🧪 **CECI EST UN TEST DU SYSTÈME**",
                reply_markup=InlineKeyboardMarkup(passenger_keyboard),
                parse_mode='Markdown'
            )
            print("✅ Boutons test envoyés au passager")
        except Exception as e:
            print(f"❌ Erreur boutons test: {e}")
        
        # Résumé
        print("\n📊 RÉSUMÉ DU TEST:")
        print(f"👤 Passager: {user.full_name or user.username} (ID: {user_telegram_id})")
        print(f"🚗 Conducteur: {driver.full_name or driver.username} (ID: {driver.telegram_id})")
        print(f"📍 Trajet: {trip.departure_city} → {trip.arrival_city}")
        print(f"📅 Date: {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}")
        print("\n🎯 Si vous ne recevez pas ces messages, il y a un problème de configuration bot/webhook")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test système: {e}")
        return False

if __name__ == "__main__":
    print("🧪 DÉMARRAGE TEST SYSTÈME DE MESSAGERIE")
    print("=" * 50)
    
    result = asyncio.run(test_message_system())
    
    if result:
        print("\n✅ Test terminé avec succès")
    else:
        print("\n❌ Test échoué")
