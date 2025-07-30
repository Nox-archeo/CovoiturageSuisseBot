
# NOUVELLE LOGIQUE: PayPal obligatoire pour tous les rôles
async def handle_profile_phone_input(update: Update, context: CallbackContext):
    """Gère la saisie du téléphone avec PayPal obligatoire pour tous"""
    phone = update.message.text.strip()
    
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
        f"🔒 **Sécurité garantie** : Protection acheteur/vendeur PayPal\n\n"
        f"👇 **Choisissez une option :**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PROFILE_PAYPAL_INPUT
