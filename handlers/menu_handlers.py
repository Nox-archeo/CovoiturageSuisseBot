from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler, 
    CommandHandler, 
    CallbackContext, 
    ConversationHandler, 
    MessageHandler, 
    filters,
    ContextTypes
)
from utils.languages import TRANSLATIONS
from database.models import User
from database import get_db

import logging
import asyncio
from handlers.create_trip_handler import start_create_trip as enter_create_trip_flow
from handlers.search_trip_handler import start_search_trip as enter_search_trip_flow
# Utiliser le nouveau gestionnaire de profil
from handlers.profile_handler import profile_handler

logger = logging.getLogger(__name__)

# States for driver availability conversation
DRIVER_OPTION, DRIVER_AVAILABILITY, DRIVER_AVAIL_TIME, DRIVER_AVAIL_SEATS, DRIVER_AVAIL_DEST, DRIVER_AVAIL_DEST_CITY, CONFIRM_AVAILABILITY = range(7)

# States for profile creation conversation
PROFILE_ROLE_SELECTION, PROFILE_NAME_INPUT, PROFILE_AGE_INPUT, PROFILE_PHONE_INPUT, PROFILE_PAYPAL_INPUT, PROFILE_COMPLETE = range(6)

# Fonction factice pour résoudre le problème de vérification dans start_fixed_bot.py
# La vraie fonction sera importée dynamiquement dans handle_menu_selection
async def list_my_trips(update, context):
    """Fonction factice qui sera remplacée par l'import dynamique"""
    # Import dynamique pour éviter les imports circulaires
    from handlers.trip_handlers import list_my_trips as real_list_my_trips
    return await real_list_my_trips(update, context)

# Fonction pour annuler une conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule la conversation en cours"""
    # Cas 1: Annulation via un callback
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Opération annulée.")
    # Cas 2: Annulation via une commande
    elif update.message:
        await update.message.reply_text("❌ Opération annulée.")
    
    # Nettoyer les données utilisateur
    context.user_data.clear()
    return ConversationHandler.END

async def start_command(update: Update, context: CallbackContext):
    """Commande /start améliorée avec vérification du profil utilisateur"""
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        # Nouvel utilisateur - proposer la création de profil
        keyboard = [
            [InlineKeyboardButton("✅ Créer mon profil", callback_data="menu:create_profile")],
            [InlineKeyboardButton("❓ En savoir plus", callback_data="menu:help")]
        ]
        
        welcome_text = (
            "👋 *Bienvenue sur CovoiturageSuisse!*\n\n"
            "Pour utiliser l'application de covoiturage, vous devez d'abord créer votre profil.\n\n"
            "🚗 *Conducteur* : Proposez vos trajets et recevez des passagers (PayPal requis)\n"
            "🎒 *Passager* : Trouvez des trajets et publiez vos demandes\n\n"
            "💡 *Vous pourrez créer les deux types de profil si vous le souhaitez !*\n\n"
            "Cliquez ci-dessous pour commencer :"
        )
    else:
        # Utilisateur existant - vérifier s'il a les deux profils
        has_driver_profile = user.is_driver and user.paypal_email
        has_passenger_profile = True  # Tous les utilisateurs peuvent être passagers
        
        if has_driver_profile and has_passenger_profile:
            # L'utilisateur a les deux profils - menu simplifié
            keyboard = [
                [
                    InlineKeyboardButton("🚗 Créer un trajet", callback_data="menu:create"),
                    InlineKeyboardButton("🔍 Chercher un trajet", callback_data="menu:search_trip")
                ],
                [
                    InlineKeyboardButton("📋 Mes trajets", callback_data="menu:my_trips"),
                    InlineKeyboardButton("👤 Mon profil", callback_data="menu:profile")
                ],
                [
                    InlineKeyboardButton("❓ Aide", callback_data="menu:help")
                ]
            ]
            
            welcome_text = (
                f"👋 *Bonjour {user.full_name or 'Utilisateur'}!*\n\n"
                f"🎯 **Vous avez accès aux deux modes :**\n\n"
                f"🚗 **Actions rapides disponibles :**\n"
                f"• Créer ou chercher des trajets\n"
                f"• Chercher des passagers ou conducteurs\n"
                f"• Gérer vos trajets et profil\n\n"
                f"Que souhaitez-vous faire aujourd'hui ?"
            )
        elif has_driver_profile:
            # Uniquement profil conducteur - menu simplifié
            keyboard = [
                [
                    InlineKeyboardButton("🚗 Créer un trajet", callback_data="menu:create"),
                    InlineKeyboardButton("🔍 Chercher un trajet", callback_data="menu:search_trip")
                ],
                [
                    InlineKeyboardButton("� Mes trajets", callback_data="menu:my_trips"),
                    InlineKeyboardButton("� Mon profil", callback_data="menu:profile")
                ],
                [
                    InlineKeyboardButton("❓ Aide", callback_data="menu:help")
                ]
            ]
            
            welcome_text = (
                f"👋 *Bonjour {user.full_name or 'Conducteur'}!*\n\n"
                f"🚗 **Mode Conducteur actif**\n"
                f"Que souhaitez-vous faire aujourd'hui ?"
            )
        else:
            # Uniquement profil passager - proposer de créer le profil conducteur
            keyboard = [
                [
                    InlineKeyboardButton("🚗 Créer un trajet", callback_data="menu:create"),
                    InlineKeyboardButton("🔍 Chercher un trajet", callback_data="menu:search_trip")
                ],
                [
                    InlineKeyboardButton("📋 Mes trajets", callback_data="menu:my_trips"),
                    InlineKeyboardButton("👤 Mon profil", callback_data="menu:profile")
                ],
                [
                    InlineKeyboardButton("🚗 Devenir conducteur", callback_data="menu:become_driver"),
                    InlineKeyboardButton("❓ Aide", callback_data="menu:help")
                ]
            ]
            
            welcome_text = (
                f"👋 *Bonjour {user.full_name or 'Passager'}!*\n\n"
                f"🎒 **Mode Passager actif**\n"
                f"Que souhaitez-vous faire aujourd'hui ?\n\n"
                f"💡 *Vous pouvez aussi devenir conducteur en configurant PayPal !*"
            )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

async def handle_menu_buttons(update: Update, context: CallbackContext):
    """Gère les clics sur les boutons du menu principal."""
    query = update.callback_query
    await query.answer()
    
    # Ajouter un log pour voir quel callback est intercepté
    logger.info(f"Menu handler intercepted callback: {query.data}")
    
    # Ne pas intercepter les callbacks du profil ou menu:profile
    if query.data.startswith("profile:") or query.data == "menu:profile":
        logger.info(f"Menu handler: Ignorer le callback de profil: {query.data}")
        # Assurez-vous que le callback n'est pas géré par ce handler
        return ConversationHandler.END
    
    # Vérifier si c'est un callback de calendrier, le menu handler ne devrait pas les intercepter
    if query.data.startswith("create_cal_") or query.data.startswith("calendar:"):
        logger.info(f"Menu handler: Ignorer le callback de calendrier: {query.data}")
        return  # Laissez-le être géré par le gestionnaire de calendrier approprié
    
    action = query.data.split(":")[1] if ":" in query.data else query.data # e.g., "menu:create_trip" -> "create_trip"

    logger.info(f"Menu button clicked: {action}")
    
    # Vérification du profil utilisateur pour les actions avancées
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()

    if action == "create_profile":
        # Démarrer le processus de création de profil
        return await start_profile_creation(update, context)
    
    elif action == "search_trip" or action == "rechercher":
        # Vérifier si l'utilisateur a un profil
        if not user:
            await query.edit_message_text(
                "❌ *Profil requis*\n\n"
                "Vous devez créer un profil avant de pouvoir rechercher un trajet.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Créer mon profil", callback_data="menu:create_profile")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
                ]),
                parse_mode="Markdown"
            )
            return ConversationHandler.END
        
        # This should call the entry point of the search_trip_conv_handler
        return await enter_search_trip_flow(update, context)
    
    elif query.data == "search_drivers":
        # Recherche de conducteurs pour les passagers - redirige vers la recherche normale
        if not user:
            await query.edit_message_text(
                "❌ *Profil requis*\n\n"
                "Vous devez créer un profil avant de pouvoir rechercher des conducteurs.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Créer mon profil", callback_data="menu:create_profile")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
                ]),
                parse_mode="Markdown"
            )
            return ConversationHandler.END
        
        # Rediriger vers la recherche de trajets avec le bon contexte
        return await enter_search_trip_flow(update, context)

    elif action == "my_trips":
        # Vérifier si l'utilisateur a un profil
        if not user:
            await query.edit_message_text(
                "❌ *Profil requis*\n\n"
                "Vous devez créer un profil avant de pouvoir voir vos trajets.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Créer un profil", callback_data="menu:create_profile")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
                ]),
                parse_mode="Markdown"
            )
            return ConversationHandler.END
        
        # Utiliser la même fonction que la commande /mes_trajets pour une expérience cohérente
        from handlers.trip_handlers import list_my_trips
        return await list_my_trips(update, context)
        
    elif action == "profile":
        # Utiliser le nouveau gestionnaire de profil
        logger.info("Button profile clicked, redirecting to profile_handler")
        try:
            return await profile_handler(update, context)
        except Exception as e:
            logger.error(f"Error in profile_handler: {str(e)}", exc_info=True)
            await query.edit_message_text("Une erreur s'est produite lors de l'affichage du profil. Veuillez réessayer.")
            return ConversationHandler.END

    # NOTE: action == "create" is now handled by create_trip_conv_handler directly
    # No need to intercept it here anymore
    
    elif action == "help":
        return await show_help_menu(update, context)
    
    elif action == "become_driver":
        # Activer le profil conducteur et demander PayPal
        return await activate_driver_profile(update, context)
    
    elif query.data == "paypal_input_start":
        # Demander la saisie de l'email PayPal
        await query.edit_message_text(
            "💳 **Configuration PayPal**\n\n"
            "📧 Veuillez entrer votre adresse email PayPal :\n\n"
            "💡 *Exemple : votre-email@example.com*\n\n"
            "⚠️ Assurez-vous que l'email est correct, il sera utilisé pour recevoir les paiements.",
            parse_mode="Markdown"
        )
        return PROFILE_PAYPAL_INPUT
    
    elif action == "back_to_main":
        # Retour au menu principal
        return await start_command(update, context)
    
    elif query.data == "setup_paypal":
        # Rediriger vers la configuration PayPal
        from handlers.paypal_setup_handler import request_paypal_email
        return await request_paypal_email(update, context)
    
    elif query.data.startswith("switch_profile:"):
        # Gérer le changement de profil
        profile_type = query.data.split(":")[1]
        return await switch_user_profile(update, context, profile_type)
    
    elif query.data == "back_to_menu":
        # This is a common callback, ensure start_command handles callback_query
        return await start_command(update, context)
    
    # 🔧 CORRECTION: Nouveaux callbacks gérés
    elif query.data == "main_menu":
        return await start_command(update, context)
    
    elif query.data == "profile_main":
        from handlers.profile_handler import profile_handler
        return await profile_handler(update, context)
    
    elif query.data == "view_payments":
        await query.edit_message_text(
            "💳 *Mes paiements*\n\n"
            "Cette fonctionnalité sera bientôt disponible.\n"
            "En attendant, utilisez /paiements pour accéder aux options de paiement.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
            ]),
            parse_mode="Markdown"
        )
    
    elif query.data == "payment_history":
        await query.edit_message_text(
            "📊 *Historique des paiements*\n\n"
            "Cette fonctionnalité sera bientôt disponible.\n"
            "En attendant, utilisez /paiements pour accéder aux options de paiement.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
            ]),
            parse_mode="Markdown"
        )
    
    elif query.data == "search_passengers":
        # Rediriger vers la recherche de passagers
        keyboard = [
            [InlineKeyboardButton("⚡ Vue rapide", callback_data="view_quick_passenger_trips")],
            [InlineKeyboardButton("🔍 Recherche avancée", callback_data="advanced_search_passengers")],
            [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
        ]
        await query.edit_message_text(
            "🚗 *Recherche de passagers*\n\n"
            "Comment souhaitez-vous rechercher des passagers ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "search_drivers":
        # Rediriger vers la recherche de conducteurs
        await query.edit_message_text(
            "🔍 *Recherche de conducteurs*\n\n"
            "Utilisez la recherche de trajets pour trouver des conducteurs disponibles.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Rechercher un trajet", callback_data="menu:search_trip")],
                [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
            ]),
            parse_mode="Markdown"
        )
    
    elif query.data == "why_paypal_required":
        await query.edit_message_text(
            "💳 *Pourquoi PayPal est requis ?*\n\n"
            "• **Sécurité** : Paiements sécurisés garantis\n"
            "• **Automatisation** : Paiements automatiques après trajets\n"
            "• **Protection** : Protection acheteur et vendeur\n"
            "• **Rapidité** : Virements instantanés\n\n"
            "💡 Configuration PayPal gratuite et rapide !",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Configurer PayPal", callback_data="setup_paypal")],
                [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
            ]),
            parse_mode="Markdown"
        )
    
    elif query.data == "ignore":
        # Pour les éléments de calendrier ou autres éléments non-cliquables
        await query.answer("ℹ️ Élément non-cliquable", show_alert=False)
        return

    # ... (handle other specific menu actions like public:driver_trips if not covered by sub-menus)
    
    # If an action leads to a conversation, it should return the first state of that conversation.
    # If it's a one-off action, it might return ConversationHandler.END or nothing if not in a conversation.
    # For now, assume menu buttons either start a new conversation (handled by their respective handlers) or display info.
    return # Or an appropriate state if this itself is part of a simple menu conversation

# ... (handle_role_choice, handle_driver_option, etc. for driver availability) ...
# These functions should be part of the availability_conv_handler
async def handle_role_choice(update: Update, context: CallbackContext):
    """Gère le choix entre conducteur et passager pour disponibilité (example flow)."""
    query = update.callback_query
    await query.answer()
    
    # Example: This could be an entry point if 'menu:availability' was clicked
    # For now, this function is kept as an example; integrate it if you have a "declare availability" button
    # _, role = query.data.split(":", 1)
    # context.user_data['user_role'] = role
    # if role == "driver":
    #    # ...
    #    return DRIVER_OPTION
    await query.edit_message_text("Déclaration de disponibilité en cours de développement.")
    return ConversationHandler.END


# Placeholder for cancel function if not already globally available
async def cancel_conversation(update: Update, context: CallbackContext):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Opération annulée.")
    else:
        await update.message.reply_text("Opération annulée.")
    context.user_data.clear()
    return ConversationHandler.END

# Example ConversationHandler for driver availability (if you implement this flow)
# availability_conv_handler = ConversationHandler(
# entry_points=[CallbackQueryHandler(handle_role_choice, pattern='^role:(driver|passenger)$')],
# states={
# DRIVER_OPTION: [CallbackQueryHandler(handle_driver_option, pattern='^driver_option:(specific|available)$')],
# DRIVER_AVAILABILITY: [
# CallbackQueryHandler(handle_driver_availability, pattern='^avail_from_'),
# CallbackQueryHandler(handle_driver_availability, pattern='^avail_other_city$'),
# MessageHandler(filters.TEXT & ~filters.COMMAND, handle_driver_availability)
# ],
#         # ... other states ...
#     },
# fallbacks=[CallbackQueryHandler(cancel_conversation, pattern='^cancel_trip$')]
# )

def register(application):
    application.add_handler(CommandHandler("start", start_command))
    # General handler for menu callbacks that don't start a new major conversation
    # N'interceptez que des motifs très spécifiques pour éviter les conflits avec d'autres handlers
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:(?!profile$|create$).*"))  # Exclure menu:profile et menu:create
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^back_to_menu$"))
    # Ajoutez les callbacks spécifiques pour les boutons de menu principaux
    # REMOVED: creer_trajet is now handled by create_trip_conv_handler
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^rechercher$"))
    # Ne pas gérer "profil" ici car il est géré par profile_handler
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^mes_trajets$"))


    # Add other handlers specific to menu_handlers.py, like the availability_conv_handler if used
    # application.add_handler(availability_conv_handler)

    # Handler for public trip listings if not part of search_handler
    # application.add_handler(CallbackQueryHandler(handle_public_trips, pattern="^public:"))
    logger.info("Menu handlers registered.")

async def start_profile_creation(update: Update, context: CallbackContext):
    """Démarre le processus de création de profil guidé"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("🚗 Conducteur", callback_data="profile_create:driver")],
        [InlineKeyboardButton("🎒 Passager", callback_data="profile_create:passenger")],
        [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
    ]
    
    text = (
        "👤 *Création de votre profil*\n\n"
        "Choisissez votre rôle principal :\n\n"
        "🚗 *Conducteur*\n"
        "• Proposez vos trajets\n"
        "• Recevez des paiements via PayPal\n"
        "• Gérez vos passagers\n\n"
        "🎒 *Passager*\n"
        "• Recherchez des trajets\n"
        "• Réservez facilement\n"
        "• Payez en ligne\n\n"
        "⚠️ Vous pourrez créer les deux profils si besoin."
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    # Retourner l'état pour démarrer le ConversationHandler d'inscription
    return PROFILE_ROLE_SELECTION

async def show_help_menu(update: Update, context: CallbackContext):
    """Affiche le menu d'aide complet"""
    query = update.callback_query if update.callback_query else None
    
    keyboard = [
        [InlineKeyboardButton("🚗 Aide conducteur", callback_data="help:driver")],
        [InlineKeyboardButton("🎒 Aide passager", callback_data="help:passenger")],
        [InlineKeyboardButton("🤝 Nouveau système", callback_data="help:dual_system")],
        [InlineKeyboardButton("💳 Paiements PayPal", callback_data="help:paypal")],
        [InlineKeyboardButton("❓ FAQ", callback_data="help:faq")],
        [InlineKeyboardButton("📞 Contact", callback_data="help:contact")],
        [InlineKeyboardButton("🔙 Menu principal", callback_data="menu:back_to_main")]
    ]
    
    text = (
        "❓ *Centre d'aide CovoiturageSuisse*\n\n"
        "Sélectionnez le sujet pour lequel vous avez besoin d'aide :\n\n"
        "🚗 **Aide conducteur** - Comment proposer vos services et créer des trajets\n"
        "🎒 **Aide passager** - Comment chercher ET créer des demandes de trajet\n"
        "🤝 **Nouveau système** - Guide complet du système dual-role\n"
        "💳 **Paiements PayPal** - Configuration et gestion des paiements\n"
        "❓ **FAQ** - Questions fréquemment posées\n"
        "📞 **Contact** - Nous contacter pour un support personnalisé"
    )
    
    if query:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    return ConversationHandler.END

async def switch_user_profile(update: Update, context: CallbackContext, profile_type: str):
    """Change le profil actif de l'utilisateur (conducteur/passager) et redirige vers le profil complet"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await query.edit_message_text("❌ Profil utilisateur non trouvé.")
        return ConversationHandler.END
    
    # NOUVEAU: Vérifier PayPal pour tous les profils
    if not user.paypal_email:
        keyboard = [
            [InlineKeyboardButton("💳 Configurer PayPal", callback_data="setup_paypal")],
            [InlineKeyboardButton("❓ Pourquoi PayPal ?", callback_data="why_paypal_required")],
            [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
        ]
        
        role_text = "conducteur" if profile_type == "driver" else "passager"
        
        await query.edit_message_text(
            f"🔒 *Configuration PayPal Requise*\n\n"
            f"Pour activer votre profil {role_text}, vous devez "
            f"configurer votre email PayPal.\n\n"
            f"💡 **Pourquoi PayPal est obligatoire ?**\n"
            f"• Sécurité des transactions\n"
            f"• Remboursements automatiques\n"
            f"• Protection acheteur/vendeur\n\n"
            f"👇 Configurez maintenant :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Vérifier et activer le profil selon le type demandé
    if profile_type == "driver":
        # Vérifier que l'utilisateur a un profil conducteur complet
        if not user.is_driver:
            keyboard = [
                [InlineKeyboardButton("💳 Activer profil conducteur", callback_data="menu:become_driver")],
                [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
            ]
            
            await query.edit_message_text(
                "🚗 *Activation du Mode Conducteur*\n\n"
                "❌ Votre profil conducteur n'est pas activé.\n"
                "Activez-le pour pouvoir créer des trajets et recevoir des passagers.\n\n"
                "💳 PayPal déjà configuré :",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return ConversationHandler.END
    
    # Enregistrer le profil actuel dans context.user_data
    context.user_data['active_profile'] = profile_type
    
    db.close()
    
    # MODIFICATION IMPORTANTE: Rediriger vers le profil complet au lieu d'afficher le mini-profil
    # Afficher un message de confirmation rapide puis rediriger
    role_text = "Conducteur" if profile_type == "driver" else "Passager"
    
    await query.edit_message_text(
        f"✅ *Mode {role_text} Activé*\n\n"
        f"Redirection vers votre profil...",
        parse_mode="Markdown"
    )
    
    # Attendre un petit moment puis rediriger vers le profil complet
    import asyncio
    await asyncio.sleep(1)
    
    # Rediriger vers la fonction profile_handler pour afficher le profil complet
    return await profile_handler(update, context)

async def activate_driver_profile(update: Update, context: CallbackContext):
    """Active le profil conducteur et demande la configuration PayPal"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await query.edit_message_text(
            "❌ Erreur : Profil utilisateur non trouvé.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
            ])
        )
        return ConversationHandler.END
    
    # Activer le profil conducteur
    user.is_driver = True
    db.commit()
    
    # Vérifier si l'utilisateur a déjà un email PayPal
    if user.paypal_email:
        keyboard = [
            [InlineKeyboardButton("🚗 Créer un trajet", callback_data="menu:create")],
            [InlineKeyboardButton("💳 Modifier PayPal", callback_data="setup_paypal")],
            [InlineKeyboardButton("🔙 Menu principal", callback_data="menu:back_to_main")]
        ]
        
        text = (
            "✅ *Profil conducteur activé !*\n\n"
            f"📧 Email PayPal : `{user.paypal_email}`\n\n"
            "Vous pouvez maintenant créer des trajets et recevoir des paiements."
        )
    else:
        keyboard = [
            [InlineKeyboardButton("💳 Configurer PayPal", callback_data="setup_paypal")],
            [InlineKeyboardButton("⏭️ Configurer plus tard", callback_data="menu:back_to_main")]
        ]
        
        text = (
            "✅ *Profil conducteur activé !*\n\n"
            "🔔 *Configuration PayPal recommandée*\n\n"
            "Pour recevoir des paiements automatiques, "
            "configurez votre email PayPal maintenant.\n\n"
            "⚠️ Sans PayPal configuré, vous ne pourrez pas recevoir de paiements automatiques."
        )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# Fonction pour gérer la commande /aide directement
async def aide_command(update: Update, context: CallbackContext):
    """Commande /aide accessible depuis n'importe où"""
    return await show_help_menu(update, context)

async def handle_profile_creation(update: Update, context: CallbackContext):
    """Gère la création de profil selon le rôle choisi"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split(":")[1]  # profile_create:driver ou profile_create:passenger
    
    # Stocker le rôle choisi
    context.user_data['selected_role'] = action
    
    # Demander le nom complet
    await query.edit_message_text(
        f"👤 *Inscription - Étape 1/4*\n\n"
        f"🎯 Rôle choisi : {'🚗 Conducteur' if action == 'driver' else '🎒 Passager'}\n\n"
        f"� **Veuillez entrer votre nom complet :**\n"
        f"(Prénom et nom de famille)\n\n"
        f"💡 Ce nom sera visible par les autres utilisateurs.",
        parse_mode="Markdown"
    )
    
    return PROFILE_NAME_INPUT

async def handle_profile_name_input(update: Update, context: CallbackContext):
    """Gère la saisie du nom complet"""
    user_input = update.message.text.strip()
    
    if len(user_input) < 2:
        await update.message.reply_text(
            "❌ Le nom doit contenir au moins 2 caractères.\n"
            "Veuillez entrer votre nom complet :"
        )
        return PROFILE_NAME_INPUT
    
    context.user_data['full_name'] = user_input
    
    await update.message.reply_text(
        f"👤 *Inscription - Étape 2/4*\n\n"
        f"✅ Nom : {user_input}\n\n"
        f"🎂 **Veuillez entrer votre âge :**\n"
        f"(Entre 18 et 99 ans)\n\n"
        f"💡 Cette information aide à créer la confiance entre utilisateurs.",
        parse_mode="Markdown"
    )
    
    return PROFILE_AGE_INPUT

async def handle_profile_age_input(update: Update, context: CallbackContext):
    """Gère la saisie de l'âge"""
    try:
        age = int(update.message.text.strip())
        if age < 18 or age > 99:
            await update.message.reply_text(
                "❌ L'âge doit être compris entre 18 et 99 ans.\n"
                "Veuillez entrer votre âge :"
            )
            return PROFILE_AGE_INPUT
    except ValueError:
        await update.message.reply_text(
            "❌ Veuillez entrer un nombre valide.\n"
            "Quel est votre âge ?"
        )
        return PROFILE_AGE_INPUT
    
    context.user_data['age'] = age
    
    await update.message.reply_text(
        f"👤 *Inscription - Étape 3/4*\n\n"
        f"✅ Nom : {context.user_data['full_name']}\n"
        f"✅ Âge : {age} ans\n\n"
        f"📱 **Veuillez entrer votre numéro de téléphone :**\n"
        f"(Format : +41 79 123 45 67 ou 079 123 45 67)\n\n"
        f"💡 Nécessaire pour les confirmations de trajet.",
        parse_mode="Markdown"
    )
    
    return PROFILE_PHONE_INPUT

async def handle_profile_phone_input(update: Update, context: CallbackContext):
    """Gère la saisie du téléphone"""
    phone = update.message.text.strip()
    
    # Validation basique du numéro de téléphone
    if len(phone) < 10 or not any(char.isdigit() for char in phone):
        await update.message.reply_text(
            "❌ Format de téléphone invalide.\n"
            "Veuillez entrer un numéro valide (ex: +41 79 123 45 67) :"
        )
        return PROFILE_PHONE_INPUT
    
    context.user_data['phone'] = phone
    selected_role = context.user_data.get('selected_role', 'passenger')
    
    # NOUVEAU: PayPal obligatoire pour TOUS (conducteurs ET passagers)
    keyboard = [
        [InlineKeyboardButton("📧 Entrer mon adresse email PayPal", callback_data="paypal_input_start")],
        [InlineKeyboardButton("🆕 Créer un compte PayPal", url="https://www.paypal.com/ch/webapps/mpp/account-selection")],
        [InlineKeyboardButton("❓ Pourquoi PayPal est obligatoire ?", callback_data="why_paypal_required")]
    ]
    
    role_text = "Conducteur" if selected_role == 'driver' else "Passager"
    
    await update.message.reply_text(
        f"👤 *Inscription - Étape 4/4*\n\n"
        f"✅ Nom : {context.user_data['full_name']}\n"
        f"✅ Âge : {context.user_data['age']} ans\n"
        f"✅ Téléphone : {phone}\n\n"
        f"💳 **Configuration PayPal ({role_text})**\n\n"
        f"Pour garantir la sécurité des transactions, PayPal est obligatoire pour tous les utilisateurs :\n\n"
        f"• **Conducteurs** : Recevoir les paiements automatiques (88% du montant)\n"
        f"• **Passagers** : Recevoir les remboursements en cas d'annulation\n\n"
        f"� **Sécurité garantie** : Protection acheteur/vendeur PayPal\n\n"
        f"👇 **Choisissez une option :**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PROFILE_PAYPAL_INPUT

async def handle_paypal_input_start(update: Update, context: CallbackContext):
    """Gère le clic sur le bouton 'Entrer mon adresse email PayPal'"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"💳 **Configuration PayPal - Étape finale**\n\n"
        f"📧 **Veuillez entrer votre adresse email PayPal :**\n\n"
        f"💡 Assurez-vous que :\n"
        f"• L'email est correctement écrit\n"
        f"• C'est bien votre email PayPal principal\n"
        f"• Votre compte PayPal est actif\n\n"
        f"⚠️ Cette adresse sera utilisée pour recevoir les paiements.",
        parse_mode="Markdown"
    )
    
    return PROFILE_PAYPAL_INPUT

async def handle_why_paypal_required(update: Update, context: CallbackContext):
    """Explique pourquoi PayPal est obligatoire pour tous"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📧 Configurer PayPal maintenant", callback_data="paypal_input_start")],
        [InlineKeyboardButton("🔙 Retour", callback_data="back_to_phone_input")]
    ]
    
    await query.edit_message_text(
        "💡 *Pourquoi PayPal est obligatoire ?*\n\n"
        "**🔒 Sécurité pour tous :**\n"
        "• Protection acheteur/vendeur PayPal\n"
        "• Transactions 100% sécurisées\n"
        "• Historique complet des paiements\n\n"
        "**💰 Avantages conducteurs :**\n"
        "• Paiements automatiques (88% du montant)\n"
        "• Pas de gestion d'argent liquide\n"
        "• Commission plateforme (12%) prélevée automatiquement\n\n"
        "**🛡️ Avantages passagers :**\n"
        "• Remboursements automatiques en cas d'annulation\n"
        "• Protection en cas de litige\n"
        "• Paiements en un clic, pas de liquide\n\n"
        "🎯 **Résultat :** Covoiturage 100% digital et sécurisé !",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PROFILE_PAYPAL_INPUT

async def handle_profile_paypal_input(update: Update, context: CallbackContext):
    """Gère la saisie de l'email PayPal pour les conducteurs"""
    email = update.message.text.strip()
    
    # Validation basique de l'email
    if '@' not in email or '.' not in email:
        await update.message.reply_text(
            "❌ Format d'email invalide.\n"
            "Veuillez entrer une adresse email PayPal valide :"
        )
        return PROFILE_PAYPAL_INPUT
    
    context.user_data['paypal_email'] = email
    
    return await complete_profile_creation(update, context)

async def complete_profile_creation(update: Update, context: CallbackContext):
    """Finalise la création du profil avec toutes les informations"""
    user_id = update.effective_user.id
    user_data = update.effective_user
    selected_role = context.user_data.get('selected_role', 'passenger')
    
    db = get_db()
    
    # Créer le profil utilisateur complet
    new_user = User(
        telegram_id=user_id,
        full_name=context.user_data['full_name'],
        username=user_data.username,
        age=context.user_data['age'],
        phone=context.user_data['phone'],
        paypal_email=context.user_data.get('paypal_email') or None,
        is_driver=(selected_role == "driver"),
        is_passenger=True  # Tous les utilisateurs peuvent être passagers
    )
    
    db.add(new_user)
    db.commit()
    
    # Message de succès personnalisé
    if selected_role == 'driver':
        keyboard = [
            [InlineKeyboardButton("🚗 Créer mon premier trajet", callback_data="menu:create")],
            [InlineKeyboardButton("👤 Voir mon profil", callback_data="menu:profile")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
        ]
        
        text = (
            f"🎉 *Profil conducteur créé avec succès !*\n\n"
            f"👋 Bienvenue {new_user.full_name} !\n\n"
            f"✅ **Votre profil :**\n"
            f"• Nom : {new_user.full_name}\n"
            f"• Âge : {new_user.age} ans\n"
            f"• Téléphone : {new_user.phone}\n"
            f"• PayPal : {new_user.paypal_email}\n\n"
            f"🚗 **Vous pouvez maintenant :**\n"
            f"• Créer des trajets\n"
            f"• Recevoir des paiements automatiques\n"
            f"• Gérer vos passagers\n\n"
            f"Prêt à proposer votre premier trajet ?"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🔍 Chercher un trajet", callback_data="menu:search_trip")],
            [InlineKeyboardButton("👤 Voir mon profil", callback_data="menu:profile")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
        ]
        
        text = (
            f"🎉 *Profil passager créé avec succès !*\n\n"
            f"👋 Bienvenue {new_user.full_name} !\n\n"
            f"✅ **Votre profil :**\n"
            f"• Nom : {new_user.full_name}\n"
            f"• Âge : {new_user.age} ans\n"
            f"• Téléphone : {new_user.phone}\n\n"
            f"🎒 **Vous pouvez maintenant :**\n"
            f"• Rechercher des trajets\n"
            f"• Réserver des places\n"
            f"• Payer en ligne\n\n"
            f"Prêt à partir à l'aventure ?"
        )
    
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    # Nettoyer les données temporaires
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_profile_creation(update: Update, context: CallbackContext):
    """Annule la création de profil"""
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ Création de profil annulée.\n\n"
            "Vous pouvez recommencer à tout moment avec /start"
        )
    else:
        await update.message.reply_text(
            "❌ Création de profil annulée.\n\n"
            "Vous pouvez recommencer à tout moment avec /start"
        )
    
    return ConversationHandler.END

async def handle_help_callbacks(update: Update, context: CallbackContext):
    """Gère les callbacks d'aide contextuelle"""
    query = update.callback_query
    await query.answer()
    
    help_type = query.data.split(":")[1]  # help:driver, help:passenger, etc.
    
    if help_type == "driver":
        text = (
            "🚗 *Aide Conducteur*\n\n"
            "**💡 NOUVEAU : Deux façons de proposer vos services !**\n\n"
            "**1️⃣ Créer un trajet classique :**\n"
            "• Créer → Conducteur → Définir votre trajet\n"
            "• Les passagers vous trouvent et réservent\n\n"
            "**2️⃣ Répondre aux demandes de passagers :**\n"
            "• Menu → 'Demandes passagers'\n"
            "• Consultez les demandes publiées\n"
            "• Proposez vos services personnalisés\n"
            "• Prix calculé automatiquement par km\n\n"
            "**📋 Étapes pour proposer un service :**\n"
            "1. Sélectionnez une demande de trajet\n"
            "2. Rédigez un message de présentation\n"
            "3. Confirmez votre tarif (prix/km standard)\n"
            "4. Décrivez votre véhicule\n"
            "5. Indiquez le point de ramassage\n"
            "6. Envoyez votre proposition\n\n"
            "**✅ Avantages du nouveau système :**\n"
            "• Plus de flexibilité dans les trajets\n"
            "• Contact direct avec les passagers\n"
            "• Tarification transparente et équitable\n"
            "• Paiement sécurisé via PayPal"
        )
    elif help_type == "passenger":
        text = (
            "🎒 *Aide Passager*\n\n"
            "**💡 NOUVEAU : Trois façons de voyager !**\n\n"
            "**1️⃣ Chercher des trajets existants :**\n"
            "• Chercher → Parcourir les trajets disponibles\n"
            "• Réserver directement en ligne\n\n"
            "**2️⃣ Publier votre demande de trajet :**\n"
            "• Créer → Passager → Publier votre demande\n"
            "• Les conducteurs vous contactent\n"
            "• Choisissez la meilleure proposition\n\n"
            "**3️⃣ Créer un trajet comme passager :**\n"
            "• Précisez que vous cherchez UN conducteur\n"
            "• Les conducteurs voient votre annonce\n"
            "• Ils vous proposent leurs services\n\n"
            "**📋 Comment publier une demande :**\n"
            "1. Créer un trajet en mode 'Passager'\n"
            "2. Indiquez vos villes de départ/arrivée\n"
            "3. Définissez date, heure et flexibilité\n"
            "4. Précisez nombre de places et budget\n"
            "5. Publiez votre demande\n"
            "6. Recevez des propositions de conducteurs\n\n"
            "**🚗 Quand les conducteurs vous contactent :**\n"
            "• Consultez les détails de chaque proposition\n"
            "• Comparez véhicules, horaires et conducteurs\n"
            "• Prix calculé automatiquement par km\n"
            "• Acceptez la meilleure offre\n"
            "• Payez en ligne via PayPal\n"
            "• Contactez votre conducteur\n\n"
            "**✅ Avantages du nouveau système :**\n"
            "• Plus de choix et flexibilité\n"
            "• Prix transparent et équitable\n"
            "• Paiement sécurisé\n"
            "• Contact direct avec conducteurs\n"
            "• Vous n'attendez plus, vous publiez !"
        )
    elif help_type == "dual_system":
        text = (
            "🤝 *Guide du Nouveau Système Dual-Role*\n\n"
            "**🎯 Concept :**\n"
            "CovoiturageSuisse fonctionne maintenant comme une marketplace où passagers et conducteurs peuvent se trouver mutuellement !\n\n"
            "**👥 Pour les PASSAGERS :**\n"
            "✅ Publiez vos demandes de trajet\n"
            "✅ Recevez des propositions personnalisées\n"
            "✅ Choisissez votre conducteur préféré\n"
            "✅ Prix calculé automatiquement par km\n\n"
            "**🚗 Pour les CONDUCTEURS :**\n"
            "✅ Créez vos trajets classiques\n"
            "✅ Consultez les demandes de passagers\n"
            "✅ Proposez vos services sur mesure\n"
            "✅ Tarification transparente et équitable\n\n"
            "**🔄 Processus de matching :**\n"
            "1. Passager publie une demande\n"
            "2. Conducteurs voient la demande\n"
            "3. Conducteurs proposent leurs services\n"
            "4. Passager choisit et accepte\n"
            "5. Paiement automatique via PayPal\n"
            "6. Confirmation et échange de contacts\n\n"
            "**🎯 Résultat :**\n"
            "Plus de trajets, plus de flexibilité, plus de choix pour tous !"
        )
    elif help_type == "paypal":
        text = (
            "💳 *Paiements PayPal*\n\n"
            "**Configuration conducteur :**\n"
            "• Allez dans votre profil\n"
            "• Cliquez sur 'Configurer PayPal'\n"
            "• Entrez votre email PayPal\n"
            "• Activez les paiements automatiques\n\n"
            "**Paiements passager :**\n"
            "• Les paiements se font via PayPal\n"
            "• Sécurisé et instantané\n"
            "• Confirmation automatique\n\n"
            "**Sécurité :**\n"
            "• Vos données sont protégées\n"
            "• Garantie de remboursement PayPal\n"
            "• Support 24h/24"
        )
    elif help_type == "faq":
        text = (
            "❓ *Questions Fréquentes*\n\n"
            "**Q: Quelle est la différence entre créer un trajet conducteur et passager ?**\n"
            "R: Conducteur = vous proposez votre véhicule. Passager = vous cherchez un conducteur et publiez votre demande.\n\n"
            "**Q: Comment les conducteurs voient-ils ma demande de trajet ?**\n"
            "R: Votre demande apparaît dans 'Demandes passagers' du menu principal pour tous les conducteurs.\n\n"
            "**Q: Puis-je négocier le prix avec un conducteur ?**\n"
            "R: Les prix sont calculés automatiquement selon la distance (CHF par km). Pas de négociation nécessaire, tarification équitable pour tous.\n\n"
            "**Q: Que se passe-t-il si plusieurs conducteurs me contactent ?**\n"
            "R: Vous recevez toutes les propositions et choisissez celle qui vous convient le mieux.\n\n"
            "**Q: Comment annuler une demande de trajet ?**\n"
            "R: Allez dans 'Mes trajets' et supprimez votre demande si aucune proposition n'a été acceptée.\n\n"
            "**Q: Le paiement est-il sécurisé ?**\n"
            "R: Oui, tous les paiements passent par PayPal avec protection acheteur.\n\n"
            "**Q: Comment contacter un conducteur après acceptation ?**\n"
            "R: Les coordonnées sont échangées automatiquement après paiement confirmé.\n\n"
            "**Q: Puis-je être à la fois conducteur et passager ?**\n"
            "R: Absolument ! Vous pouvez publier des demandes ET proposer vos services selon vos besoins."
        )
    elif help_type == "contact":
        text = (
            "📞 *Nous Contacter*\n\n"
            "**Support technique :**\n"
            "• Email: support@covoiturage-suisse.ch\n"
            "• Telegram: @CovoiturageSuisseSupport\n\n"
            "**Questions générales :**\n"
            "• Email: contact@covoiturage-suisse.ch\n"
            "• Téléphone: +41 XX XXX XX XX\n\n"
            "**Urgences sécurité :**\n"
            "• Numéro d'urgence: 117 (Police)\n"
            "• Email urgent: urgent@covoiturage-suisse.ch\n\n"
            "**Horaires support :**\n"
            "Lundi-Vendredi: 8h-18h\n"
            "Weekend: 10h-16h"
        )
    else:
        text = "❌ Section d'aide non trouvée."
    
    keyboard = [
        [InlineKeyboardButton("🔙 Retour aide", callback_data="menu:help")],
        [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def handle_profile_created_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gérer les actions après création du profil"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "setup_paypal":
        # Rediriger vers la configuration PayPal
        from handlers.paypal_setup_handler import start_paypal_setup
        return await start_paypal_setup(update, context)
    elif action == "add_vehicle":
        # Rediriger vers l'ajout de véhicule
        from handlers.vehicle_handler import start_vehicle_setup
        return await start_vehicle_setup(update, context)
    elif action == "main_menu":
        # Retourner au menu principal
        from .menu_handlers import show_main_menu
        await show_main_menu(update, context)
        return ConversationHandler.END
    
    return ConversationHandler.END

# ConversationHandler pour la création complète de profil
profile_creation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_profile_creation, pattern=r"^menu:create_profile$"),
    ],
    states={
        PROFILE_ROLE_SELECTION: [
            CallbackQueryHandler(handle_profile_creation, pattern=r"^profile_create:(driver|passenger)$"),
            CallbackQueryHandler(cancel_profile_creation, pattern=r"^menu:back_to_main$")
        ],
        PROFILE_NAME_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profile_name_input),
            CommandHandler("cancel", cancel_profile_creation)
        ],
        PROFILE_AGE_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profile_age_input),
            CommandHandler("cancel", cancel_profile_creation)
        ],
        PROFILE_PHONE_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profile_phone_input),
            CommandHandler("cancel", cancel_profile_creation)
        ],
        PROFILE_PAYPAL_INPUT: [
            CallbackQueryHandler(handle_paypal_input_start, pattern=r"^paypal_input_start$"),
            CallbackQueryHandler(handle_why_paypal_required, pattern=r"^why_paypal_required$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profile_paypal_input),
            CommandHandler("cancel", cancel_profile_creation)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel_profile_creation),
        CallbackQueryHandler(cancel_profile_creation, pattern=r"^menu:back_to_main$")
    ],
    name="profile_creation",
    persistent=True,
    allow_reentry=True,
    per_message=False
)
