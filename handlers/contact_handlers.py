from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CallbackContext, ConversationHandler, MessageHandler, filters
from database.models import User, Message
from database import get_db
import logging

logger = logging.getLogger(__name__)

# États de la conversation
TYPING_MESSAGE = 0

async def initiate_contact(update: Update, context: CallbackContext):
    """Démarre une conversation avec le conducteur"""
    query = update.callback_query
    await query.answer()
    
    # 🚨 SÉCURITÉ: Cette fonction utilise l'ancien format avec driver_id visible
    # Elle ne devrait plus être utilisée - rediriger vers la recherche sécurisée
    await query.edit_message_text(
        "🔒 *Accès sécurisé requis*\n\n"
        "Pour protéger la vie privée des conducteurs, l'accès aux contacts "
        "nécessite maintenant une réservation payée.\n\n"
        "Utilisez la fonction de recherche pour trouver et réserver un trajet.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Rechercher un trajet", callback_data="search_new")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")]
        ]),
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END

async def send_message(update: Update, context: CallbackContext):
    """Envoie le message au conducteur"""
    message_text = update.message.text
    sender_id = update.effective_user.id
    recipient_id = context.user_data.get('recipient_id')
    
    if not recipient_id:
        await update.message.reply_text("❌ Erreur: destinataire non défini.")
        return ConversationHandler.END
    
    db = get_db()
    recipient = db.query(User).get(recipient_id)
    
    if not recipient:
        await update.message.reply_text("❌ Destinataire non trouvé.")
        return ConversationHandler.END
    
    # Enregistrer le message dans la base de données
    message = Message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=message_text
    )
    db.add(message)
    db.commit()
    
    # Envoyer le message au conducteur
    keyboard = [[InlineKeyboardButton("📱 Répondre", callback_data=f"reply_{sender_id}")]]
    try:
        await context.bot.send_message(
            chat_id=recipient.telegram_id,
            text=f"📨 Nouveau message de {update.effective_user.first_name}:\n\n{message_text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Confirmation à l'expéditeur
        await update.message.reply_text(
            "✅ Message envoyé au conducteur!"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message: {str(e)}")
        await update.message.reply_text("❌ Erreur lors de l'envoi du message. Veuillez réessayer plus tard.")
    
    return ConversationHandler.END

async def cancel_contact(update: Update, context: CallbackContext):
    """Annule l'envoi du message"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Envoi du message annulé.")
    return ConversationHandler.END

def register(application):
    """Enregistre les handlers de contact"""
    # Handler pour le bouton "Contacter le conducteur"
    contact_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(initiate_contact, pattern="^contact_driver_")
        ],
        states={
            TYPING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_message),
                CallbackQueryHandler(cancel_contact, pattern="^cancel_contact$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_contact, pattern="^cancel_contact$")
        ],
        per_message=True
    )
    
    application.add_handler(contact_conv_handler)
    
    # Ajouter un handler de réponse également
    application.add_handler(
        CallbackQueryHandler(
            lambda u, c: u.callback_query.answer("Fonctionnalité de réponse en développement"),
            pattern="^reply_"
        )
    )
    
    logger.info("Contact handlers registered.")

async def initiate_contact(update: Update, context: CallbackContext):
    """Démarre une conversation avec le conducteur - VERSION DÉPRÉCIÉE"""
    query = update.callback_query
    await query.answer()
    
    # 🚨 SÉCURITÉ: Cette fonction utilise l'ancien format avec driver_id visible
    # Elle ne devrait plus être utilisée - rediriger vers la recherche sécurisée
    await query.edit_message_text(
        "🔒 *Accès sécurisé requis*\n\n"
        "Pour protéger la vie privée des conducteurs, l'accès aux contacts "
        "nécessite maintenant une réservation payée.\n\n"
        "Utilisez la fonction de recherche pour trouver et réserver un trajet.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Rechercher un trajet", callback_data="search_new")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")]
        ]),
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END

async def send_message(update: Update, context: CallbackContext):
    """Envoie le message au conducteur"""
    message_text = update.message.text
    sender_id = update.effective_user.id
    recipient_id = context.user_data.get('recipient_id')
    
    if not recipient_id:
        await update.message.reply_text("❌ Erreur: destinataire non défini.")
        return ConversationHandler.END
    
    db = get_db()
    recipient = db.query(User).get(recipient_id)
    
    if not recipient:
        await update.message.reply_text("❌ Destinataire non trouvé.")
        return ConversationHandler.END
    
    # Enregistrer le message dans la base de données
    message = Message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=message_text
    )
    db.add(message)
    db.commit()
    
    # Envoyer le message au conducteur
    keyboard = [[InlineKeyboardButton("📱 Répondre", callback_data=f"reply_{sender_id}")]]
    try:
        await context.bot.send_message(
            chat_id=recipient.telegram_id,
            text=f"📨 Nouveau message de {update.effective_user.first_name}:\n\n{message_text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Confirmation à l'expéditeur
        await update.message.reply_text(
            "✅ Message envoyé au conducteur!"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message: {str(e)}")
        await update.message.reply_text("❌ Erreur lors de l'envoi du message. Veuillez réessayer plus tard.")
    
    return ConversationHandler.END

async def cancel_contact(update: Update, context: CallbackContext):
    """Annule l'envoi du message"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Envoi du message annulé.")
    return ConversationHandler.END

def register(application):
    """Enregistre les handlers de contact"""
    # Handler pour le bouton "Contacter le conducteur"
    contact_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(initiate_contact, pattern="^contact_driver_")
        ],
        states={
            TYPING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_message),
                CallbackQueryHandler(cancel_contact, pattern="^cancel_contact$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_contact, pattern="^cancel_contact$")
        ]
    )
    
    application.add_handler(contact_conv_handler)
    
    # Ajouter un handler de réponse également
    application.add_handler(
        CallbackQueryHandler(
            lambda u, c: u.callback_query.answer("Fonctionnalité de réponse en développement"),
            pattern="^reply_"
        )
    )
    
    logger.info("Contact handlers registered.")
