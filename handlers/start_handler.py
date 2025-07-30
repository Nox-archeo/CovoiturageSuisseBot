import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackContext, ConversationHandler, 
    MessageHandler, filters, CallbackQueryHandler
)
from database.models import User
from database import get_db

logger = logging.getLogger(__name__)

# Définir les états de la conversation
PHONE_ENTRY = 1

async def start(update: Update, context: CallbackContext):
    """Handler pour la commande /start"""
    # Sauvegarder l'utilisateur dans la BDD
    try:
        db = get_db()
        user = update.effective_user
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        if not db_user:
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if not full_name:
                full_name = "Utilisateur"
            
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                full_name=full_name
            )
            db.add(new_user)
            db.commit()
            logger.info(f"Nouvel utilisateur créé: {user.id}")
            
            # Demander le numéro de téléphone pour les nouveaux utilisateurs
            await update.message.reply_text(
                "📱 Bienvenue sur CovoiturageSuisse!\n\n"
                "Pour continuer, merci de nous fournir votre numéro de téléphone.\n"
                "Celui-ci sera partagé uniquement avec vos co-voyageurs lors d'une réservation confirmée.\n\n"
                "Format: +41 XX XXX XX XX ou 07X XXX XX XX"
            )
            return PHONE_ENTRY
        
        # Si l'utilisateur existe mais n'a pas de téléphone
        if not db_user.phone:
            await update.message.reply_text(
                "📱 Pour utiliser pleinement CovoiturageSuisse, nous avons besoin de votre numéro de téléphone.\n"
                "Celui-ci sera partagé uniquement avec vos co-voyageurs lors d'une réservation confirmée.\n\n"
                "Format: +41 XX XXX XX XX ou 07X XXX XX XX"
            )
            return PHONE_ENTRY
        
        # L'utilisateur existe et a déjà un téléphone, afficher le menu principal
        return await show_main_menu(update, context)
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de l'utilisateur: {e}")
        # En cas d'erreur, afficher quand même le menu principal
        return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: CallbackContext):
    """Affiche le menu principal"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Rechercher", callback_data="rechercher"),
            InlineKeyboardButton("➕ Créer", callback_data="menu:create")
        ],
        [
            InlineKeyboardButton("👤 Mon Profil", callback_data="profil"),
            InlineKeyboardButton("🗂️ Mes Trajets", callback_data="mes_trajets")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        "🚗 Bienvenue sur CovoiturageSuisse!\n\n"
        "Je suis votre assistant pour trouver ou proposer des trajets en Suisse.\n\n"
        "Que souhaitez-vous faire ?"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    
    return ConversationHandler.END

async def handle_phone_input(update: Update, context: CallbackContext):
    """Gère l'entrée du numéro de téléphone lors de l'inscription"""
    if not update.message:
        return PHONE_ENTRY

    phone = update.message.text.strip()
    
    # Nettoyage du numéro
    phone = phone.replace(" ", "").replace("-", "").replace(".", "")
    if phone.startswith("0"):
        phone = "+41" + phone[1:]
    
    # Validation du format
    if not (phone.startswith('+41') and len(phone) == 12 and phone[1:].isdigit()):
        await update.message.reply_text(
            "❌ Format invalide. Veuillez utiliser:\n"
            "+41 XX XXX XX XX ou\n"
            "07X XXX XX XX"
        )
        return PHONE_ENTRY
    
    # Enregistrer le numéro dans la base de données
    try:
        db = get_db()
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if user:
            user.phone = phone
            db.commit()
            await update.message.reply_text(f"✅ Numéro de téléphone enregistré: {phone}")
        else:
            await update.message.reply_text("❌ Erreur: utilisateur non trouvé.")
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du téléphone: {e}")
        await update.message.reply_text("❌ Une erreur est survenue. Veuillez réessayer.")
        return PHONE_ENTRY
    
    # Afficher le menu principal
    return await show_main_menu(update, context)

async def cancel_phone_entry(update: Update, context: CallbackContext):
    """Annule l'entrée du numéro de téléphone"""
    await update.message.reply_text(
        "⚠️ L'entrée du numéro de téléphone a été annulée. "
        "Certaines fonctionnalités peuvent être limitées sans un numéro de téléphone valide."
    )
    return await show_main_menu(update, context)

# Créer un ConversationHandler pour gérer l'inscription et la saisie du téléphone
start_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        PHONE_ENTRY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input),
            CommandHandler('cancel', cancel_phone_entry)
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel_phone_entry)],
    name="start_conversation",
    persistent=True,
    allow_reentry=True,
    per_message=False
)

def register(application):
    """Enregistre les handlers dans l'application"""
    application.add_handler(start_conv_handler)
    logger.info("Start handler registered.")
