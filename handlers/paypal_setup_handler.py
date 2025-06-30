"""
Handler pour la configuration PayPal des conducteurs
Gère l'enregistrement et la validation des comptes PayPal
"""

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackContext, 
    ConversationHandler, 
    CommandHandler,
    MessageHandler, 
    CallbackQueryHandler,
    filters
)
from database import get_db
from database.models import User

logger = logging.getLogger(__name__)

# États de conversation
WAITING_PAYPAL_EMAIL, CONFIRMING_EMAIL = range(2)

async def request_paypal_email(update: Update, context: CallbackContext):
    """Demande l'email PayPal du conducteur"""
    user_id = update.effective_user.id
    
    # Vérifier si c'est un callback ou un message direct
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        send_message = query.edit_message_text
    else:
        send_message = update.message.reply_text
    
    await send_message(
        "💳 *Configuration de votre compte PayPal*\n\n"
        "Pour recevoir vos paiements de covoiturage, nous avons besoin "
        "de votre adresse email PayPal.\n\n"
        "⚠️ *Important :*\n"
        "• Cette adresse doit être associée à un compte PayPal actif\n"
        "• Elle sera utilisée pour tous vos paiements automatiques\n"
        "• Vous pouvez la modifier plus tard avec /paypal\n\n"
        "📧 Veuillez saisir votre adresse email PayPal :",
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WAITING_PAYPAL_EMAIL

async def handle_paypal_email_input(update: Update, context: CallbackContext):
    """Traite l'email PayPal saisi par l'utilisateur"""
    email = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Validation de base de l'email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        await update.message.reply_text(
            "❌ *Adresse email invalide*\n\n"
            "Veuillez saisir une adresse email valide.\n"
            "Exemple: votrenom@gmail.com",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_PAYPAL_EMAIL
    
    # Stocker temporairement l'email pour confirmation
    context.user_data['temp_paypal_email'] = email
    
    # Demander confirmation
    keyboard = [
        [InlineKeyboardButton("✅ Confirmer", callback_data="confirm_paypal_email")],
        [InlineKeyboardButton("✏️ Modifier", callback_data="edit_paypal_email")],
        [InlineKeyboardButton("❌ Annuler", callback_data="cancel_paypal_setup")]
    ]
    
    await update.message.reply_text(
        f"📧 *Confirmation de votre email PayPal*\n\n"
        f"Email saisi : `{email}`\n\n"
        f"⚠️ Vérifiez bien cette adresse car elle sera utilisée "
        f"pour recevoir vos paiements automatiques.\n\n"
        f"Confirmez-vous cette adresse ?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CONFIRMING_EMAIL

async def handle_paypal_confirmation(update: Update, context: CallbackContext):
    """Gère la confirmation de l'email PayPal"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    user_id = update.effective_user.id
    
    if action == "confirm_paypal_email":
        # Sauvegarder l'email en base
        email = context.user_data.get('temp_paypal_email')
        if not email:
            await query.edit_message_text(
                "❌ Erreur : Email non trouvé. Veuillez recommencer."
            )
            return ConversationHandler.END
        
        try:
            db = get_db()
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user:
                await query.edit_message_text(
                    "❌ Utilisateur non trouvé. Veuillez d'abord utiliser /start"
                )
                return ConversationHandler.END
            
            # Sauvegarder l'email PayPal
            user.paypal_email = email
            db.commit()
            
            await query.edit_message_text(
                f"✅ *Email PayPal enregistré avec succès !*\n\n"
                f"📧 Email : `{email}`\n\n"
                f"🎉 Vous pouvez maintenant recevoir des paiements automatiques "
                f"pour vos trajets en tant que conducteur.\n\n"
                f"💡 Pour modifier cet email plus tard, utilisez la commande /paypal",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Nettoyer les données temporaires
            context.user_data.pop('temp_paypal_email', None)
            
            logger.info(f"Email PayPal enregistré pour l'utilisateur {user_id}: {email}")
            
            # Retourner l'état suivant si on est dans un flux de création de trajet
            next_state = context.user_data.get('next_state_after_paypal')
            if next_state:
                context.user_data.pop('next_state_after_paypal', None)
                return next_state
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'email PayPal : {e}")
            await query.edit_message_text(
                "❌ Erreur lors de l'enregistrement. Veuillez réessayer plus tard."
            )
            return ConversationHandler.END
    
    elif action == "edit_paypal_email":
        # Retour à la saisie
        await query.edit_message_text(
            "✏️ *Modification de l'email PayPal*\n\n"
            "Veuillez saisir votre nouvelle adresse email PayPal :",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_PAYPAL_EMAIL
    
    elif action == "cancel_paypal_setup":
        # Annulation
        await query.edit_message_text(
            "❌ Configuration PayPal annulée."
        )
        context.user_data.pop('temp_paypal_email', None)
        return ConversationHandler.END

async def cancel_paypal_setup(update: Update, context: CallbackContext):
    """Annule la configuration PayPal"""
    await update.message.reply_text("❌ Configuration PayPal annulée.")
    context.user_data.pop('temp_paypal_email', None)
    return ConversationHandler.END

async def check_paypal_command(update: Update, context: CallbackContext):
    """Commande /paypal pour vérifier ou modifier l'email PayPal"""
    user_id = update.effective_user.id
    
    try:
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await update.message.reply_text(
                "❌ Utilisateur non trouvé. Veuillez d'abord utiliser /start"
            )
            return
        
        if user.paypal_email:
            # L'utilisateur a déjà un email PayPal
            keyboard = [
                [InlineKeyboardButton("✏️ Modifier", callback_data="modify_paypal_email")],
                [InlineKeyboardButton("❌ Supprimer", callback_data="remove_paypal_email")]
            ]
            
            await update.message.reply_text(
                f"💳 *Votre compte PayPal*\n\n"
                f"📧 Email actuel : `{user.paypal_email}`\n\n"
                f"Ce compte est utilisé pour recevoir vos paiements automatiques.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Pas d'email PayPal configuré
            keyboard = [
                [InlineKeyboardButton("➕ Ajouter un email PayPal", callback_data="add_paypal_email")]
            ]
            
            await update.message.reply_text(
                "💳 *Configuration PayPal*\n\n"
                "❌ Aucun email PayPal configuré.\n\n"
                "Pour recevoir des paiements automatiques en tant que conducteur, "
                "vous devez configurer votre email PayPal.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification PayPal : {e}")
        await update.message.reply_text(
            "❌ Erreur lors de la vérification. Veuillez réessayer plus tard."
        )

async def handle_paypal_management(update: Update, context: CallbackContext):
    """Gère les actions de gestion du compte PayPal"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "add_paypal_email" or action == "modify_paypal_email":
        # Démarrer la configuration PayPal
        await request_paypal_email(update, context)
        return WAITING_PAYPAL_EMAIL
    
    elif action == "remove_paypal_email":
        # Demander confirmation de suppression
        keyboard = [
            [InlineKeyboardButton("✅ Confirmer la suppression", callback_data="confirm_remove_paypal")],
            [InlineKeyboardButton("❌ Annuler", callback_data="cancel_remove_paypal")]
        ]
        
        await query.edit_message_text(
            "⚠️ *Suppression du compte PayPal*\n\n"
            "Êtes-vous sûr de vouloir supprimer votre email PayPal ?\n\n"
            "❌ Vous ne pourrez plus recevoir de paiements automatiques "
            "jusqu'à ce que vous en configuriez un nouveau.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif action == "confirm_remove_paypal":
        # Supprimer l'email PayPal
        user_id = update.effective_user.id
        
        try:
            db = get_db()
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if user:
                user.paypal_email = None
                db.commit()
                
                await query.edit_message_text(
                    "✅ *Email PayPal supprimé*\n\n"
                    "Votre email PayPal a été supprimé de votre profil.\n\n"
                    "⚠️ Vous ne recevrez plus de paiements automatiques "
                    "jusqu'à ce que vous en configuriez un nouveau avec /paypal",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                logger.info(f"Email PayPal supprimé pour l'utilisateur {user_id}")
            else:
                await query.edit_message_text("❌ Utilisateur non trouvé.")
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression PayPal : {e}")
            await query.edit_message_text(
                "❌ Erreur lors de la suppression. Veuillez réessayer plus tard."
            )
    
    elif action == "cancel_remove_paypal":
        # Annuler la suppression
        await query.edit_message_text(
            "❌ Suppression annulée. Votre email PayPal a été conservé."
        )
    
    return ConversationHandler.END

# Gestionnaire de conversation pour la configuration PayPal
paypal_setup_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('paypal', check_paypal_command),
        CallbackQueryHandler(handle_paypal_management, pattern=r'^(add_paypal_email|modify_paypal_email)$'),
        CallbackQueryHandler(request_paypal_email, pattern=r'^setup_paypal$')
    ],
    states={
        WAITING_PAYPAL_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_paypal_email_input),
            CallbackQueryHandler(handle_paypal_management, pattern=r'^(add_paypal_email|modify_paypal_email)$')
        ],
        CONFIRMING_EMAIL: [
            CallbackQueryHandler(handle_paypal_confirmation, pattern=r'^(confirm_paypal_email|edit_paypal_email|cancel_paypal_setup)$')
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel_paypal_setup),
        CommandHandler('annuler', cancel_paypal_setup),
        CallbackQueryHandler(handle_paypal_management, pattern=r'^(remove_paypal_email|confirm_remove_paypal|cancel_remove_paypal)$')
    ],
    allow_reentry=True
)

def get_paypal_setup_handlers():
    """Retourne les handlers de configuration PayPal"""
    return {
        'conversation_handler': paypal_setup_conv_handler,
        'command_handlers': [
            CommandHandler('paypal', check_paypal_command)
        ],
        'callback_handlers': [
            CallbackQueryHandler(handle_paypal_management, pattern=r'^(remove_paypal_email|confirm_remove_paypal|cancel_remove_paypal)$')
        ]
    }

if __name__ == "__main__":
    print("✅ Handler de configuration PayPal créé")
    print("Commandes disponibles :")
    print("  /paypal - Gérer son compte PayPal")
    print("Callbacks disponibles :")
    print("  setup_paypal - Démarrer la configuration PayPal")
