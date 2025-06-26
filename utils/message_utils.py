"""
Utilitaires pour la gestion des messages Telegram
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

async def safe_edit_message_text(update, text, reply_markup=None, parse_mode=None):
    """
    Modifie le texte d'un message de manière sécurisée, en gérant l'erreur 'Message is not modified'.
    
    Args:
        update: L'objet Update contenant le callback_query
        text: Le nouveau texte du message
        reply_markup: La nouvelle markup des boutons (InlineKeyboardMarkup)
        parse_mode: Le mode de parsing du texte (ParseMode)
        
    Returns:
        bool: True si la mise à jour a réussi ou si l'erreur est simplement 'Message is not modified'
    """
    try:
        # Ne pas ajouter de caractère invisible pour permettre au contenu réel de changer
        # Le contenu visible doit être différent pour que le message soit véritablement mis à jour
        
        # Utiliser directement le callback_query pour éditer le message
        query = update.callback_query
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Message identique, on ignore simplement cette erreur
            logger.debug("Message identique ignoré: %s", str(e))
            return True
        else:
            # Autre erreur BadRequest, on la journalise
            logger.error("Erreur lors de la mise à jour du message: %s", str(e))
            raise  # Réémettre l'exception
