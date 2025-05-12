from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from database.models import Trip, Booking, User
import os

# Définition directe de votre ID admin
ADMIN_IDS = [5932296330]  # Votre ID Telegram vérifié

async def admin_panel(update: Update, context: CallbackContext):
    """Panneau d'administration"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Accès non autorisé.")
        return

    keyboard = [
        [InlineKeyboardButton("Trajets en attente", callback_data="admin_pending_trips")],
        [InlineKeyboardButton("Litiges", callback_data="admin_disputes")],
        [InlineKeyboardButton("Statistiques", callback_data="admin_stats")]
    ]
    await update.message.reply_text(
        "Panel Administrateur\n"
        "Sélectionnez une option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def register(dispatcher):
    """Enregistre les handlers admin"""
    dispatcher.add_handler(CommandHandler("admin", admin_panel))
