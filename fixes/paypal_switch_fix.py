
# NOUVELLE LOGIQUE: Vérifier PayPal lors du switch
async def switch_user_profile(update: Update, context: CallbackContext, profile_type: str):
    """Change le profil actif avec vérification PayPal obligatoire"""
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
    
    # Continuer avec la logique normale si PayPal est configuré
    context.user_data['active_profile'] = profile_type
    # ... reste de la fonction ...
