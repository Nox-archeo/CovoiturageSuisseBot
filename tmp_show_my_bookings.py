async def show_my_bookings(update: Update, context: CallbackContext):
    """
    Affiche la liste des réservations de l'utilisateur
    """
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Ajouter un caractère invisible à la fin pour forcer la mise à jour
        refresh_token = f"\u200B{datetime.now().microsecond}"
        
        if not user:
            await query.edit_message_text(
                f"⚠️ Utilisateur non trouvé.{refresh_token}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]])
            )
            return PROFILE_MAIN
        
        # Récupérer les réservations (confirmées et à venir)
        bookings = db.query(Booking).filter(
            Booking.passenger_id == user.id,
            Booking.status.in_(['confirmed', 'pending']),
        ).join(Trip).filter(
            Trip.departure_time > datetime.now()
        ).order_by(Trip.departure_time).all()
        
        if not bookings:
            message = f"🎫 *Mes Réservations*\n\nVous n'avez aucune réservation active.{refresh_token}"
        else:
            message = f"🎫 *Mes Réservations*\n\n"
            for booking in bookings:
                trip = booking.trip
                departure_date = trip.departure_time.strftime("%d/%m/%Y %H:%M")
                
                try:
                    status = "✅ Confirmée" if booking.status == 'confirmed' else "⏳ En attente"
                    
                    # Gérer de façon sécurisée l'accès à is_paid qui pourrait ne pas exister
                    payment = "💸 Paiement requis"
                    try:
                        if hasattr(booking, 'is_paid') and booking.is_paid:
                            payment = "💰 Payée"
                    except Exception as payment_error:
                        logger.error(f"Erreur lors de l'accès à booking.is_paid: {str(payment_error)}")
                    
                    # Gérer de façon sécurisée l'accès à seats qui pourrait ne pas exister
                    num_seats = 1  # Valeur par défaut
                    try:
                        if hasattr(booking, 'seats') and booking.seats is not None:
                            num_seats = booking.seats
                    except Exception as seats_error:
                        logger.error(f"Erreur lors de l'accès à booking.seats: {str(seats_error)}")
                    
                    # Gérer le nom du conducteur de façon sécurisée
                    driver_name = "N/A"
                    if (trip.driver and 
                        hasattr(trip.driver, 'full_name') and 
                        trip.driver.full_name):
                        driver_name = trip.driver.full_name
                    
                    message += (
                        f"• *{trip.departure_city} → {trip.arrival_city}*\n"
                        f"  📅 {departure_date}\n"
                        f"  🚗 Conducteur: {driver_name}\n"
                        f"  💺 {num_seats} place(s)\n"
                        f"  {status} - {payment}\n\n"
                    )
                except Exception as e:
                    logger.error(f"Erreur lors de l'affichage de la réservation: {str(e)}")
                    # Message minimal en cas d'erreur
                    message += (
                        f"• *{trip.departure_city} → {trip.arrival_city}*\n"
                        f"  📅 {departure_date}\n"
                        f"  {booking.status if hasattr(booking, 'status') else 'Statut inconnu'}\n\n"
                    )
            
            message += f"{refresh_token}"
        
        keyboard = [
            [InlineKeyboardButton("🔍 Rechercher un trajet", callback_data="menu:search_trip")],
            [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return PROFILE_MAIN
        
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message identique ignoré: %s", str(e))
            return PROFILE_MAIN
        else:
            logger.error(f"Erreur BadRequest dans show_my_bookings: {str(e)}")
            try:
                await query.edit_message_text(
                    f"⚠️ Une erreur est survenue lors de l'affichage de vos réservations. Veuillez réessayer.\n\u200B{datetime.now().microsecond}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
                )
            except Exception as e2:
                logger.error(f"Erreur secondaire dans show_my_bookings: {str(e2)}")
            return PROFILE_MAIN
    except Exception as e:
        logger.error(f"Erreur dans show_my_bookings: {str(e)}")
        try:
            await query.edit_message_text(
                f"⚠️ Une erreur est survenue lors de l'affichage de vos réservations. Veuillez réessayer.\n\u200B{datetime.now().microsecond}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
            )
        except Exception as e2:
            logger.error(f"Erreur secondaire dans show_my_bookings: {str(e2)}")
        return PROFILE_MAIN
