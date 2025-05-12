from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from database import get_db
from database.models import Trip

ENTERING_DEPARTURE = 0
ENTERING_DESTINATION = 1
CHOOSING_DATE = 2
SELECTING_TRIP = 3

async def start_search(update: Update, context):
    """Démarre la recherche de trajet"""
    await update.message.reply_text(
        """🔍 <b>Recherche de trajet</b>

Entrez votre ville de départ:
• Par code postal (ex: 1700)
• Par nom de ville (ex: Fribourg)""",
        parse_mode='HTML'
    )
    return ENTERING_DEPARTURE

async def search_trips(departure, destination, date):
    """Recherche les trajets disponibles"""
    db = get_db()
    return db.query(Trip).filter(
        Trip.departure == departure,
        Trip.destination == destination,
        Trip.date == date,
        Trip.seats_available > 0
    ).all()

async def show_results(update: Update, context):
    """Affiche les résultats de recherche"""
    trips = await search_trips(
        context.user_data['departure'],
        context.user_data['destination'],
        context.user_data['date']
    )

    if not trips:
        await update.message.reply_text(
            "❌ Aucun trajet trouvé pour ces critères."
        )
        return ConversationHandler.END

    buttons = []
    for trip in trips:
        buttons.append([
            InlineKeyboardButton(
                f"{trip.time} - {trip.price}CHF ({trip.seats_available} places)",
                callback_data=f"book_{trip.id}"
            )
        ])

    await update.message.reply_text(
        f"""🚗 <b>Trajets disponibles</b>
De: {context.user_data['departure']}
À: {context.user_data['destination']}
Date: {context.user_data['date']}

Sélectionnez un trajet:""",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )
    return SELECTING_TRIP

def register(application):
    """Enregistre les handlers de recherche"""
    search_conv = ConversationHandler(
        entry_points=[CommandHandler('chercher', start_search)],
        states={
            ENTERING_DEPARTURE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_departure)
            ],
            ENTERING_DESTINATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_destination)
            ],
            CHOOSING_DATE: [
                CallbackQueryHandler(handle_date, pattern='^date_')
            ],
            SELECTING_TRIP: [
                CallbackQueryHandler(handle_trip_selection, pattern='^book_')
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(search_conv)
