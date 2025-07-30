#!/usr/bin/env python
"""
Handler de debug pour capturer tous les callbacks non traités
"""
import logging
from telegram import Update
from telegram.ext import CallbackQueryHandler, CallbackContext

logger = logging.getLogger(__name__)

async def debug_unhandled_callback(update: Update, context: CallbackContext):
    """Capture tous les callbacks non traités pour debug"""
    if update.callback_query:
        query = update.callback_query
        logger.warning(f"🔍 CALLBACK NON TRAITÉ: {query.data} (user: {update.effective_user.id})")
        await query.answer("⚠️ Callback non traité: " + query.data)
    return

# Handler de debug à ajouter en dernière position
debug_callback_handler = CallbackQueryHandler(debug_unhandled_callback)
