from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Trip, User, Booking
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io

async def show_user_stats(update: Update, context):
    """Affiche les statistiques détaillées de l'utilisateur"""
    user_id = update.effective_user.id
    user = User.get(user_id)
    
    # Statistiques générales
    stats_text = (
        "📊 Vos statistiques\n\n"
        f"🌟 Note moyenne conducteur: {user.driver_rating:.1f}/5\n"
        f"💰 Gains totaux: {calculate_total_earnings(user_id)} CHF\n"
        f"🚗 Trajets effectués: {user.trips_completed}\n"
        f"✅ Taux de complétion: {calculate_completion_rate(user_id):.0%}\n"
        f"⭐️ Avis positifs: {count_positive_reviews(user_id)}\n"
    )
    
    # Générer graphique des trajets
    plt.figure(figsize=(10, 5))
    trips_data = get_trips_over_time(user_id)
    plt.plot(trips_data['dates'], trips_data['counts'])
    plt.title('Vos trajets sur les 3 derniers mois')
    
    # Convertir le graphique en bytes pour Telegram
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    keyboard = [
        [
            InlineKeyboardButton("📈 Vue détaillée", callback_data="detailed_stats"),
            InlineKeyboardButton("💰 Revenus", callback_data="earnings_stats")
        ]
    ]
    
    await update.message.reply_photo(
        photo=buf,
        caption=stats_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Correction : exclure les trajets annulés des statistiques
    # (Supposons que get_trips_over_time et autres fonctions utilisent Trip)
    # Ajoutez ce filtre dans les fonctions concernées ou ici si la liste est accessible
    # Exemple :
    # trips = db.query(Trip).filter(Trip.user_id == user_id, (Trip.is_cancelled == False) | (Trip.is_cancelled.is_(None))).all()
