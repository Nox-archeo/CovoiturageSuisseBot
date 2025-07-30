async def handle_show_trips_by_time_new(update: Update, context: CallbackContext):
    """Affiche les trajets selon le choix temporel avec boutons individuels pour chaque trajet"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Parser le callback : trips:show_driver_future ou trips:show_passenger_past
        callback_data = query.data
        parts = callback_data.split("_")
        
        if len(parts) < 3:
            raise ValueError(f"Format de callback invalide: {callback_data}")
            
        user_type = parts[1]  # driver ou passenger
        time_period = parts[2]  # future ou past
        
        logger.info(f"Affichage {user_type} - période: {time_period}")
        
        user_id = update.effective_user.id
        db = get_db()
        
        # Trouver l'utilisateur
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            await query.edit_message_text(
                "⚠️ Utilisateur non trouvé. Veuillez utiliser /start pour créer votre profil.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")
                ]])
            )
            return

        now = datetime.now()
        
        if user_type == "driver":
            # Trajets conducteur
            if time_period == "future":
                trips = db.query(Trip).filter(
                    Trip.driver_id == user.id,
                    Trip.is_cancelled != True,
                    Trip.departure_time > now
                ).order_by(Trip.departure_time.asc()).all()
                
                title = "📅 À venir"
                empty_message = (
                    "🚗 *Trajets à venir (Conducteur)*\n\n"
                    "Aucun trajet à venir pour le moment.\n\n"
                    "💡 Créez un nouveau trajet pour commencer !"
                )
                
            else:  # past
                trips = db.query(Trip).filter(
                    Trip.driver_id == user.id,
                    Trip.departure_time <= now
                ).order_by(Trip.departure_time.desc()).all()
                
                title = "🕓 Passés"
                empty_message = (
                    "🚗 *Trajets passés (Conducteur)*\n\n"
                    "Aucun trajet passé trouvé.\n\n"
                    "💡 Vos trajets terminés apparaîtront ici."
                )
            
            if not trips:
                keyboard = [
                    [InlineKeyboardButton("➕ Créer un trajet", callback_data="menu:create")],
                    [InlineKeyboardButton("🔙 Retour", callback_data=f"trips:list_{user_type}")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
                ]
                
                await query.edit_message_text(
                    empty_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return
                
            # Header message
            header_message = f"🚗 *{title} (Conducteur)*\n\n📊 {len(trips)} trajet(s) trouvé(s)"
            await query.edit_message_text(header_message, parse_mode="Markdown")
            
            # Envoyer chaque trajet avec ses boutons individuels
            for trip in trips:
                departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
                
                # Compter les réservations
                booking_count = db.query(Booking).filter(
                    Booking.trip_id == trip.id, 
                    Booking.status.in_(["pending", "confirmed", "completed"])
                ).count()
                
                # Icône selon l'état
                icon = "🚗" if time_period == "future" else "🏁"
                
                trip_message = (
                    f"{icon} {trip.departure_city} → {trip.arrival_city}\n"
                    f"📅 {departure_date}\n"
                    f"💰 {trip.price_per_seat:.2f} CHF/place • 💺 {booking_count}/{trip.seats_available}"
                )
                
                # Boutons individuels pour CE trajet spécifique
                if time_period == "future":
                    trip_buttons = [
                        [InlineKeyboardButton("✏️ Modifier", callback_data=f"trip:edit:{trip.id}")],
                        [InlineKeyboardButton("🗑 Supprimer", callback_data=f"trip:delete:{trip.id}")],
                        [InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip.id}")]
                    ]
                else:
                    trip_buttons = [
                        [InlineKeyboardButton("👁️ Détails", callback_data=f"trip:view:{trip.id}")],
                        [InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip.id}")]
                    ]
                
                # Envoyer ce trajet avec SES boutons juste en dessous
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=trip_message,
                    reply_markup=InlineKeyboardMarkup(trip_buttons),
                    parse_mode="Markdown"
                )
            
        else:  # passenger
            # Même logique pour les passagers mais avec les réservations
            if time_period == "future":
                bookings = db.query(Booking).join(Trip).filter(
                    Booking.passenger_id == user.id,
                    Trip.departure_time > now
                ).order_by(Trip.departure_time.asc()).all()
                
                title = "📅 À venir"
                empty_message = (
                    "🎒 *Réservations à venir (Passager)*\n\n"
                    "Aucune réservation à venir pour le moment.\n\n"
                    "💡 Recherchez un trajet pour voyager !"
                )
                
            else:  # past
                bookings = db.query(Booking).join(Trip).filter(
                    Booking.passenger_id == user.id,
                    Trip.departure_time <= now
                ).order_by(Trip.departure_time.desc()).all()
                
                title = "🕓 Passés"
                empty_message = (
                    "🎒 *Réservations passées (Passager)*\n\n"
                    "Aucune réservation passée trouvée.\n\n"
                    "💡 Vos voyages terminés apparaîtront ici."
                )
            
            if not bookings:
                keyboard = [
                    [InlineKeyboardButton("🔍 Chercher un trajet", callback_data="menu:search_trip")],
                    [InlineKeyboardButton("🔙 Retour", callback_data=f"trips:list_{user_type}")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
                ]
                
                await query.edit_message_text(
                    empty_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return
                
            # Header message
            header_message = f"🎒 *{title} (Passager)*\n\n📊 {len(bookings)} réservation(s) trouvée(s)"
            await query.edit_message_text(header_message, parse_mode="Markdown")
            
            # Envoyer chaque réservation avec ses boutons individuels
            for booking in bookings:
                trip = booking.trip
                departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
                
                status_map = {
                    "pending": "⏳ En attente",
                    "confirmed": "✅ Confirmée", 
                    "cancelled": "❌ Annulée",
                    "completed": "🏁 Terminée"
                }
                status = status_map.get(booking.status, "❓ Inconnu")
                
                # Icône selon l'état
                icon = "🎒" if time_period == "future" else "🏁"
                
                booking_message = (
                    f"{icon} {trip.departure_city} → {trip.arrival_city}\n"
                    f"📅 {departure_date}\n"
                    f"💰 {booking.amount:.2f} CHF • 💺 {booking.seats} place(s)\n"
                    f"📊 {status}"
                )
                
                # Boutons individuels pour CETTE réservation
                if time_period == "future" and booking.status in ["pending", "confirmed"]:
                    booking_buttons = [
                        [InlineKeyboardButton("👁️ Détails", callback_data=f"booking:view:{booking.id}")],
                        [InlineKeyboardButton("❌ Annuler", callback_data=f"booking:cancel:{booking.id}")],
                        [InlineKeyboardButton("🚩 Signaler", callback_data=f"booking:report:{booking.id}")]
                    ]
                else:
                    booking_buttons = [
                        [InlineKeyboardButton("👁️ Détails", callback_data=f"booking:view:{booking.id}")],
                        [InlineKeyboardButton("🚩 Signaler", callback_data=f"booking:report:{booking.id}")]
                    ]
                
                # Envoyer cette réservation avec SES boutons juste en dessous
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=booking_message,
                    reply_markup=InlineKeyboardMarkup(booking_buttons),
                    parse_mode="Markdown"
                )
        
        # Boutons de navigation finale
        nav_buttons = [
            [InlineKeyboardButton("🔙 Retour", callback_data=f"trips:list_{user_type}")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
        ]
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="─────────────────",
            reply_markup=InlineKeyboardMarkup(nav_buttons)
        )
        
    except Exception as e:
        logger.error(f"Erreur dans handle_show_trips_by_time: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Une erreur est survenue lors de l'affichage de vos trajets.\n\n"
            "Veuillez réessayer ou contacter le support si le problème persiste.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="menu:my_trips")],
                [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_main")]
            ])
        )
