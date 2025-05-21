import logging
from typing import Callable
from telegram import Update
from telegram.ext import CallbackContext

button_logger = logging.getLogger("button_debugger")
button_logger.setLevel(logging.DEBUG)

# Ajouter un handler de fichier pour stocker les logs de debug des boutons
file_handler = logging.FileHandler("button_debug.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
button_logger.addHandler(file_handler)

def debug_button_callback(func: Callable):
    """Décorateur pour déboguer les callbacks des boutons"""
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        query = update.callback_query
        if query:
            button_logger.debug(f"👉 Bouton cliqué: {query.data}")
            button_logger.debug(f"👤 Utilisateur: {update.effective_user.id} ({update.effective_user.username})")
            button_logger.debug(f"📝 Context user_data: {context.user_data}")
        
        try:
            result = await func(update, context, *args, **kwargs)
            button_logger.debug(f"✅ Résultat du callback: {result}")
            return result
        except Exception as e:
            button_logger.error(f"❌ Erreur dans le callback: {str(e)}", exc_info=True)
            # Informer l'utilisateur
            if query:
                await query.answer("Une erreur est survenue. Veuillez réessayer.")
            # Re-raise l'exception pour ne pas interrompre le flux normal des erreurs
            raise
    
    return wrapper

# Fonction pour utiliser le débogage sans décorateur
async def log_button_click(update: Update, context: CallbackContext):
    """Enregistre les informations sur un clic de bouton"""
    query = update.callback_query
    if query:
        button_logger.debug(f"👉 Bouton cliqué: {query.data}")
        button_logger.debug(f"👤 Utilisateur: {update.effective_user.id} ({update.effective_user.username})")
        button_logger.debug(f"📝 Context user_data: {context.user_data}")
