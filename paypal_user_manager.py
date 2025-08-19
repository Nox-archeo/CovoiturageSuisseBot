#!/usr/bin/env python3
"""
Gestionnaire pour s'assurer que TOUS les utilisateurs ont une adresse PayPal
"""

import logging
from database.models import User
from database import get_db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

async def ensure_user_has_paypal_email(user_id: int, bot, context) -> bool:
    """
    S'assure qu'un utilisateur a une adresse PayPal configurée
    Demande l'adresse si elle manque
    
    Returns:
        True si l'utilisateur a une adresse PayPal
    """
    try:
        db = get_db()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False
        
        # Vérifier si l'utilisateur a déjà une adresse PayPal
        if user.paypal_email:
            return True
        
        # Demander l'adresse PayPal
        await request_paypal_email_setup(user, bot)
        return False  # Pas encore configuré
        
    except Exception as e:
        logger.error(f"Erreur ensure_user_has_paypal_email: {e}")
        return False

async def request_paypal_email_setup(user: User, bot):
    """
    Demande à l'utilisateur de configurer son adresse PayPal
    """
    try:
        message = (
            f"🔧 **Configuration requise**\n\n"
            f"Pour profiter pleinement de CovoiturageSuisse, "
            f"vous devez configurer votre adresse email PayPal.\n\n"
            f"📧 **Pourquoi PayPal ?**\n"
            f"• Recevoir des remboursements automatiques\n"
            f"• Recevoir vos gains en tant que conducteur\n"
            f"• Paiements sécurisés et instantanés\n\n"
            f"⚠️ **Important :** Cette adresse doit être associée "
            f"à un compte PayPal actif.\n\n"
            f"Cliquez ci-dessous pour configurer :"
        )
        
        keyboard = [
            [InlineKeyboardButton("📧 Configurer mon PayPal", callback_data="paypal_input_start")],
            [InlineKeyboardButton("ℹ️ Plus d'infos", callback_data="paypal_info")],
            [InlineKeyboardButton("⏭️ Passer pour l'instant", callback_data="paypal_skip")]
        ]
        
        await bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        logger.info(f"Demande de configuration PayPal envoyée à l'utilisateur {user.id}")
        
    except Exception as e:
        logger.error(f"Erreur request_paypal_email_setup: {e}")

async def check_and_request_paypal_before_booking(passenger_id: int, bot) -> bool:
    """
    Vérifie qu'un passager a une adresse PayPal avant de réserver
    Demande l'adresse si elle manque
    
    Returns:
        True si le passager peut procéder à la réservation
    """
    try:
        db = get_db()
        passenger = db.query(User).filter(User.id == passenger_id).first()
        
        if not passenger:
            return False
        
        if passenger.paypal_email:
            return True  # Adresse PayPal déjà configurée
        
        # Demander la configuration PayPal avec contexte de réservation
        message = (
            f"⚠️ **Configuration PayPal requise**\n\n"
            f"Avant de réserver, vous devez configurer votre adresse PayPal.\n\n"
            f"🔄 **Pourquoi maintenant ?**\n"
            f"• Remboursements automatiques si un autre passager s'ajoute\n"
            f"• Remboursements en cas d'annulation\n"
            f"• Traitement rapide et sécurisé\n\n"
            f"📧 Configurez votre PayPal pour continuer :"
        )
        
        keyboard = [
            [InlineKeyboardButton("📧 Configurer maintenant", callback_data="paypal_input_start")],
            [InlineKeyboardButton("❌ Annuler la réservation", callback_data="booking_cancel")]
        ]
        
        await bot.send_message(
            chat_id=passenger.telegram_id,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return False  # Bloquer la réservation jusqu'à configuration
        
    except Exception as e:
        logger.error(f"Erreur check_and_request_paypal_before_booking: {e}")
        return False

async def remind_missing_paypal_emails(bot):
    """
    Rappel périodique aux utilisateurs sans adresse PayPal
    """
    try:
        db = get_db()
        users_without_paypal = db.query(User).filter(
            User.paypal_email.is_(None),
            User.telegram_id.isnot(None)
        ).limit(10).all()  # Limiter pour éviter le spam
        
        for user in users_without_paypal:
            message = (
                f"🔔 **Rappel : Configuration PayPal**\n\n"
                f"Vous n'avez pas encore configuré votre adresse PayPal.\n\n"
                f"⚡ **Avantages :**\n"
                f"• Remboursements automatiques\n"
                f"• Réception des gains\n"
                f"• Expérience complète\n\n"
                f"⏰ Configurez maintenant en quelques secondes :"
            )
            
            keyboard = [
                [InlineKeyboardButton("📧 Configurer PayPal", callback_data="paypal_input_start")],
                [InlineKeyboardButton("🔕 Ne plus me rappeler", callback_data="paypal_reminder_stop")]
            ]
            
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                logger.info(f"Rappel PayPal envoyé à l'utilisateur {user.id}")
                
            except Exception as e:
                logger.error(f"Erreur envoi rappel PayPal à {user.id}: {e}")
        
    except Exception as e:
        logger.error(f"Erreur remind_missing_paypal_emails: {e}")
