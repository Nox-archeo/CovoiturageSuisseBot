from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler
from database.models import Trip

# États de conversation pour la création de trajet
DEPARTURE, ARRIVAL, DATE, SEATS, PRICE, CONFIRM = range(6)

async def create_trip(update: Update, context: CallbackContext):
    """Démarre le processus de création d'un trajet"""
    await update.message.reply_text(
        "Commençons la création de votre trajet! 🚗\n"
        "Quelle est votre ville de départ?"
    )
    return DEPARTURE

async def search_trip(update: Update, context: CallbackContext):
    """Recherche un trajet"""
    await update.message.reply_text(
        "Recherche de trajets 🔍\n"
        "Entrez votre ville de départ:"
    )
    return DEPARTURE

def register(application):
    """Enregistre les handlers pour les trajets"""
    # Handler pour la création de trajet
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('creer', create_trip)],
        states={
            DEPARTURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, departure)],
            ARRIVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, arrival)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],
            SEATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, seats)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
            CONFIRM: [CallbackQueryHandler(confirm)]
        },
        fallbacks=[CommandHandler('annuler', cancel)]
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("chercher", search_trip))
