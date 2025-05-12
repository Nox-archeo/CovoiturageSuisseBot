from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from database.models import User, ReferralBonus

BONUS_AMOUNT = 5  # CHF de bonus par parrainage

async def generate_referral_link(update: Update, context):
    """Génère un lien de parrainage"""
    user_id = update.effective_user.id
    referral_code = generate_unique_code(user_id)
    
    await update.message.reply_text(
        "🎁 Programme de parrainage\n\n"
        f"Votre lien: t.me/votre_bot?start=ref_{referral_code}\n\n"
        f"Gagnez {BONUS_AMOUNT} CHF pour chaque ami qui s'inscrit!\n"
        f"Bonus accumulés: {get_total_bonus(user_id)} CHF"
    )

async def handle_referral(update: Update, context):
    """Traite un nouveau parrainage"""
    ref_code = context.args[0].replace('ref_', '') if context.args else None
    if not ref_code:
        return
    
    referrer = User.get_by_ref_code(ref_code)
    if referrer:
        # Créer le bonus
        ReferralBonus.create(
            referrer_id=referrer.id,
            referred_id=update.effective_user.id,
            amount=BONUS_AMOUNT
        )
        
        await context.bot.send_message(
            chat_id=referrer.telegram_id,
            text=f"🎁 Félicitations! Vous avez gagné {BONUS_AMOUNT} CHF grâce à un parrainage!"
        )
