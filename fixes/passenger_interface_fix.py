
# NOUVELLE INTERFACE: Gestion complète des trajets passagers
async def show_passenger_trip_management(update: Update, context: CallbackContext):
    """Affiche l'interface de gestion des trajets passagers avec toutes les options"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await query.edit_message_text("⚠️ Utilisateur non trouvé.")
            return PROFILE_MAIN
        
        # Récupérer les trajets passagers (demandes)
        passenger_trips = db.query(Trip).filter(
            Trip.creator_id == user.id,
            Trip.trip_role == "passenger"
        ).order_by(Trip.departure_time.desc()).all()
        
        if not passenger_trips:
            message = (
                "🎒 *Mes Trajets Passager*\n\n"
                "❌ Aucune demande de trajet créée.\n\n"
                "💡 Créez votre première demande de trajet !"
            )
            keyboard = [
                [InlineKeyboardButton("➕ Créer une demande", callback_data="menu:create")],
                [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
            ]
        else:
            message = "🎒 *Mes Trajets Passager*\n\n"
            keyboard = []
            
            for trip in passenger_trips[:5]:  # Limiter à 5 trajets
                status_emoji = "🟢" if not getattr(trip, 'is_cancelled', False) else "🔴"
                trip_text = f"{status_emoji} {trip.departure_city} → {trip.arrival_city}"
                if hasattr(trip, 'departure_time'):
                    trip_text += f"\n📅 {trip.departure_time.strftime('%d/%m à %H:%M')}"
                
                message += f"\n{trip_text}\n"
                
                # Boutons pour chaque trajet
                trip_keyboard = [
                    InlineKeyboardButton("✏️ Modifier", callback_data=f"edit_passenger_trip:{trip.id}"),
                    InlineKeyboardButton("🗑️ Supprimer", callback_data=f"delete_passenger_trip:{trip.id}"),
                    InlineKeyboardButton("🚨 Signaler", callback_data=f"report_passenger_trip:{trip.id}")
                ]
                keyboard.append(trip_keyboard)
            
            # Boutons généraux
            keyboard.extend([
                [InlineKeyboardButton("➕ Nouvelle demande", callback_data="menu:create")],
                [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
            ])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return PROFILE_MAIN
        
    except Exception as e:
        logger.error(f"Erreur dans show_passenger_trip_management: {e}")
        await query.edit_message_text(
            "⚠️ Erreur lors de l'affichage des trajets passagers.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Retour", callback_data="profile:back_to_profile")
            ]])
        )
        return PROFILE_MAIN

async def handle_passenger_trip_action(update: Update, context: CallbackContext):
    """Gère les actions sur les trajets passagers (edit/delete/report)"""
    query = update.callback_query
    await query.answer()
    
    action_data = query.data
    action, trip_id = action_data.split(":")
    trip_id = int(trip_id)
    
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        await query.edit_message_text("❌ Trajet non trouvé.")
        return PROFILE_MAIN
    
    if action == "edit_passenger_trip":
        # Rediriger vers l'édition de trajet passager
        keyboard = [
            [InlineKeyboardButton("📍 Modifier départ", callback_data=f"edit_trip_departure:{trip_id}")],
            [InlineKeyboardButton("🎯 Modifier arrivée", callback_data=f"edit_trip_arrival:{trip_id}")],
            [InlineKeyboardButton("📅 Modifier date/heure", callback_data=f"edit_trip_datetime:{trip_id}")],
            [InlineKeyboardButton("👥 Modifier nb passagers", callback_data=f"edit_trip_passengers:{trip_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="profile:my_trips")]
        ]
        
        await query.edit_message_text(
            f"✏️ *Modifier le trajet passager*\n\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Que souhaitez-vous modifier ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif action == "delete_passenger_trip":
        # Demander confirmation de suppression
        keyboard = [
            [InlineKeyboardButton("❌ Confirmer suppression", callback_data=f"confirm_delete_passenger:{trip_id}")],
            [InlineKeyboardButton("⬅️ Annuler", callback_data="profile:my_trips")]
        ]
        
        await query.edit_message_text(
            f"🗑️ *Supprimer le trajet passager*\n\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"⚠️ **Attention !** Cette action est irréversible.\n\n"
            f"Voulez-vous vraiment supprimer cette demande de trajet ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif action == "report_passenger_trip":
        # Interface de signalement
        keyboard = [
            [InlineKeyboardButton("🚨 Problème de sécurité", callback_data=f"report_safety:{trip_id}")],
            [InlineKeyboardButton("💰 Problème de paiement", callback_data=f"report_payment:{trip_id}")],
            [InlineKeyboardButton("📞 Problème de contact", callback_data=f"report_contact:{trip_id}")],
            [InlineKeyboardButton("❓ Autre problème", callback_data=f"report_other:{trip_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="profile:my_trips")]
        ]
        
        await query.edit_message_text(
            f"🚨 *Signaler un problème*\n\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\n\n"
            f"Quel type de problème souhaitez-vous signaler ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    return PROFILE_MAIN
