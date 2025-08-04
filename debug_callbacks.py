"""
Script de debugging pour capturer TOUS les callbacks et voir ce qui se passe
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def debug_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture TOUS les callbacks pour debugging"""
    if update.callback_query:
        query = update.callback_query
        callback_data = query.data
        user_id = update.effective_user.id
        
        logger.error(f"🔥 DEBUG CALLBACK CAPTURED: user={user_id}, data='{callback_data}'")
        print(f"🔥 DEBUG CALLBACK CAPTURED: user={user_id}, data='{callback_data}'")
        
        await query.answer(f"DEBUG: Reçu '{callback_data}'", show_alert=True)
        
        # Si c'est un callback search_canton, forcer la réponse
        if callback_data.startswith("search_canton:"):
            canton_code = callback_data.split(':')[1]
            await query.edit_message_text(
                f"🔥 DEBUG FORCÉ: Canton {canton_code} sélectionné!\n\n"
                f"Le callback '{callback_data}' a été intercepté par le debug handler.\n\n"
                f"Ceci prouve que les callbacks fonctionnent mais sont mal routés."
            )
    else:
        logger.error(f"🔥 DEBUG: Update sans callback_query reçu")
