import stripe
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
import os
from datetime import datetime, timedelta
from database.models import User
from database import get_db

stripe.api_key = os.getenv('STRIPE_API_KEY')
SUBSCRIPTION_PRICE = 250  # 2.50 CHF en centimes

async def subscribe_command(update: Update, context):
    """Commence le processus d'abonnement"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'chf',
                    'unit_amount': SUBSCRIPTION_PRICE,
                    'product_data': {
                        'name': 'Abonnement Premium CovoiturageSuisse',
                        'description': 'Accès mensuel à toutes les fonctionnalités'
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://t.me/votre_bot?start=sub_success',
            cancel_url='https://t.me/votre_bot?start=sub_cancel',
        )
        
        keyboard = [[InlineKeyboardButton("S'abonner", url=session.url)]]
        await update.message.reply_text(
            "🌟 Abonnement Premium - 2.50 CHF/mois\n\n"
            "✅ Accès à toutes les fonctionnalités\n"
            "✅ Création de trajets illimitée\n"
            "✅ Recherche et réservation\n\n"
            "Cliquez ci-dessous pour vous abonner:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await update.message.reply_text(
            "Désolé, une erreur est survenue. Réessayez plus tard."
        )

async def check_subscription(user_id: int) -> bool:
    """Vérifie l'abonnement de l'utilisateur"""
    db = get_db()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        return False
    return user.subscription_end and user.subscription_end > datetime.now()

async def create_subscription(update: Update, context):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'chf',
                    'unit_amount': 250,  # 2.50 CHF
                    'product_data': {
                        'name': 'Abonnement Premium CovoiturageSuisse',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://t.me/your_bot?start=sub_success',
            cancel_url='https://t.me/your_bot?start=sub_cancel',
        )
        
        keyboard = [[InlineKeyboardButton("Payer", url=session.url)]]
        await update.callback_query.message.reply_text(
            "Abonnement Premium - 2.50 CHF/mois",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await update.callback_query.message.reply_text("Erreur lors du paiement.")

def is_premium(user_id: int) -> bool:
    """Vérifie si l'utilisateur est premium"""
    user = User.get(user_id)
    if not user or not user.subscription_end:
        return False
    return user.subscription_end > datetime.now()

def register(application):
    """Enregistre les handlers d'abonnement"""
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    
    # Handler pour le bouton de création d'abonnement
    application.add_handler(CallbackQueryHandler(create_subscription, pattern="^create_subscription$"))
    
    # Handler pour les callbacks de succès/échec de l'abonnement
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("Abonnement activé!"), pattern="^sub_success$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("Abonnement annulé."), pattern="^sub_cancel$"))
