#!/usr/bin/env python3
"""
Gestionnaire pour l'entrée et validation des adresses PayPal
"""

import logging
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import User
from database import get_db

logger = logging.getLogger(__name__)

def is_valid_email(email: str) -> bool:
    """
    Valide une adresse email
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

async def handle_paypal_input_start(update, context):
    """
    Démarre le processus d'entrée de l'adresse PayPal
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Définir l'état de l'utilisateur
        context.user_data['awaiting_paypal_email'] = True
        
        message = (
            f"📧 **Configuration PayPal**\n\n"
            f"Entrez votre adresse email PayPal.\n\n"
            f"⚠️ **Important :**\n"
            f"• Cette adresse doit être associée à un compte PayPal actif\n"
            f"• Vérifiez l'orthographe - les erreurs empêchent les paiements\n"
            f"• Utilisez la même adresse que votre compte PayPal\n\n"
            f"📝 Tapez votre adresse email :"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Annuler", callback_data="paypal_input_cancel")]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur handle_paypal_input_start: {e}")

async def handle_paypal_email_input(update, context):
    """
    Traite l'entrée de l'adresse email PayPal
    """
    try:
        # Vérifier si on attend une adresse PayPal
        if not context.user_data.get('awaiting_paypal_email'):
            return
        
        email = update.message.text.strip()
        
        # Valider l'email
        if not is_valid_email(email):
            await update.message.reply_text(
                "❌ **Adresse invalide**\n\n"
                "L'adresse email que vous avez entrée n'est pas valide.\n\n"
                "📝 Veuillez entrer une adresse email valide :",
                parse_mode='Markdown'
            )
            return
        
        # Confirmer l'adresse
        keyboard = [
            [InlineKeyboardButton("✅ Confirmer", callback_data=f"paypal_confirm:{email}")],
            [InlineKeyboardButton("✏️ Modifier", callback_data="paypal_input_start")],
            [InlineKeyboardButton("❌ Annuler", callback_data="paypal_input_cancel")]
        ]
        
        message = (
            f"🔍 **Confirmation PayPal**\n\n"
            f"📧 Adresse saisie :\n"
            f"`{email}`\n\n"
            f"⚠️ **Vérifiez bien :**\n"
            f"• Cette adresse est-elle correcte ?\n"
            f"• Est-elle associée à votre compte PayPal ?\n"
            f"• Pouvez-vous recevoir des paiements dessus ?\n\n"
            f"Confirmez ou modifiez :"
        )
        
        await update.message.reply_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        # Nettoyer l'état
        context.user_data['awaiting_paypal_email'] = False
        
    except Exception as e:
        logger.error(f"Erreur handle_paypal_email_input: {e}")

async def handle_paypal_confirm(update, context):
    """
    Confirme et sauvegarde l'adresse PayPal
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Extraire l'email du callback_data
        email = query.data.split(':', 1)[1]
        
        # Sauvegarder dans la base de données
        db = get_db()
        user = db.query(User).filter(User.telegram_id == query.from_user.id).first()
        
        if not user:
            await query.edit_message_text(
                "❌ Erreur : Utilisateur non trouvé."
            )
            return
        
        # Mettre à jour l'adresse PayPal
        user.paypal_email = email
        db.commit()
        
        message = (
            f"✅ **PayPal configuré avec succès !**\n\n"
            f"📧 Adresse enregistrée :\n"
            f"`{email}`\n\n"
            f"🎉 **Vous pouvez maintenant :**\n"
            f"• Recevoir des remboursements automatiques\n"
            f"• Recevoir vos gains en tant que conducteur\n"
            f"• Profiter pleinement de CovoiturageSuisse\n\n"
            f"💡 Vous pouvez modifier cette adresse à tout moment "
            f"dans votre profil."
        )
        
        keyboard = [
            [InlineKeyboardButton("👤 Voir mon profil", callback_data="profile_view")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        logger.info(f"Adresse PayPal configurée pour utilisateur {user.id}: {email}")
        
    except Exception as e:
        logger.error(f"Erreur handle_paypal_confirm: {e}")

async def handle_paypal_input_cancel(update, context):
    """
    Annule la configuration PayPal
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Nettoyer l'état
        context.user_data.pop('awaiting_paypal_email', None)
        
        message = (
            f"❌ **Configuration annulée**\n\n"
            f"Vous pouvez configurer votre PayPal à tout moment "
            f"depuis votre profil.\n\n"
            f"⚠️ **Note :** Certaines fonctionnalités nécessitent "
            f"une adresse PayPal configurée."
        )
        
        keyboard = [
            [InlineKeyboardButton("👤 Mon profil", callback_data="profile_view")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur handle_paypal_input_cancel: {e}")

async def handle_paypal_info(update, context):
    """
    Affiche des informations sur PayPal
    """
    try:
        query = update.callback_query
        await query.answer()
        
        message = (
            f"ℹ️ **Informations PayPal**\n\n"
            f"🔐 **Sécurité :**\n"
            f"• PayPal est un leader mondial des paiements\n"
            f"• Vos données sont protégées\n"
            f"• Transactions sécurisées et traçables\n\n"
            f"💰 **Remboursements :**\n"
            f"• Automatiques quand nécessaire\n"
            f"• Instantanés vers votre compte\n"
            f"• Aucune commission pour vous\n\n"
            f"👩‍💼 **Gains conducteur :**\n"
            f"• 88% du prix du trajet\n"
            f"• Paiement après confirmation mutuelle\n"
            f"• Versement direct sur votre PayPal\n\n"
            f"❓ **Pas de compte PayPal ?**\n"
            f"Créez-en un gratuitement sur paypal.com"
        )
        
        keyboard = [
            [InlineKeyboardButton("📧 Configurer maintenant", callback_data="paypal_input_start")],
            [InlineKeyboardButton("🔙 Retour", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur handle_paypal_info: {e}")
