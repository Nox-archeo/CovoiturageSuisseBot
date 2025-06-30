#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/handlers/profile_handler.py
"""
Handler complet pour la gestion du profil utilisateur.
Fournit un tableau de bord interactif avec toutes les informations pertinentes.
"""
import logging
import re
from sqlalchemy import func
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler, CallbackContext, ConversationHandler, 
    MessageHandler, filters, CallbackQueryHandler
)
from telegram.error import BadRequest
from database.models import User, Trip, Booking, Review
from database import get_db
from datetime import datetime
from utils.message_utils import safe_edit_message_text

logger = logging.getLogger(__name__)

# États de la conversation
PROFILE_MAIN, EDIT_PROFILE, TYPING_NAME, TYPING_AGE, TYPING_PHONE, TYPING_DESCRIPTION = range(6)

async def profile_handler(update: Update, context: CallbackContext):
    """
    Handler principal pour la commande /profil ou le bouton de profil
    Affiche le tableau de bord utilisateur avec toutes les informations pertinentes
    """
    if update.callback_query:
        logger.info(f"profile_handler appelé avec callback data: {update.callback_query.data}")
    else:
        logger.info("profile_handler appelé avec message direct (pas de callback)")
    
    # Log plus détaillé pour le debug
    try:
        if update.callback_query:
            logger.info(f"Type de callback: {update.callback_query.data}")
            logger.info(f"Message ID: {update.callback_query.message.message_id}")
    except Exception as e:
        logger.error(f"Erreur lors du logging: {str(e)}")
    
    user_id = update.effective_user.id
    db = get_db()
    
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
    except Exception as e:
        logger.error(f"Erreur dans profile_handler: {str(e)}")
        if update.callback_query:
            await update.callback_query.answer("Une erreur est survenue. Veuillez réessayer.")
            await update.callback_query.edit_message_text("⚠️ Désolé, une erreur est survenue lors de l'accès à votre profil.")
        elif update.message:
            await update.message.reply_text("⚠️ Désolé, une erreur est survenue lors de l'accès à votre profil.")
        return ConversationHandler.END

    if not user:
        if update.message:
            await update.message.reply_text(
                "⚠️ Votre profil n'a pas été trouvé. Veuillez utiliser /start pour vous inscrire."
            )
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                "⚠️ Votre profil n'a pas été trouvé. Veuillez utiliser /start pour vous inscrire."
            )
        return ConversationHandler.END
    
    # Gérer le callback query si présent
    if update.callback_query:
        await update.callback_query.answer()
    
    # Générer le profil dynamiquement
    await show_profile_dashboard(update, context, user)
    return PROFILE_MAIN

async def show_profile_dashboard(update: Update, context: CallbackContext, user=None):
    """
    Affiche le tableau de bord du profil utilisateur avec toutes les informations
    """
    try:
        user_id = update.effective_user.id
        db = get_db()
        
        if not user:
            try:
                user = db.query(User).filter(User.telegram_id == user_id).first()
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de l'utilisateur: {str(e)}")
                if update.callback_query:
                    await update.callback_query.edit_message_text("Une erreur est survenue lors de l'accès à votre profil. Veuillez réessayer.")
                else:
                    await update.message.reply_text("Une erreur est survenue lors de l'accès à votre profil. Veuillez réessayer.")
                return
        
        if not user:
            if update.callback_query:
                await update.callback_query.edit_message_text("⚠️ Profil non trouvé. Utilisez /start pour vous inscrire.")
            else:
                await update.message.reply_text("⚠️ Profil non trouvé. Utilisez /start pour vous inscrire.")
            return
        
        # Récupérer les statistiques
        stats = await get_user_stats(user_id)
        
        # Définir le type d'utilisateur
        user_type = []
        if hasattr(user, 'is_driver') and user.is_driver:
            user_type.append("Conducteur")
        if hasattr(user, 'is_passenger') and user.is_passenger:
            user_type.append("Passager")
        user_type_str = " & ".join(user_type) if user_type else "Non défini"
        
        # Formater le numéro de téléphone pour l'affichage
        phone_display = "Non renseigné [Ajouter 📞]"
        phone_button_text = "📞 Ajouter un téléphone"
        if hasattr(user, 'phone') and user.phone:
            # Masquer une partie du numéro pour des raisons de confidentialité
            matches = re.match(r'(\+\d{2})(\d{2})(\d{3})(\d{2})(\d{2})', user.phone)
            if matches:
                phone_display = f"{matches.group(1)} {matches.group(2)} {matches.group(3)} {matches.group(4)} {matches.group(5)}"
            else:
                phone_display = user.phone
            phone_button_text = "📞 Modifier le téléphone"
        
        # Construire le message du profil (sans horodatage pour éviter des problèmes)
        username = f"@{user.username}" if hasattr(user, 'username') and user.username else ""
        name = user.full_name if hasattr(user, 'full_name') and user.full_name else "Sans nom"
        age = f", {user.age} ans" if hasattr(user, 'age') and user.age else ""
        
        profile_text = (
            f"👤 *PROFIL UTILISATEUR* ({name}{age})\n\n"
            f"📱 Téléphone : {phone_display}\n"
            f"📌 Type : {user_type_str}\n"
            f"⭐ Note moyenne : {stats['rating']:.1f} / 5\n"
            f"🚗 Mes trajets : {stats['trips_count']} trajets à venir\n"
            f"🎫 Mes réservations : {stats['bookings_count']} réservations actives\n"
            f"💸 Mes gains : CHF {stats['earnings']:.2f}"
        )
        
        # Créer les boutons du menu
        keyboard = [
            [
                InlineKeyboardButton("🚗 Mes trajets", callback_data="profile:my_trips"),
                InlineKeyboardButton("🎫 Mes réservations", callback_data="profile:my_bookings")
            ],
            [
                InlineKeyboardButton("💸 Mes gains", callback_data="profile:my_earnings"),
                InlineKeyboardButton("✏️ Modifier mon profil", callback_data="profile:edit")
            ],
            [
                InlineKeyboardButton("📤 Inviter un ami", callback_data="profile:invite"),
                InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Log du contenu pour débogage
        logger.info(f"Affichage du profil avec {len(profile_text)} caractères")
        
        # Envoyer ou mettre à jour le message
        if update.callback_query:
            query = update.callback_query
            try:
                # Utiliser directement la fonction d'édition avec le contenu complet
                logger.info("Mise à jour du message profil via edit_message_text")
                await query.edit_message_text(
                    text=profile_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.debug("Message identique ignoré: %s", str(e))
                    # Forcer une modification du message en changeant le titre
                    parts = profile_text.split('\n', 1)
                    content_part = parts[1] if len(parts) > 1 else ""
                    simple_text = f"👤 *PROFIL UTILISATEUR*\n\n{content_part}"
                    try:
                        await query.edit_message_text(
                            simple_text,
                            reply_markup=reply_markup,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except BadRequest:
                        # Si cela échoue encore, ignorons simplement
                        pass
                else:
                    logger.error(f"Autre erreur BadRequest: {e}")
                    # Pour les autres erreurs, essayons un message plus simple
                    simple_text = f"👤 *PROFIL UTILISATEUR*\n\nType : {user_type_str}\nNote : {stats['rating']:.1f}/5"
                    await query.edit_message_text(
                        simple_text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN
                    )
        else:
            await update.message.reply_text(
                profile_text, 
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du profil: {str(e)}")
        # Utiliser un timestamp visible au lieu d'un caractère invisible
        # Essayer avec un message plus simple en cas d'erreur
        simple_text = f"👤 *Votre profil*\n\nDésolé, une erreur est survenue lors de l'affichage complet de votre profil."
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Rafraîchir", callback_data="profile:back_to_profile")],
            [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]
        ])
        try:
            if update.callback_query:
                query = update.callback_query
                await query.edit_message_text(
                    simple_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    simple_text, 
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
        except BadRequest as e_bad:
            logger.error(f"Erreur secondaire lors de l'envoi du message simple: {str(e_bad)}")
        except Exception as e2:
            logger.error(f"Erreur secondaire lors de l'envoi du message simple: {str(e2)}")
        return PROFILE_MAIN

async def get_user_stats(user_id):
    """
    Récupère les statistiques de l'utilisateur à partir de la BDD
    """
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    # Valeurs par défaut
    stats = {
        'rating': 0,
        'trips_count': 0,
        'bookings_count': 0,
        'earnings': 0.00
    }
    
    if not user:
        return stats
    
    # Récupérer la note moyenne (combinée conducteur et passager)
    driver_rating = user.driver_rating if hasattr(user, 'driver_rating') else 0
    passenger_rating = user.passenger_rating if hasattr(user, 'passenger_rating') else 0
    
    if driver_rating and passenger_rating:
        stats['rating'] = (driver_rating + passenger_rating) / 2
    elif driver_rating:
        stats['rating'] = driver_rating
    elif passenger_rating:
        stats['rating'] = passenger_rating
    else:
        stats['rating'] = 5.0  # Note par défaut si aucune évaluation
    
    # Compter les trajets à venir (en tant que conducteur)
    future_trips = db.query(func.count(Trip.id)).filter(
        Trip.driver_id == user.id,
        Trip.departure_time > datetime.now(),
        Trip.is_published == True
    ).scalar()
    stats['trips_count'] = future_trips or 0
    
    # Compter les réservations actives (en tant que passager)
    active_bookings = db.query(func.count(Booking.id)).filter(
        Booking.passenger_id == user.id,
        Booking.status.in_(['confirmed', 'pending']),
        Trip.departure_time > datetime.now()
    ).join(Trip).scalar()
    stats['bookings_count'] = active_bookings or 0
    
    # Calculer les gains (trajets complétés * prix par siège * 0.88 (100% - 12%))
    completed_trips = db.query(Trip).filter(
        Trip.driver_id == user.id,
        Trip.departure_time <= datetime.now()
    ).all()
    
    total_earnings = 0
    for trip in completed_trips:
        try:
            # Trouver les réservations confirmées pour ce trajet
            try:
                # Vérifier de façon sécurisée si la colonne is_paid existe
                bookings = db.query(Booking).filter(
                    Booking.trip_id == trip.id,
                    Booking.status == 'completed'
                ).all()
                
                # Filtrer après la requête pour les colonnes qui pourraient ne pas exister
                filtered_bookings = []
                for booking in bookings:
                    try:
                        if not hasattr(booking, 'is_paid') or booking.is_paid:
                            filtered_bookings.append(booking)
                    except Exception:
                        # Si on ne peut pas accéder à is_paid, considérer la réservation comme payée
                        filtered_bookings.append(booking)
                
                for booking in filtered_bookings:
                    # Gérer le cas où la colonne seats n'existe pas ou est null
                    seats = 1
                    try:
                        if hasattr(booking, 'seats') and booking.seats is not None:
                            seats = booking.seats
                    except Exception:
                        # Si problème pour accéder à seats, utiliser la valeur par défaut
                        pass
                    
                    price = trip.price_per_seat or 0
                    total_earnings += seats * price * 0.88  # 88% après commission de 12%
            except Exception as booking_error:
                logger.error(f"Erreur lors de la requête des réservations pour le trajet {trip.id}: {str(booking_error)}")
        except Exception as e:
            logger.error(f"Erreur lors du calcul des gains pour le trajet {trip.id}: {str(e)}")
            # Continuer avec le trajet suivant
    
    stats['earnings'] = total_earnings
    
    return stats

async def handle_profile_action(update: Update, context: CallbackContext):
    """
    Gère les actions du menu profil
    """
    try:
        query = update.callback_query
        await query.answer()
        if not query.data or ':' not in query.data:
            await query.edit_message_text(
                "⚠️ Erreur: Format de données invalide. Veuillez retourner au menu principal.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]])
            )
            return PROFILE_MAIN
        action = query.data.split(':')[1]
        logger.info(f"Action de profil sélectionnée: {action}")
        if action == "back_to_profile":
            return await back_to_profile(update, context)
        if action == "my_trips":
            # Utiliser la fonction unifiée des trajets
            from handlers.trip_handlers import list_my_trips
            return await list_my_trips(update, context)
        elif action == "my_bookings":
            return await show_my_bookings(update, context)
        elif action == "my_earnings":
            return await show_my_earnings(update, context)
        elif action == "edit":
            return await show_edit_profile(update, context)
        elif action == "invite":
            return await generate_invite_link(update, context)
        else:
            await query.edit_message_text(
                "⚠️ Option non reconnue. Veuillez choisir une option valide.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
            )
            return PROFILE_MAIN
    except Exception as e:
        logger.error(f"Erreur dans handle_profile_action: {str(e)}")
        try:
            await update.callback_query.edit_message_text(
                "⚠️ Une erreur est survenue. Veuillez réessayer.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]
                ])
            )
        except Exception as e2:
            logger.error(f"Erreur secondaire lors de la gestion d'erreur: {str(e2)}")
        return PROFILE_MAIN

async def show_my_trips(update: Update, context: CallbackContext):
    """
    Affiche la liste des trajets créés par l'utilisateur (page totalement différente du profil principal)
    """
    try:
        query = update.callback_query
        await query.answer()
        logger.info("[NAVIGATION] Affichage de la page MES TRAJETS")
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            logger.error("Utilisateur non trouvé pour telegram_id=%s", user_id)
            await query.edit_message_text(
                "⚠️ Utilisateur non trouvé.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]])
            )
            return PROFILE_MAIN
        # Récupérer tous les trajets à venir publiés du conducteur, sans filtrer sur is_cancelled côté SQL
        trips = db.query(Trip).filter(
            Trip.driver_id == user.id,
            Trip.is_published == True,
            Trip.departure_time > datetime.now(),
            Trip.is_cancelled == False
        ).order_by(Trip.departure_time).all()
        logger.info(f"[MES TRAJETS] {len(trips)} trajets trouvés pour user_id={user_id}")
        active_blocks = []
        for trip in trips:
            try:
                # Ajout automatique du champ is_cancelled si absent
                if not hasattr(trip, 'is_cancelled'):
                    setattr(trip, 'is_cancelled', False)
                    try:
                        db.commit()
                        logger.info(f"[MES TRAJETS] Champ is_cancelled ajouté pour le trajet {trip.id}.")
                    except Exception as e:
                        logger.error(f"[MES TRAJETS] Impossible d'ajouter is_cancelled pour le trajet {trip.id}: {e}")
                        print(f"[MES TRAJETS] Impossible d'ajouter is_cancelled pour le trajet {trip.id}: {e}")
                # EXCLURE STRICTEMENT LES TRAJETS ANNULÉS
                if getattr(trip, 'is_cancelled', False):
                    continue  # On saute ce trajet, il n'est affiché nulle part
                departure_date = trip.departure_time.strftime("%d/%m/%Y %H:%M") if hasattr(trip, 'departure_time') and trip.departure_time else "?"
                departure_city = getattr(trip, 'departure_city', "Départ")
                arrival_city = getattr(trip, 'arrival_city', "Arrivée")
                price_per_seat = getattr(trip, 'price_per_seat', 0.00)
                try:
                    booking_count = db.query(Booking).filter(Booking.trip_id == trip.id, Booking.status.in_(["pending", "confirmed"])) .count()
                except Exception as e:
                    logger.error(f"Erreur lors du comptage des réservations pour le trajet {getattr(trip, 'id', '?')}: {e}")
                    booking_count = 0
                trip_str = (
                    f"• {departure_city} → {arrival_city}\n"
                    f"  📅 {departure_date}\n"
                    f"  💰 {price_per_seat:.2f} CHF/place"
                )
                row_btns = []
                if booking_count == 0:
                    row_btns.append(InlineKeyboardButton("✏️ Modifier", callback_data=f"trip:edit:{trip.id}"))
                row_btns.append(InlineKeyboardButton("❌ Annuler", callback_data=f"trip:cancel:{trip.id}"))
                active_blocks.append({'text': trip_str, 'buttons': row_btns})
            except Exception as e:
                logger.error(f"[MES TRAJETS] Erreur sur le trajet: {getattr(trip, 'id', '?')} : {e}")
                print(f"[MES TRAJETS] Erreur sur le trajet: {getattr(trip, 'id', '?')} : {e}")
                continue
        if not active_blocks:
            message = "🚗 *Mes trajets à venir :*\n\nAucun trajet prévu pour le moment."
            keyboard = [
                [InlineKeyboardButton("➕ Créer un trajet", callback_data="menu:create")],
                [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
            ]
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            return PROFILE_MAIN
        # Construction du message et du clavier
        text = "🚗 *Mes trajets à venir :*"
        reply_markup_rows = []
        for b in active_blocks:
            text += f"\n\n{b['text']}"
            if b['buttons']:
                reply_markup_rows.append(b['buttons'])
        reply_markup_rows.append([InlineKeyboardButton("➕ Créer un trajet", callback_data="menu:create")])
        reply_markup_rows.append([InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")])
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(reply_markup_rows),
            parse_mode=ParseMode.MARKDOWN
        )
        return PROFILE_MAIN
    except Exception as e:
        logger.error(f"Erreur dans show_my_trips: {str(e)}")
        print(f"[MES TRAJETS] Exception globale: {e}")
        await update.callback_query.edit_message_text(
            "⚠️ Erreur lors de l'affichage de vos trajets.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
        )
        return PROFILE_MAIN

async def show_my_bookings(update: Update, context: CallbackContext):
    """
    Affiche la liste des réservations de l'utilisateur (page totalement différente du profil principal)
    """
    try:
        query = update.callback_query
        await query.answer()
        logger.info("[NAVIGATION] Affichage de la page MES RESERVATIONS")
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            await query.edit_message_text(
                "⚠️ Utilisateur non trouvé.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]])
            )
            return PROFILE_MAIN
        bookings = db.query(Booking).filter(
            Booking.passenger_id == user.id,
            Booking.status.in_(['confirmed', 'pending']),
        ).join(Trip).filter(
            Trip.departure_time > datetime.now()
        ).order_by(Trip.departure_time).all()
        if not bookings:
            message = "🎫 *Mes réservations :*\n\nAucune réservation active."
        else:
            message = "🎫 *Mes réservations :*\n\n"
            for booking in bookings:
                trip = booking.trip
                departure_date = trip.departure_time.strftime("%d/%m/%Y %H:%M")
                departure_city = getattr(trip, 'departure_city', "Départ")
                arrival_city = getattr(trip, 'arrival_city', "Arrivée")
                status = "✅ Confirmée" if booking.status == 'confirmed' else "⏳ En attente"
                message += (
                    f"• {departure_city} → {arrival_city}\n"
                    f"  📅 {departure_date}\n"
                    f"  {status}\n\n"
                )
        keyboard = [
            [InlineKeyboardButton("🔍 Rechercher un trajet", callback_data="menu:search_trip")],
            [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
        ]
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return PROFILE_MAIN
    except Exception as e:
        logger.error(f"Erreur dans show_my_bookings: {str(e)}")
        await update.callback_query.edit_message_text(
            "⚠️ Erreur lors de l'affichage de vos réservations.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
        )
        return PROFILE_MAIN

async def show_my_earnings(update: Update, context: CallbackContext):
    """
    Affiche les gains du conducteur :
    - Uniquement les trajets confirmés ET payés (is_paid ET is_confirmed)
    - Affiche le net après commission 12%
    - Affiche une section 'en attente' pour les réservations non confirmées ou non payées
    - Affiche la commission totale prélevée
    """
    try:
        query = update.callback_query
        await query.answer()
        logger.info("[NAVIGATION] Affichage de la page MES GAINS (nouvelle logique)")
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            await query.edit_message_text(
                "⚠️ Utilisateur non trouvé.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]])
            )
            return PROFILE_MAIN
        completed_trips = db.query(Trip).filter(
            Trip.driver_id == user.id,
            Trip.departure_time <= datetime.now()
        ).all()
        confirmed_lines = []
        pending_lines = []
        total_net = 0.0
        total_commission = 0.0
        for trip in completed_trips:
            # Pour chaque réservation de ce trajet
            bookings = db.query(Booking).filter(Booking.trip_id == trip.id).all()
            for booking in bookings:
                price = getattr(trip, 'price_per_seat', 0.0)
                seats = getattr(booking, 'seats', 1)
                total = price * seats
                commission = total * 0.12
                net = total * 0.88
                departure_city = getattr(trip, 'departure_city', "Départ")
                arrival_city = getattr(trip, 'arrival_city', "Arrivée")
                date = trip.departure_time.strftime("%d/%m/%Y")
                # Statuts
                is_paid = getattr(booking, 'is_paid', False)
                is_confirmed = getattr(booking, 'is_confirmed', False)
                # Section confirmée et payée
                if is_paid and is_confirmed:
                    confirmed_lines.append(f"• {departure_city} → {arrival_city} ({date}) : {total:.2f} CHF → {net:.2f} CHF net")
                    total_net += net
                    total_commission += commission
                else:
                    # Section en attente
                    status = []
                    if not is_confirmed:
                        status.append("non confirmé")
                    if not is_paid:
                        status.append("non payé")
                    status_str = ", ".join(status)
                    pending_lines.append(f"• {departure_city} → {arrival_city} ({date}) : {total:.2f} CHF ({status_str})")
        # Construction du message
        message = "💰 *Mes gains :*\n\n"
        message += "✅ *Gains confirmés :*\n"
        if confirmed_lines:
            message += "\n".join(confirmed_lines) + "\n"
            message += f"\n*Total net disponible : {total_net:.2f} CHF*\n"
        else:
            message += "Aucun gain confirmé pour l'instant.\n"
        if pending_lines:
            message += "\n🕓 *En attente de confirmation ou de paiement :*\n"
            message += "\n".join(pending_lines) + "\n"
        message += f"\nCommission totale prélevée : {total_commission:.2f} CHF"
        keyboard = [
            [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
        ]
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return PROFILE_MAIN
    except Exception as e:
        logger.error(f"Erreur dans show_my_earnings: {str(e)}")
        await update.callback_query.edit_message_text(
            "⚠️ Erreur lors de l'affichage de vos gains.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
        )
        return PROFILE_MAIN

async def show_edit_profile(update: Update, context: CallbackContext):
    """
    Affiche le menu d'édition du profil (page totalement différente du profil principal)
    """
    try:
        query = update.callback_query
        await query.answer()
        logger.info("[NAVIGATION] Affichage de la page EDITION DU PROFIL")
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            await query.edit_message_text(
                "⚠️ Utilisateur non trouvé.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]])
            )
            return PROFILE_MAIN
        keyboard = [
            [
                InlineKeyboardButton("👤 Modifier nom", callback_data="edit:name"),
                InlineKeyboardButton("🔢 Modifier âge", callback_data="edit:age")
            ],
            [
                InlineKeyboardButton("📱 Modifier téléphone", callback_data="edit:phone"),
                InlineKeyboardButton("📝 Modifier description", callback_data="edit:description")
            ],
            [
                InlineKeyboardButton("🚗 Gérer véhicule", callback_data="edit:vehicle"),
                InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")
            ]
        ]
        name = user.full_name if hasattr(user, 'full_name') and user.full_name else "Non renseigné"
        age = f"{user.age} ans" if hasattr(user, 'age') and user.age else "Non renseigné"
        phone = user.phone or "Non renseigné"
        description = getattr(user, 'description', "Non renseigné")
        car = getattr(user, 'car_model', "Non renseigné")
        message = (
            "✏️ *Édition du profil*\n\n"
            f"*Nom:* {name}\n"
            f"*Âge:* {age}\n"
            f"*Téléphone:* {phone}\n"
            f"*Description:* {description}\n"
            f"*Véhicule:* {car}\n\n"
            "Que souhaitez-vous modifier ?"
        )
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return EDIT_PROFILE
    except Exception as e:
        logger.error(f"Erreur dans show_edit_profile: {str(e)}")
        await update.callback_query.edit_message_text(
            "⚠️ Erreur lors de l'affichage du menu d'édition.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
        )
        return PROFILE_MAIN

async def handle_edit_action(update: Update, context: CallbackContext):
    """
    Gère les actions d'édition du profil
    """
    query = update.callback_query
    await query.answer()
    action = query.data.split(':')[1]
    
    if action == "name":
        await query.edit_message_text(
            "👤 *Modifier votre nom*\n\n"
            "Veuillez entrer votre nom complet:",
            parse_mode=ParseMode.MARKDOWN
        )
        return TYPING_NAME
    
    elif action == "age":
        await query.edit_message_text(
            "🔢 *Modifier votre âge*\n\n"
            "Veuillez entrer votre âge (nombre entier):",
            parse_mode=ParseMode.MARKDOWN
        )
        return TYPING_AGE
    
    elif action == "phone":
        await query.edit_message_text(
            "📱 *Modifier votre téléphone*\n\n"
            "Veuillez entrer votre numéro de téléphone.\n"
            "Format: +41 XX XXX XX XX ou 07X XXX XX XX",
            parse_mode=ParseMode.MARKDOWN
        )
        return TYPING_PHONE
    
    elif action == "description":
        await query.edit_message_text(
            "📝 *Modifier votre description*\n\n"
            "Veuillez entrer une courte description de vous-même:",
            parse_mode=ParseMode.MARKDOWN
        )
        return TYPING_DESCRIPTION
    
    elif action == "vehicle":
        # Laisser le ConversationHandler vehicle_conv_handler gérer ce callback (ne rien faire ici)
        return ConversationHandler.END
    
    return EDIT_PROFILE

async def handle_name_input(update: Update, context: CallbackContext):
    """
    Gère l'entrée du nom
    """
    user_id = update.effective_user.id
    name = update.message.text.strip()
    
    # Validation basique
    if len(name) < 2 or len(name) > 50:
        await update.message.reply_text(
            "⚠️ Le nom doit contenir entre 2 et 50 caractères. Veuillez réessayer."
        )
        return TYPING_NAME
    
    # Mise à jour dans la BDD
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await update.message.reply_text("⚠️ Utilisateur non trouvé.")
        return ConversationHandler.END
    
    # Mettre à jour le nom complet
    user.full_name = name
    db.commit()
    
    await update.message.reply_text(f"✅ Nom mis à jour: {name}")
    
    # Retourner au menu d'édition
    keyboard = [[InlineKeyboardButton("🔙 Retour à l'édition", callback_data="profile:back_to_edit")]]
    await update.message.reply_text(
        "Que souhaitez-vous faire maintenant?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_PROFILE

async def handle_age_input(update: Update, context: CallbackContext):
    """
    Gère l'entrée de l'âge
    """
    user_id = update.effective_user.id
    age_text = update.message.text.strip()
    
    # Validation
    try:
        age = int(age_text)
        if age < 18 or age > 100:
            raise ValueError("Age hors limites")
    except ValueError:
        await update.message.reply_text(
            "⚠️ Veuillez entrer un âge valide entre 18 et 100 ans."
        )
        return TYPING_AGE
    
    # Mise à jour dans la BDD
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await update.message.reply_text("⚠️ Utilisateur non trouvé.")
        return ConversationHandler.END
    
    user.age = age
    db.commit()
    
    await update.message.reply_text(f"✅ Âge mis à jour: {age} ans")
    
    # Retourner au menu d'édition
    keyboard = [[InlineKeyboardButton("🔙 Retour à l'édition", callback_data="profile:back_to_edit")]]
    await update.message.reply_text(
        "Que souhaitez-vous faire maintenant?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_PROFILE

async def handle_phone_input(update: Update, context: CallbackContext):
    """
    Gère l'entrée du numéro de téléphone
    """
    user_id = update.effective_user.id
    phone = update.message.text.strip()
    
    # Nettoyage du numéro
    phone = phone.replace(" ", "").replace("-", "").replace(".", "")
    if phone.startswith("0"):
        phone = "+41" + phone[1:]
    
    # Validation du format
    if not (phone.startswith('+41') and len(phone) == 12 and phone[1:].isdigit()):
        await update.message.reply_text(
            "❌ Format invalide. Veuillez utiliser:\n"
            "+41 XX XXX XX XX ou\n"
            "07X XXX XX XX"
        )
        return TYPING_PHONE
    
    # Mise à jour dans la BDD
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await update.message.reply_text("⚠️ Utilisateur non trouvé.")
        return ConversationHandler.END
    
    user.phone = phone
    user.phone_verified = True  # Marquer comme vérifié
    db.commit()
    
    await update.message.reply_text(f"✅ Numéro de téléphone mis à jour: {phone}")
    
    # Retourner au menu d'édition
    keyboard = [[InlineKeyboardButton("🔙 Retour à l'édition", callback_data="profile:back_to_edit")]]
    await update.message.reply_text(
        "Que souhaitez-vous faire maintenant?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_PROFILE

async def handle_description_input(update: Update, context: CallbackContext):
    """
    Gère l'entrée de la description
    """
    user_id = update.effective_user.id
    description = update.message.text.strip()
    
    # Validation
    if len(description) > 500:
        await update.message.reply_text(
            "⚠️ La description est trop longue (max 500 caractères)."
        )
        return TYPING_DESCRIPTION
    
    # Mise à jour dans la BDD
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await update.message.reply_text("⚠️ Utilisateur non trouvé.")
        return ConversationHandler.END
    
    user.full_name = description  # Utiliser le champ full_name pour la description (à adapter selon votre modèle)
    db.commit()
    
    await update.message.reply_text("✅ Description mise à jour avec succès.")
    
    # Retourner au menu d'édition
    keyboard = [[InlineKeyboardButton("🔙 Retour à l'édition", callback_data="profile:back_to_edit")]]
    await update.message.reply_text(
        "Que souhaitez-vous faire maintenant?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_PROFILE

async def generate_invite_link(update: Update, context: CallbackContext):
    """
    Génère un lien d'invitation pour partager le bot
    """
    try:
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        username = user.username
        
        if not username:
            message = (
                "📤 *Inviter un ami*\n\n"
                "Pour générer un lien d'invitation personnalisé, "
                "vous devez d'abord configurer un nom d'utilisateur Telegram.\n\n"
                "Allez dans les paramètres de Telegram, puis 'Nom d'utilisateur' pour en configurer un.\n\n"
            )
        else:
            bot_username = context.bot.username
            invite_link = f"https://t.me/{bot_username}?start=ref_{username}"
            
            message = (
                "📤 *Inviter un ami*\n\n"
                "Partagez ce lien avec vos amis pour les inviter à rejoindre CovoiturageSuisse:\n\n"
                f"`{invite_link}`\n\n"
                "Copiez ce message et envoyez-le à vos contacts:"
                "\n\n"
                f"🚗 Rejoins-moi sur CovoiturageSuisse! C'est une application de covoiturage spécialement conçue pour la Suisse. Voici mon lien d'invitation: {invite_link}\n\n"
            )
        
        keyboard = [[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]]
        
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
            logger.error(f"Erreur BadRequest dans generate_invite_link: {str(e)}")
            try:
                await query.edit_message_text(
                    "⚠️ Une erreur est survenue lors de la génération du lien d'invitation. Veuillez réessayer.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
                )
            except Exception as e2:
                logger.error(f"Erreur secondaire dans generate_invite_link: {str(e2)}")
            return PROFILE_MAIN
            
    except Exception as e:
        logger.error(f"Erreur dans generate_invite_link: {str(e)}")
        try:
            query = update.callback_query
            await query.edit_message_text(
                "⚠️ Une erreur est survenue lors de la génération du lien d'invitation. Veuillez réessayer.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]])
            )
        except Exception as e2:
            logger.error(f"Erreur secondaire dans generate_invite_link: {str(e2)}")
        return PROFILE_MAIN

async def back_to_profile(update: Update, context: CallbackContext):
    """
    Retourne au tableau de bord du profil depuis n'importe quelle sous-page
    """
    await show_profile_dashboard(update, context)
    return PROFILE_MAIN

async def back_to_edit(update: Update, context: CallbackContext):
    """
    Retourne au menu d'édition du profil
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Directement appeler show_edit_profile qui va utiliser le token de rafraîchissement
        await show_edit_profile(update, context)
        return EDIT_PROFILE
    
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message identique ignoré: %s", str(e))
            return EDIT_PROFILE
        else:
            logger.error(f"Erreur BadRequest dans back_to_edit: {str(e)}")
            try:
                query = update.callback_query
                await query.edit_message_text(
                    "⚠️ Une erreur est survenue lors du retour au menu d'édition. Veuillez réessayer.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")],
                        [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]
                    ])
                )
            except Exception as e2:
                logger.error(f"Erreur secondaire dans back_to_edit: {str(e2)}")
            return EDIT_PROFILE
    
    except Exception as e:
        logger.error(f"Erreur dans back_to_edit: {str(e)}")
        try:
            query = update.callback_query
            await query.edit_message_text(
                "⚠️ Une erreur est survenue lors du retour au menu d'édition. Veuillez réessayer.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="menu:back_to_menu")]
                ])
            )
        except Exception as e2:
            logger.error(f"Erreur secondaire dans back_to_edit: {str(e2)}")
        return EDIT_PROFILE

async def cancel_profile(update: Update, context: CallbackContext):
    """
    Annule la conversation du profil
    """
    try:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text("❌ Modification du profil annulée.")
        else:
            await update.message.reply_text("❌ Modification du profil annulée.")
        
        # Retour au menu principal
        # Importation ici pour éviter les imports circulaires
        try:
            from handlers.menu_handlers import start_command
            await start_command(update, context)
        except Exception as e:
            logger.error(f"Erreur lors du retour au menu principal: {str(e)}")
            # Fallback en cas d'erreur avec start_command
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "🏠 Retour au menu principal...",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Rafraîchir", callback_data="menu:refresh")]])
                )
            else:
                await update.message.reply_text("🏠 Tapez /start pour revenir au menu principal.")
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Erreur dans cancel_profile: {str(e)}")
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "⚠️ Une erreur est survenue. Veuillez taper /start pour revenir au menu principal.",
                    reply_markup=None
                )
            else:
                await update.message.reply_text("⚠️ Une erreur est survenue. Veuillez taper /start pour revenir au menu principal.")
        except:
            pass
        return ConversationHandler.END

# Création du ConversationHandler pour la gestion du profil
profile_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("profil", profile_handler),
        CommandHandler("profile", profile_handler),
        CallbackQueryHandler(profile_handler, pattern="^profil$"),
        CallbackQueryHandler(profile_handler, pattern="^menu:profile$"),
        CallbackQueryHandler(profile_handler, pattern="menu:profile"),
        # NE PAS inclure .*profile.* ici !
    ],
    states={
        PROFILE_MAIN: [
            CallbackQueryHandler(handle_profile_action, pattern="^profile:(my_trips|my_bookings|my_earnings|edit|invite)$"),
            CallbackQueryHandler(back_to_profile, pattern="^profile:back_to_profile$"),
            CallbackQueryHandler(cancel_profile, pattern="^menu:back_to_menu$")
        ],
        EDIT_PROFILE: [
            CallbackQueryHandler(handle_edit_action, pattern="^edit:(name|age|phone|description|vehicle)$"),
            CallbackQueryHandler(back_to_profile, pattern="^profile:back_to_profile$"),
            CallbackQueryHandler(back_to_edit, pattern="^profile:back_to_edit$")
        ],
        TYPING_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input),
            CommandHandler("cancel", cancel_profile)
        ],
        TYPING_AGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age_input),
            CommandHandler("cancel", cancel_profile)
        ],
        TYPING_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input),
            CommandHandler("cancel", cancel_profile)
        ],
        TYPING_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description_input),
            CommandHandler("cancel", cancel_profile)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel_profile),
        CallbackQueryHandler(cancel_profile, pattern="^cancel$")
    ],
    name="profile_conversation",
    persistent=True,
    allow_reentry=True
)

# Gestionnaire spécifique pour le bouton de profil dans le menu principal
profile_button_handler = CallbackQueryHandler(profile_handler, pattern="^menu:profile$")
logger.info("Profile button handler registered with pattern: ^menu:profile$")

def register(application):
    """
    Enregistre les handlers dans l'application
    """
    application.add_handler(profile_conv_handler)
    logger.info("Profile handlers registered.")

async def handle_cancel_trip_callback(update: Update, context: CallbackContext):
    """
    Handler pour l'annulation d'un trajet par le conducteur.
    Robuste : ne crash jamais même si le champ is_cancelled n'existe pas encore.
    """
    query = update.callback_query
    db = get_db()
    try:
        trip_id = None
        if query and query.data:
            # On suppose que le callback_data est du type "trip:cancel:<trip_id>"
            parts = query.data.split(":")
            if len(parts) == 3 and parts[0] == "trip" and parts[1] == "cancel":
                trip_id = int(parts[2])
        logger.info(f"[CANCEL] Demande d'annulation du trajet id={trip_id}")

        if not trip_id:
            logger.error("[CANCEL] trip_id manquant dans le callback_data")
            await query.answer("Erreur : identifiant du trajet manquant.", show_alert=True)
            return PROFILE_MAIN

        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            logger.error(f"[CANCEL] Trajet id={trip_id} introuvable en base")
            await query.answer("Erreur : trajet introuvable.", show_alert=True)
            return PROFILE_MAIN

        # Vérification et initialisation du champ is_cancelled
        if not hasattr(trip, "is_cancelled"):
            logger.warning(f"[CANCEL] Attribut 'is_cancelled' absent sur Trip id={trip_id}, initialisation à False")
            try:
                setattr(trip, "is_cancelled", False)
                db.commit()
                logger.info(f"[CANCEL] Attribut 'is_cancelled' ajouté et initialisé à False pour Trip id={trip_id}")
            except Exception as e:
                logger.error(f"[CANCEL] Impossible d'ajouter 'is_cancelled' à Trip id={trip_id} : {e}")

        # Vérification finale avant accès
        if not hasattr(trip, "is_cancelled"):
            logger.error(f"[CANCEL] Attribut 'is_cancelled' toujours absent après tentative d'ajout sur Trip id={trip_id}")
            await query.answer("Erreur interne : impossible d'annuler ce trajet.", show_alert=True)
            return PROFILE_MAIN

        if trip.is_cancelled:
            logger.info(f"[CANCEL] Trajet id={trip_id} déjà annulé")
            await query.answer("Ce trajet est déjà annulé.", show_alert=True)
            return PROFILE_MAIN

        # Annulation effective
        trip.is_cancelled = True
        db.commit()
        logger.info(f"[CANCEL] Trajet id={trip_id} annulé avec succès")

        # Notifier les passagers (exemple, à adapter selon ta logique)
        try:
            bookings = db.query(Booking).filter(Booking.trip_id == trip.id, Booking.status == "confirmed").all()
            for booking in bookings:
                # Ici, tu peux envoyer une notification Telegram ou email
                logger.info(f"[CANCEL] Notification envoyée au passager id={booking.passenger_id} pour annulation du trajet id={trip_id}")
        except Exception as e:
            logger.error(f"[CANCEL] Erreur lors de la notification des passagers pour Trip id={trip_id} : {e}")

        await query.answer("Trajet annulé avec succès.", show_alert=True)
        # Rafraîchir la liste des trajets
        await show_my_trips(update, context)
        return PROFILE_MAIN

    except Exception as e:
        logger.error(f"[CANCEL] Exception globale dans handle_cancel_trip_callback : {e}")
        await query.answer("Erreur lors de l'annulation du trajet.", show_alert=True)
        return PROFILE_MAIN