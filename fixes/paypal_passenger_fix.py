
# NOUVELLE LOGIQUE: PayPal obligatoire pour passagers aussi
async def handle_become_passenger(update: Update, context: CallbackContext):
    """Gère l'activation du profil passager avec PayPal obligatoire"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "become_passenger":
        user_id = query.from_user.id
        db = get_db()
        user = db.query(User).filter_by(telegram_id=user_id).first()
        
        if user:
            user.is_passenger = True
            db.commit()
            logger.info(f"Utilisateur {user_id} est devenu passager")
            
            # NOUVEAU: Vérifier PayPal pour passagers aussi
            if user.paypal_email:
                await query.edit_message_text(
                    "✅ *Profil passager activé!*\n\n"
                    f"📧 PayPal configuré : `{user.paypal_email}`\n\n"
                    "Vous pouvez maintenant créer des demandes de trajet.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return await start_departure_selection(update, context)
            else:
                # Demander la configuration PayPal pour les passagers
                keyboard = [
                    [InlineKeyboardButton("💳 Configurer PayPal", callback_data="setup_paypal")],
                    [InlineKeyboardButton("❓ Pourquoi PayPal ?", callback_data="why_paypal_passenger")]
                ]
                
                await query.edit_message_text(
                    "✅ *Profil passager activé!*\n\n"
                    "💳 *Configuration PayPal requise*\n\n"
                    "Pour garantir la sécurité des transactions et permettre "
                    "les remboursements automatiques en cas d'annulation, "
                    "vous devez configurer votre email PayPal.\n\n"
                    "⚠️ Sans PayPal, vous ne pourrez pas recevoir de remboursements "
                    "automatiques ni utiliser la protection acheteur.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                context.user_data['next_state_after_paypal'] = "DEPARTURE"
                return "PAYPAL_SETUP"
