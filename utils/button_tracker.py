import logging
from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext

# Configurer un logger spécial pour tracer les callbacks
button_logger = logging.getLogger("button_tracker")
button_logger.setLevel(logging.DEBUG)

# Ajouter un handler pour écrire dans un fichier
file_handler = logging.FileHandler("button_debug.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
button_logger.addHandler(file_handler)

# Ajouter un handler pour écrire dans la console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("🔘 BUTTON: %(message)s"))
button_logger.addHandler(console_handler)

def track_button(func):
    """Décorateur pour tracer les callbacks des boutons"""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if update.callback_query:
            button_logger.info(f"Button clicked: {update.callback_query.data} by user {update.effective_user.id}")
            try:
                result = await func(update, context, *args, **kwargs)
                button_logger.info(f"Handler result: {result}")
                return result
            except Exception as e:
                button_logger.error(f"Error in button handler: {str(e)}", exc_info=True)
                # Répondre au callback pour éviter l'erreur "Callback Query expired"
                await update.callback_query.answer("Une erreur s'est produite. Veuillez réessayer.")
                # Informer l'utilisateur
                await update.callback_query.edit_message_text(
                    "❌ Une erreur s'est produite lors du traitement de votre demande.\n"
                    "Veuillez réessayer en utilisant /start pour revenir au menu principal."
                )
                raise
        else:
            return await func(update, context, *args, **kwargs)
    return wrapper
