from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from database.models import Trip, User, Booking
from database import get_db

async def handle_driver_profile(update: Update, context):
    """Gère l'affichage du profil conducteur"""
    query = update.callback_query
    user_id = query.from_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if user and user.is_driver:
        stats = await get_driver_stats(user_id)
        keyboard = [
            [InlineKeyboardButton("📝 Modifier profil", callback_data="edit_driver")],
            [InlineKeyboardButton("🔄 Retour", callback_data="back_to_profile")]
        ]
        await query.edit_message_text(
            f"🚗 Profil Conducteur\n\n"
            f"Note: ⭐ {stats['rating']:.1f}\n"
            f"Trajets effectués: {stats['trips_count']}\n"
            f"Revenus totaux: {stats['total_earnings']} CHF",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(
            "Vous n'avez pas encore de profil conducteur.\n"
            "Utilisez /profil pour en créer un."
        )

async def handle_passenger_profile(update: Update, context):
    """Gère l'affichage du profil passager"""
    query = update.callback_query
    user_id = query.from_user.id
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if user and user.is_passenger:
        stats = await get_passenger_stats(user_id)
        keyboard = [
            [InlineKeyboardButton("📝 Modifier profil", callback_data="edit_passenger")],
            [InlineKeyboardButton("🔄 Retour", callback_data="back_to_profile")]
        ]
        await query.edit_message_text(
            f"🧍 Profil Passager\n\n"
            f"Note: ⭐ {stats['rating']:.1f}\n"
            f"Trajets effectués: {stats['trips_count']}\n"
            f"Dépenses totales: {stats['total_spent']} CHF",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(
            "Vous n'avez pas encore de profil passager.\n"
            "Utilisez /profil pour en créer un."
        )

async def get_driver_stats(user_id):
    """Récupère les statistiques du conducteur"""
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    trips = db.query(Trip).filter_by(driver_id=user.id).all()
    
    return {
        'rating': user.driver_rating,
        'trips_count': len(trips),
        'total_earnings': sum(t.price_per_seat * len(t.bookings) for t in trips)
    }

async def get_passenger_stats(user_id):
    """Récupère les statistiques du passager"""
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    bookings = db.query(Booking).filter_by(passenger_id=user.id).all()
    
    return {
        'rating': user.passenger_rating,
        'trips_count': len(bookings),
        'total_spent': sum(b.trip.price_per_seat for b in bookings)
    }

def register(application):
    """Enregistre les handlers des actions du menu"""
    application.add_handler(CallbackQueryHandler(handle_driver_profile, pattern="^driver_profile$"))
    application.add_handler(CallbackQueryHandler(handle_passenger_profile, pattern="^passenger_profile$"))
    
    # Ajouter d'autres handlers pour les boutons du profil
    application.add_handler(CallbackQueryHandler(handle_driver_profile, pattern="^edit_driver$"))
    application.add_handler(CallbackQueryHandler(handle_passenger_profile, pattern="^edit_passenger$"))
    application.add_handler(CallbackQueryHandler(handle_driver_profile, pattern="^back_to_profile$"))
