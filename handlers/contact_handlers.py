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
    
    # Extrait l'ID du conducteur selon le format du callback_data
    if query.data.startswith("contact_driver_"):
        driver_id_str = query.data.replace("contact_driver_", "")
        driver_id = int(driver_id_str)
    else:
        logger.error(f"Format de callback_data non reconnu: {query.data}")
        await query.edit_message_text("❌ Format de demande non reconnu.")
        return ConversationHandler.END
    
    context.user_data['contact_driver_id'] = driver_id
    
    db = get_db()
    driver = db.query(User).get(driver_id)
    
    if not driver:
        await query.edit_message_text("❌ Conducteur non trouvé.")
        return ConversationHandler.END
    
    # Sauvegarde l'ID du destinataire pour la conversation
    context.user_data['recipient_id'] = driver.id
    
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel_contact")]]
    
    await query.edit_message_text(
        f"📱 Vous allez envoyer un message à {driver.username or 'le conducteur'}\n\n"
        "Veuillez saisir votre message:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return TYPING_MESSAGE

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
    """Démarre une conversation avec le conducteur"""
    query = update.callback_query
    await query.answer()
    
    # Extrait l'ID du conducteur selon le format du callback_data
    if query.data.startswith("contact_driver_"):
        driver_id_str = query.data.replace("contact_driver_", "")
        driver_id = int(driver_id_str)
    else:
        logger.error(f"Format de callback_data non reconnu: {query.data}")
        await query.edit_message_text("❌ Format de demande non reconnu.")
        return ConversationHandler.END
    
    context.user_data['contact_driver_id'] = driver_id
    
    db = get_db()
    driver = db.query(User).get(driver_id)
    
    if not driver:
        await query.edit_message_text("❌ Conducteur non trouvé.")
        return ConversationHandler.END
    
    # Sauvegarde l'ID du destinataire pour la conversation
    context.user_data['recipient_id'] = driver.id
    
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel_contact")]]
    
    await query.edit_message_text(
        f"📱 Vous allez envoyer un message à {driver.username or 'le conducteur'}\n\n"
        "Veuillez saisir votre message:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return TYPING_MESSAGE

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
