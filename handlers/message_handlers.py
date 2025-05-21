from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database.models import Message, User
from database import get_db

async def show_conversations(update: Update, context):
    """Affiche les conversations actives"""
    user_id = update.effective_user.id
    db = get_db()
    
    # Récupérer les conversations uniques
    messages = db.query(Message).filter(
        (Message.sender_id == user_id) | (Message.recipient_id == user_id)
    ).order_by(Message.timestamp.desc()).all()
    
    # Grouper par conversation
    conversations = {}
    for msg in messages:
        other_id = msg.recipient_id if msg.sender_id == user_id else msg.sender_id
        if other_id not in conversations:
            other_user = db.query(User).get(other_id)
            conversations[other_id] = {
                'user': other_user,
                'last_message': msg
            }
    
    # Créer le clavier inline
    keyboard = []
    for conv in conversations.values():
        keyboard.append([
            InlineKeyboardButton(
                f"💬 {conv['user'].username}",
                callback_data=f"chat_{conv['user'].id}"
            )
        ])
    
    await update.message.reply_text(
        "📨 Vos conversations:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def register(application):
    """Enregistre les handlers de messagerie"""
    application.add_handler(CommandHandler("messages", show_conversations))
    
    # Handler pour les callbacks de conversation
    application.add_handler(CallbackQueryHandler(
        lambda u, c: u.callback_query.answer("Fonctionnalité en développement"),
        pattern="^chat_"
    ))
