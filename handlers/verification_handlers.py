from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from database.models import User
from database import get_db
import os

UPLOAD_ID, UPLOAD_SELFIE = range(2)

async def start_verification(update: Update, context):
    """Commence le processus de vérification"""
    await update.message.reply_text(
        "📝 Vérification d'identité\n\n"
        "Pour votre sécurité et celle des autres utilisateurs, "
        "nous devons vérifier votre identité.\n\n"
        "1. Envoyez une photo de votre pièce d'identité\n"
        "2. Envoyez un selfie avec votre pièce d'identité\n\n"
        "Ces informations seront traitées de manière sécurisée."
    )
    return UPLOAD_ID

async def verify_gender(update: Update, context):
    """Vérifie le genre pour l'option Entre femmes"""
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if not user.identity_verified:
        keyboard = [[InlineKeyboardButton("✅ Vérifier mon identité", callback_data="verify_identity")]]
        await update.message.reply_text(
            "Pour utiliser l'option 'Entre femmes', nous devons vérifier votre identité.\n"
            "Cette vérification est unique et sécurisée.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    return user.gender == 'F' and user.identity_verified

async def handle_verification_photo(update: Update, context):
    """Gère la réception des photos de vérification"""
    user_id = update.effective_user.id
    photo = update.message.photo[-1]  # Prendre la plus grande version de la photo
    
    # Sauvegarder la photo
    file = await context.bot.get_file(photo.file_id)
    photo_path = f"verifications/{user_id}_{context.user_data.get('verification_step', 'id')}.jpg"
    await file.download_to_drive(photo_path)
    
    if context.user_data.get('verification_step') == 'id':
        context.user_data['verification_step'] = 'selfie'
        await update.message.reply_text(
            "✅ Photo de la pièce d'identité reçue.\n\n"
            "Maintenant, envoyez un selfie avec votre pièce d'identité."
        )
        return UPLOAD_SELFIE
    else:
        # Les deux photos ont été reçues
        db = get_db()
        user = db.query(User).filter_by(telegram_id=user_id).first()
        user.identity_verified = True
        db.commit()
        
        await update.message.reply_text(
            "✅ Vérification complète!\n\n"
            "Votre identité a été vérifiée avec succès.\n"
            "Vous pouvez maintenant utiliser toutes les fonctionnalités."
        )
        return ConversationHandler.END

async def cancel(update: Update, context):
    """Annule le processus de vérification"""
    await update.message.reply_text(
        "❌ Processus de vérification annulé.\n"
        "Vous pouvez recommencer à tout moment avec /verifier"
    )
    return ConversationHandler.END

def register(application):
    """Enregistre les handlers de vérification"""
    # Créer le dossier pour les vérifications s'il n'existe pas
    os.makedirs("verifications", exist_ok=True)
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('verifier', start_verification),
            CallbackQueryHandler(start_verification, pattern='^verify_identity$')
        ],
        states={
            UPLOAD_ID: [MessageHandler(filters.PHOTO, handle_verification_photo)],
            UPLOAD_SELFIE: [MessageHandler(filters.PHOTO, handle_verification_photo)]
        },
        fallbacks=[CommandHandler('annuler', cancel)],
        name="verification_conversation",  # Ajouté pour persistent=True
        persistent=True,
        allow_reentry=True,
        per_message=False  # Important : évite le warning PTBUserWarning
    )
    application.add_handler(conv_handler)
