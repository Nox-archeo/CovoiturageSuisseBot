import logging
import functools
import traceback
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

def debug_callback(func):
    """Décorateur pour déboguer les callbacks de boutons"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if update.callback_query:
            logger.info(f"🔘 Bouton cliqué: {update.callback_query.data}")
            logger.info(f"👤 Utilisateur: ID {update.effective_user.id}, Username: {update.effective_user.username}")
            logger.info(f"👤 UserData: {context.user_data}")
        
        try:
            result = await func(update, context, *args, **kwargs)
            logger.info(f"✅ Résultat de la fonction {func.__name__}: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Erreur dans {func.__name__}:")
            logger.error(traceback.format_exc())
            # Tenter d'informer l'utilisateur
            try:
                if update.callback_query:
                    await update.callback_query.answer("Une erreur s'est produite. Réessayez ou utilisez /start.")
                    await update.callback_query.edit_message_text(
                        "⚠️ *Désolé, une erreur s'est produite*\n\n"
                        "Veuillez réessayer en utilisant /start pour recommencer.",
                        parse_mode="Markdown"
                    )
            except Exception:
                pass
            # Relancer l'exception pour éviter de bloquer silencieusement
            raise
    
    return wrapper
