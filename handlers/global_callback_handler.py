"""
Gestionnaire global pour tous les callbacks non gérés
Capture les boutons qui ne sont pas traités par d'autres handlers
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def handle_missing_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gestionnaire global pour les callbacks manqués
    Fournit une réponse appropriée et redirige vers le menu principal
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    logger.warning(f"Callback non géré détecté: {callback_data}")
    
    # Réponses spécifiques selon le type de callback
    if "profil" in callback_data.lower() or "profile" in callback_data.lower():
        response_text = (
            "👤 *Edition du profil*\n\n"
            "Cette fonction sera bientôt disponible.\n"
            "En attendant, utilisez /profil pour accéder à vos paramètres."
        )
    elif "back" in callback_data.lower() or "retour" in callback_data.lower():
        response_text = (
            "🔙 *Retour*\n\n"
            "Retour au menu principal..."
        )
        # Pour les boutons de retour, rediriger directement vers le menu
        from handlers.menu_handlers import show_main_menu
        await show_main_menu(update, context)
        return
    elif "search" in callback_data.lower() or "recherch" in callback_data.lower():
        response_text = (
            "🔍 *Recherche*\n\n"
            "Fonction de recherche en cours de développement.\n"
            "Utilisez les commandes /chercher ou /propositions en attendant."
        )
    elif "paiement" in callback_data.lower() or "payment" in callback_data.lower():
        response_text = (
            "💳 *Paiements*\n\n"
            "Système de paiement en cours de configuration.\n"
            "Contactez le support pour l'assistance."
        )
    elif "menu" in callback_data.lower():
        response_text = (
            "🏠 *Menu*\n\n"
            "Redirection vers le menu principal..."
        )
        # Pour les menus, rediriger vers le menu principal
        from handlers.menu_handlers import show_main_menu
        await show_main_menu(update, context)
        return
    else:
        response_text = (
            "⚠️ *Fonction non disponible*\n\n"
            f"La fonction demandée (`{callback_data}`) n'est pas encore implémentée.\n\n"
            "Nous travaillons activement sur cette fonctionnalité !"
        )
    
    # Boutons de navigation
    keyboard = [
        [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")],
        [InlineKeyboardButton("👤 Mon profil", callback_data="profile_main")],
        [InlineKeyboardButton("❓ Aide", callback_data="menu:help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(
            response_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du message: {e}")
        # En cas d'erreur, envoyer un nouveau message
        await query.message.reply_text(
            response_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_profile_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gestionnaire spécifique pour les callbacks du profil
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    logger.info(f"Callback profil reçu: {callback_data}")
    
    # Rediriger vers le gestionnaire de profil approprié
    if callback_data == "profile_main" or callback_data == "profil":
        from handlers.profile_handler import profile_handler
        await profile_handler(update, context)
    elif callback_data.startswith("profile:"):
        # Callbacks spécifiques du profil
        action = callback_data.split(":", 1)[1]
        
        if action == "edit":
            response_text = (
                "✏️ *Edition du profil*\n\n"
                "🔧 Cette fonction est en cours de mise à jour.\n"
                "Utilisez la commande /profil pour accéder à votre profil."
            )
        elif action == "back_to_profile":
            from handlers.profile_handler import profile_handler
            await profile_handler(update, context)
            return
        else:
            response_text = (
                f"👤 *Profil - {action}*\n\n"
                "Cette section de votre profil sera bientôt disponible.\n"
                "Merci de votre patience !"
            )
        
        keyboard = [
            [InlineKeyboardButton("👤 Mon profil", callback_data="profile_main")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            response_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

# Liste des patterns de callbacks couramment manqués
MISSING_CALLBACK_PATTERNS = [
    "profil",
    "profile:",
    "edit_profile",
    "back_to_profile", 
    "menu:profile",
    "main_menu",
    "ignore",
    "setup_paypal",
    "why_paypal_required",
    "menu:become_driver",
    "search_new",
    "search_drivers",
    "search_passengers",
    "view_passenger_trips",
    "mes_trajets",
    "rechercher"
]
