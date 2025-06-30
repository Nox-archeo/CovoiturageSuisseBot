# Ancien fichier Stripe - désactivé car plus utilisé
# Ce fichier était utilisé pour la gestion des abonnements via Stripe
# Il a été désactivé car le système utilise maintenant PayPal uniquement

def register(application):
    """Fonction de register vide - Stripe désactivé"""
    pass

def check_subscription(user_id: int) -> bool:
    """Vérifie l'abonnement de l'utilisateur - Retourne toujours True car plus d'abonnement"""
    return True

def is_premium(user_id: int) -> bool:
    """Vérifie si l'utilisateur est premium - Retourne toujours True car plus d'abonnement"""
    return True

# Note: Tout le code Stripe a été retiré car plus utilisé
# Si vous souhaitez réactiver Stripe à l'avenir, 
# consultez l'historique git pour récupérer le code original
    application.add_handler(CallbackQueryHandler(create_subscription, pattern="^create_subscription$"))
    
    # Handler pour les callbacks de succès/échec de l'abonnement
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("Abonnement activé!"), pattern="^sub_success$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("Abonnement annulé."), pattern="^sub_cancel$"))
