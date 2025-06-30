from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

async def actual_help_message_function(update: Update, context: CallbackContext):
    """Envoie le message d'aide."""
    help_text = (
        "🆘 *Aide CovoiturageSuisse*\n\n"
        "*Commandes principales:*\n"
        "/creer - Proposer un nouveau trajet\n"
        "/chercher - Chercher un trajet\n"
        "/mes_trajets - Voir vos trajets\n"
        "/profil - Gérer votre profil\n"
        "/start - Afficher le menu principal\n"
        "/cancel - Annuler l'opération en cours\n\n"
        "*💳 Commandes de paiement PayPal:*\n"
        "/definirpaypal - Configurer votre email PayPal\n"
        "/payer <id_trajet> - Payer un trajet\n"
        "/confirmer <id_trajet> - Confirmer un trajet (conducteur)\n"
        "/statut_paiement - Vérifier vos paiements\n\n"
        "*ℹ️ Comment ça marche:*\n"
        "1. Les passagers paient via PayPal\n"
        "2. 88% va au conducteur, 12% à la plateforme\n"
        "3. Le conducteur confirme le trajet pour recevoir le paiement\n\n"
        "Pour plus d'aide, contactez-nous via les options du menu."
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode='Markdown')
    elif update.callback_query: # Si appelé depuis un bouton
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(help_text, parse_mode='Markdown')

# Renommez cette fonction si votre fonction d'aide principale a un autre nom
async def help_guide(update: Update, context: CallbackContext):
    """Fonction appelée par le CommandHandler ou un bouton d'aide."""
    await actual_help_message_function(update, context)
    # Si help_guide est aussi utilisé pour des boutons avec callback_data="menu:help"
    # et que cela doit retourner un état de conversation, ajustez ici.
    # Pour un simple message d'aide, pas de retour d'état nécessaire.

def register(application):
    """Enregistre les handlers pour les commandes d'aide."""
    application.add_handler(CommandHandler("help", help_guide)) # Assurez-vous que 'help_guide' est le nom de la fonction qui envoie le message
    # Si vous avez des boutons dans le menu d'aide, ajoutez leurs CallbackQueryHandlers ici
    # Par exemple:
    # application.add_handler(CallbackQueryHandler(handle_faq_button, pattern="^help:faq$"))
    logger.info("Help handlers registered.")
