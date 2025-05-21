from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
import sys
import os
import logging

# Ajout du chemin parent au chemin d'importation Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))
from database.models import User
from database import get_db

# États de conversation
CHOOSING, TYPING_PHONE = range(2)  # Simplification des états

async def profile_menu(update: Update, context):
    """Menu principal du profil"""
    try:
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter_by(telegram_id=user_id).first()
        
        if not user:
            user = User(telegram_id=user_id, username=update.effective_user.username)
            db.add(user)
            db.commit()

        keyboard = [
            [
                InlineKeyboardButton("🚗 Mode Conducteur", callback_data="driver"),
                InlineKeyboardButton("🧍 Mode Passager", callback_data="passenger")
            ],
            [InlineKeyboardButton("📱 Ajouter téléphone", callback_data="phone")],
            [InlineKeyboardButton("🔙 Menu principal", callback_data="menu")]
        ]

        text = (
            f"👤 Profil de {update.effective_user.first_name}\n\n"
            f"📱 Téléphone: {user.phone or 'Non renseigné'}\n"
            f"Mode: {'Conducteur' if user.is_driver else 'Passager' if user.is_passenger else 'Non défini'}"
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return CHOOSING

    except Exception as e:
        print(f"Error in profile_menu: {str(e)}")
        return ConversationHandler.END

async def handle_button(update: Update, context):
    """Gère les clics sur les boutons"""
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    try:
        db = get_db()
        user = db.query(User).filter_by(telegram_id=query.from_user.id).first()

        if choice == "driver":
            user.is_driver = True
            db.commit()
            await query.edit_message_text("✅ Mode conducteur activé!")
            return CHOOSING

        elif choice == "passenger":
            user.is_passenger = True
            db.commit()
            await query.edit_message_text("✅ Mode passager activé!")
            return CHOOSING

        elif choice == "phone":
            await query.edit_message_text(
                "📱 Veuillez entrer votre numéro de téléphone\n"
                "Format: +41 XX XXX XX XX ou 07X XXX XX XX"
            )
            return TYPING_PHONE

        elif choice == "menu":
            return await profile_menu(update, context)

    except Exception as e:
        print(f"Error: {str(e)}")
        await query.edit_message_text("Une erreur est survenue.")
        return ConversationHandler.END

async def handle_phone_input(update: Update, context):
    """Traite l'entrée du numéro de téléphone"""
    if not update.message:
        return TYPING_PHONE

    phone = update.message.text.strip()
    
    # Nettoyage du numéro
    phone = phone.replace(" ", "")
    if phone.startswith("0"):
        phone = "+41" + phone[1:]
    
    # Validation du format
    if not (phone.startswith('+41') and len(phone) == 12 and phone[1:].isdigit()):
        await update.message.reply_text(
            "❌ Format invalide. Veuillez utiliser:\n"
            "+41 XX XXX XX XX ou\n"
            "07X XXX XX XX"
        )
        return TYPING_PHONE

    try:
        db = get_db()
        user = db.query(User).filter_by(telegram_id=update.effective_user.id).first()
        user.phone = phone
        db.commit()
        
        # Retour au menu profil avec confirmation
        await update.message.reply_text("✅ Numéro de téléphone enregistré!")
        return await profile_menu(update, context)
        
    except Exception as e:
        print(f"Error saving phone: {str(e)}")
        await update.message.reply_text("Une erreur est survenue.")
        return TYPING_PHONE

def get_user_mode(user):
    """Retourne le mode actuel de l'utilisateur"""
    if user.is_driver and user.is_passenger:
        return "Conducteur et Passager"
    elif user.is_driver:
        return "Conducteur"
    elif user.is_passenger:
        return "Passager"
    return "Non défini"

def register(application):
    """Enregistre les handlers"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('profil', profile_menu)],
        states={
            CHOOSING: [
                CallbackQueryHandler(handle_button)
            ],
            TYPING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input),
                CallbackQueryHandler(profile_menu, pattern='^back_to_profile$')
            ]
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
