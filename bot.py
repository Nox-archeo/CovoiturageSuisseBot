import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    PicklePersistence
)
from dotenv import load_dotenv
import os
from handlers import (
    subscription_handlers,
    profile_handlers,
    trip_handlers,
    payment_handlers,
    admin_handlers,
    rating_handlers,
    booking_handlers
)
from utils.languages import TRANSLATIONS
from handlers import menu_handlers
from database import get_db
from database.models import User  # Ajout de l'import manquant

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Correction ici: levelname au lieu de levelvel
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Chargement du token
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start_command(update: Update, context):
    """Point d'entrée du bot"""
    try:
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter_by(telegram_id=user_id).first()
        
        # Crée le profil utilisateur s'il n'existe pas
        if not user:
            user = User(
                telegram_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                language='fr',
                is_driver=False,
                is_passenger=False,
                rating=5.0,
                trips_completed=0
            )
            db.add(user)
            db.commit()

        keyboard = [
            [
                InlineKeyboardButton("🔍 Chercher un trajet", callback_data="search"),
                InlineKeyboardButton("🚗 Proposer un trajet", callback_data="create")
            ],
            [
                InlineKeyboardButton("👤 Mon profil", callback_data="profile"),
                InlineKeyboardButton("🗺️ Mes trajets", callback_data="my_trips")
            ],
            [
                InlineKeyboardButton("🌟 Mode conducteur", callback_data="driver"),
                InlineKeyboardButton("🧍 Mode passager", callback_data="passenger")
            ]
        ]
        
        await update.message.reply_text(
            f"Bonjour {user.first_name} ! 👋\n\n"
            "Bienvenue sur CovoiturageSuisse\n\n"
            "• Trouvez un trajet en tant que passager 🧍\n"
            "• Proposez vos trajets en tant que conducteur 🚗\n\n"
            "Que souhaitez-vous faire ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Erreur: {e}")
        await update.message.reply_text(
            "Une erreur est survenue. Tapez /start pour recommencer."
        )

async def help_command(update: Update, context):
    """Affiche l'aide"""
    await update.message.reply_text(
        "🔰 Aide - CovoiturageSuisse\n\n"
        "   • 🚗 Conducteur : pour proposer des trajets\n"
        "   • 🧍 Passager : pour réserver des places\n\n"
        "2️⃣ Commandes principales :\n"
        "/start - Menu principal\n"
        "/profil - Gérer vos profils\n"
        "/chercher - Rechercher un trajet\n"
        "/creer - Proposer un trajet\n"
       "/mes_trajets - Voir vos trajets\n\n"
        "💳 Paiements :\n"
        "• Les paiements sont sécurisés via Stripe\n"
        "• L'argent est transféré au conducteur après le trajet\n\n"
        "ℹ️ Besoin d'aide ? Contactez @admin"
    )

async def select_language(update: Update, context):
    """Permet à l'utilisateur de choisir sa langue"""
    keyboard = [
        [
            InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr"),
            InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang_de")
        ],
        [
            InlineKeyboardButton("Italiano 🇮🇹", callback_data="lang_it"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
        ]
    ]
    await update.message.reply_text(
        "Choisissez votre langue / Wählen Sie Ihre Sprache / Select your language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def language_callback(update: Update, context):
    """Gère le choix de la langue"""
    query = update.callback_query
    lang = query.data.replace("lang_", "")
    context.user_data['language'] = lang
    # Mettre à jour la langue dans la base de données
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    if user:
        user.language = lang
        db.commit()
    # Afficher le menu principal dans la langue choisie
    await show_main_menu(update, context, lang)
    await query.answer(f"Langue changée en {lang}")

async def show_main_menu(update: Update, context, lang='fr'):
    """Affiche le menu principal dans la langue choisie"""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['fr'])
    keyboard = [
        [
            InlineKeyboardButton(translations['menu']['search'], callback_data="search_trip"),
            InlineKeyboardButton(translations['menu']['create'], callback_data="create_trip"),
        ],
        [
            InlineKeyboardButton(translations['menu']['profile'], callback_data="profile"),
            InlineKeyboardButton(translations['menu']['bookings'], callback_data="my_bookings")
        ],
        [InlineKeyboardButton(translations['menu']['language'], callback_data="change_language")]
    ]
    # Utiliser reply_text pour nouveau message ou edit_message_text pour mettre à jour
    if update.callback_query:
        await update.callback_query.message.edit_text(
            translations['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            translations['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def profile_command(update: Update, context):
    """Raccourci vers le profil"""
    await profile_handlers.profile_menu(update, context)

def setup():
    """Configure les handlers du bot"""
    persistence = PicklePersistence(filepath="conversation_states.pickle")
    
    application = Application.builder()\
        .token(TOKEN)\
        .persistence(persistence)\
        .build()
    
    # Handlers principaux
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    
    # Gestion des profils
    profile_handlers.register(application)
    
    # Gestion des trajets
    trip_handlers.register(application)
    
    # Gestion des réservations
    booking_handlers.register(application)
    
    # Gestion des paiements
    payment_handlers.register(application)
    
    # Gestion des notations
    rating_handlers.register(application)
    
    # Admin
    admin_handlers.register(application)
    
    return application

def main():
    """Point d'entrée principal"""
    app = asyncio.run(setup())
    app.run_polling()

if __name__ == '__main__':
    main()

