#!/usr/bin/env python3
"""
Système de communication post-réservation
Ajoute des boutons d'interaction après qu'une réservation soit payée
"""

import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Booking, Trip, User
from database import get_db
import logging

logger = logging.getLogger(__name__)

async def add_post_booking_communication(booking_id: int, bot):
    """
    Ajoute des boutons de communication après une réservation payée
    
    Args:
        booking_id: ID de la réservation
        bot: Instance du bot Telegram
    """
    try:
        db = get_db()
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking:
            logger.error(f"Réservation {booking_id} non trouvée")
            return
        
        trip = booking.trip
        passenger = booking.passenger
        driver = trip.driver
        
        # Boutons pour le passager
        if passenger and passenger.telegram_id:
            passenger_keyboard = [
                [InlineKeyboardButton("💬 Contacter le conducteur", callback_data=f"contact_driver:{trip.id}")],
                [InlineKeyboardButton("📍 Point de rendez-vous", callback_data=f"meeting_point:{trip.id}")],
                [InlineKeyboardButton("❌ Annuler avec remboursement", callback_data=f"cancel_booking:{booking_id}")],
                [InlineKeyboardButton("ℹ️ Détails du trajet", callback_data=f"trip_details:{trip.id}")]
            ]
            
            driver_contact = ""
            if driver:
                # Afficher le nom complet et les contacts
                driver_name = driver.full_name or driver.username or f"Conducteur #{driver.id}"
                contact_info = []
                
                if driver.username:
                    contact_info.append(f"@{driver.username}")
                if driver.phone:
                    contact_info.append(f"📞 {driver.phone}")
                
                if contact_info:
                    driver_contact = f"👤 **Conducteur:** {driver_name}\n📱 **Contact:** {' | '.join(contact_info)}\n"
                else:
                    driver_contact = f"👤 **Conducteur:** {driver_name}\n📱 **Contact:** Via boutons ci-dessous\n"
            
            passenger_message = (
                f"🎉 **Réservation confirmée #{booking_id}**\n\n"
                f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                f"💰 **Montant payé:** {booking.total_price:.2f} CHF\n\n"
                f"{driver_contact}\n"
                f"🔽 **Actions disponibles:**"
            )
            
            await bot.send_message(
                chat_id=passenger.telegram_id,
                text=passenger_message,
                reply_markup=InlineKeyboardMarkup(passenger_keyboard),
                parse_mode='Markdown'
            )
        
        # Boutons pour le conducteur
        if driver and driver.telegram_id:
            driver_keyboard = [
                [InlineKeyboardButton("💬 Contacter le passager", callback_data=f"contact_passenger:{booking_id}")],
                [InlineKeyboardButton("📍 Définir point de RDV", callback_data=f"set_meeting_point:{trip.id}")],
                [InlineKeyboardButton("👥 Voir tous les passagers", callback_data=f"view_passengers:{trip.id}")],
                [InlineKeyboardButton("ℹ️ Détails du trajet", callback_data=f"trip_details:{trip.id}")]
            ]
            
            passenger_contact = ""
            if passenger:
                # Afficher le nom complet et les contacts
                passenger_name = passenger.full_name or passenger.username or f"Passager #{passenger.id}"
                contact_info = []
                
                if passenger.username:
                    contact_info.append(f"@{passenger.username}")
                if passenger.phone:
                    contact_info.append(f"📞 {passenger.phone}")
                
                if contact_info:
                    passenger_contact = f"👤 **Passager:** {passenger_name}\n📱 **Contact:** {' | '.join(contact_info)}\n"
                else:
                    passenger_contact = f"👤 **Passager:** {passenger_name}\n📱 **Contact:** Via boutons ci-dessous\n"
            
            # Compter le total de passagers payants
            total_paid_passengers = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.payment_status == 'completed'
            ).count()
            
            driver_message = (
                f"🎉 **Nouveau passager #{booking_id}**\n\n"
                f"📍 **Trajet:** {trip.departure_city} → {trip.arrival_city}\n"
                f"📅 **Date:** {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n"
                f"👥 **Total passagers:** {total_paid_passengers}\n"
                f"💰 **Prix payé:** {booking.total_price:.2f} CHF\n\n"
                f"{passenger_contact}\n"
                f"🔽 **Actions disponibles:**"
            )
            
            await bot.send_message(
                chat_id=driver.telegram_id,
                text=driver_message,
                reply_markup=InlineKeyboardMarkup(driver_keyboard),
                parse_mode='Markdown'
            )
        
        logger.info(f"✅ Boutons de communication ajoutés pour la réservation {booking_id}")
        
    except Exception as e:
        logger.error(f"❌ Erreur ajout boutons communication: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test de la fonction
    import asyncio
    from unittest.mock import AsyncMock
    
    async def test():
        mock_bot = AsyncMock()
        await add_post_booking_communication(28, mock_bot)
        print("Test terminé")
    
    asyncio.run(test())
