"""
Gestionnaires Telegram pour les paiements PayPal
Gestion des commandes de paiement et intégration avec PayPal
"""

import logging
import json
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from database.db_manager import get_db
from database.models import User, Trip, Booking
from paypal_utils import create_trip_payment, complete_trip_payment, pay_driver
import asyncio
from contextlib import contextmanager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# États pour le ConversationHandler
WAITING_PAYPAL_EMAIL = 1

@contextmanager
def get_db_session():
    """Context manager pour gérer les sessions de base de données"""
    session = get_db()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

class PaymentHandlers:
    """Gestionnaires pour les paiements PayPal"""
    
    @staticmethod
    async def set_paypal_email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Commande /definirpaypal - Enregistrer l'email PayPal d'un utilisateur
        """
        user = update.effective_user
        
        await update.message.reply_text(
            "🏦 *Configuration PayPal*\n\n"
            "Pour recevoir vos paiements de covoiturage, nous avons besoin de votre adresse email PayPal.\n\n"
            "⚠️ *Important :* Assurez-vous que cette adresse email est bien associée à votre compte PayPal.\n\n"
            "📧 Veuillez saisir votre adresse email PayPal :",
            parse_mode='Markdown'
        )
        
        return WAITING_PAYPAL_EMAIL
    
    @staticmethod
    async def save_paypal_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Sauvegarde l'email PayPal de l'utilisateur
        """
        email = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Validation basique de l'email
        if '@' not in email or '.' not in email:
            await update.message.reply_text(
                "❌ Adresse email invalide. Veuillez saisir une adresse email valide :",
                parse_mode='Markdown'
            )
            return WAITING_PAYPAL_EMAIL
        
        try:
            with get_db_session() as session:
                # Recherche de l'utilisateur
                user = session.query(User).filter(User.telegram_id == user_id).first()
                
                if not user:
                    await update.message.reply_text(
                        "❌ Utilisateur non trouvé. Veuillez d'abord vous inscrire avec /start"
                    )
                    return ConversationHandler.END
                
                # Mise à jour de l'email PayPal
                user.paypal_email = email
                session.commit()
                
                await update.message.reply_text(
                    f"✅ *Email PayPal enregistré avec succès !*\n\n"
                    f"📧 Email : `{email}`\n\n"
                    f"Vous pouvez maintenant recevoir des paiements pour vos trajets en tant que conducteur.",
                    parse_mode='Markdown'
                )
                
                logger.info(f"Email PayPal enregistré pour l'utilisateur {user_id}: {email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'email PayPal : {e}")
            await update.message.reply_text(
                "❌ Erreur lors de l'enregistrement. Veuillez réessayer plus tard."
            )
        
        return ConversationHandler.END
    
    @staticmethod
    async def cancel_paypal_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Annule la configuration PayPal
        """
        await update.message.reply_text("❌ Configuration PayPal annulée.")
        return ConversationHandler.END
    
    @staticmethod
    async def pay_trip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Commande /payer <id_trajet> - Initier un paiement pour un trajet
        """
        user_id = update.effective_user.id
        
        # Vérification des arguments
        if not context.args:
            await update.message.reply_text(
                "❌ Usage : `/payer <id_trajet>`\n\n"
                "Exemple : `/payer 123`",
                parse_mode='Markdown'
            )
            return
        
        try:
            trip_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ ID de trajet invalide. Veuillez saisir un nombre."
            )
            return
        
        try:
            with get_db_session() as session:
                # Vérification de l'existence du trajet
                trip = session.query(Trip).filter(Trip.id == trip_id).first()
                if not trip:
                    await update.message.reply_text(
                        f"❌ Trajet #{trip_id} non trouvé."
                    )
                    return
                
                # Vérification que l'utilisateur a une réservation pour ce trajet
                booking = session.query(Booking).filter(
                    Booking.trip_id == trip_id,
                    Booking.passenger_id == user_id,
                    Booking.status == 'confirmed'
                ).first()
                
                if not booking:
                    await update.message.reply_text(
                        f"❌ Vous n'avez pas de réservation confirmée pour le trajet #{trip_id}."
                    )
                    return
                
                # Vérification que le paiement n'a pas déjà été effectué
                if booking.payment_status == 'paid':
                    await update.message.reply_text(
                        f"✅ Vous avez déjà payé pour le trajet #{trip_id}."
                    )
                    return
                
                # Récupération du conducteur
                driver = session.query(User).filter(User.telegram_id == trip.driver_id).first()
                if not driver:
                    await update.message.reply_text(
                        "❌ Conducteur non trouvé."
                    )
                    return
                
                # Création du paiement PayPal
                trip_description = f"{trip.departure_city} → {trip.arrival_city}"
                success, payment_id, approval_url = create_trip_payment(
                    amount=float(booking.total_price),
                    trip_description=trip_description
                )
                
                if success and payment_id and approval_url:
                    # Sauvegarde de l'ID de paiement
                    booking.paypal_payment_id = payment_id
                    booking.payment_status = 'pending'
                    session.commit()
                    
                    # Création du clavier avec le lien PayPal
                    keyboard = [
                        [InlineKeyboardButton("💳 Payer avec PayPal", url=approval_url)],
                        [InlineKeyboardButton("❌ Annuler", callback_data=f"cancel_payment_{trip_id}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"💰 *Paiement du trajet #{trip_id}*\n\n"
                        f"🚗 Trajet : {trip_description}\n"
                        f"👤 Conducteur : {driver.full_name or 'Nom non défini'}\n"
                        f"💵 Montant : {booking.total_price} CHF\n\n"
                        f"Cliquez sur le bouton ci-dessous pour procéder au paiement PayPal :",
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    
                    logger.info(f"Paiement initié pour le trajet {trip_id}, montant: {booking.total_price} CHF")
                    
                else:
                    await update.message.reply_text(
                        "❌ Erreur lors de la création du paiement PayPal. Veuillez réessayer plus tard."
                    )
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du paiement : {e}")
            await update.message.reply_text(
                "❌ Erreur lors de l'initiation du paiement. Veuillez réessayer plus tard."
            )
    
    @staticmethod
    async def confirm_trip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Commande /confirmer <id_trajet> - Valider un trajet et payer le conducteur
        Utilisé par le conducteur pour confirmer que le trajet a été effectué
        """
        user_id = update.effective_user.id
        
        # Vérification des arguments
        if not context.args:
            await update.message.reply_text(
                "❌ Usage : `/confirmer <id_trajet>`\n\n"
                "Exemple : `/confirmer 123`",
                parse_mode='Markdown'
            )
            return
        
        try:
            trip_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ ID de trajet invalide. Veuillez saisir un nombre."
            )
            return
        
        try:
            with get_db_session() as session:
                # Vérification que le trajet existe et appartient au conducteur
                trip = session.query(Trip).filter(
                    Trip.id == trip_id,
                    Trip.driver_id == user_id
                ).first()
                
                if not trip:
                    await update.message.reply_text(
                        f"❌ Trajet #{trip_id} non trouvé ou vous n'êtes pas le conducteur."
                    )
                    return
                
                # Vérification que le trajet n'a pas déjà été confirmé
                if trip.status == 'completed':
                    await update.message.reply_text(
                        f"✅ Le trajet #{trip_id} a déjà été confirmé."
                    )
                    return
                
                # Récupération du conducteur
                driver = session.query(User).filter(User.telegram_id == user_id).first()
                if not driver or not hasattr(driver, 'paypal_email') or not driver.paypal_email:
                    await update.message.reply_text(
                        "❌ Vous devez d'abord configurer votre email PayPal avec /definirpaypal"
                    )
                    return
                
                # Récupération des réservations payées pour ce trajet
                paid_bookings = session.query(Booking).filter(
                    Booking.trip_id == trip_id,
                    Booking.payment_status == 'paid'
                ).all()
                
                if not paid_bookings:
                    await update.message.reply_text(
                        f"❌ Aucun passager n'a encore payé pour le trajet #{trip_id}."
                    )
                    return
                
                # Calcul du montant total à verser au conducteur
                total_amount = sum(float(booking.total_price) for booking in paid_bookings)
                
                # Envoi du paiement au conducteur (88% du montant)
                success, payout_batch_id = pay_driver(
                    driver_email=driver.paypal_email,
                    trip_amount=total_amount
                )
                
                if success:
                    # Mise à jour du statut du trajet
                    trip.status = 'completed'
                    trip.payout_batch_id = payout_batch_id
                    
                    # Mise à jour des réservations
                    for booking in paid_bookings:
                        booking.status = 'completed'
                    
                    session.commit()
                    
                    driver_amount = round(total_amount * 0.88, 2)
                    commission = round(total_amount * 0.12, 2)
                    
                    await update.message.reply_text(
                        f"✅ *Trajet #{trip_id} confirmé !*\n\n"
                        f"💰 Montant total collecté : {total_amount} CHF\n"
                        f"💵 Votre part (88%) : {driver_amount} CHF\n"
                        f"🏦 Commission (12%) : {commission} CHF\n\n"
                        f"💳 Le paiement a été envoyé à votre compte PayPal : {driver.paypal_email}\n\n"
                        f"Merci d'avoir utilisé notre service de covoiturage ! 🚗",
                        parse_mode='Markdown'
                    )
                    
                    # Notification aux passagers
                    for booking in paid_bookings:
                        passenger = session.query(User).filter(User.telegram_id == booking.passenger_id).first()
                        if passenger:
                            try:
                                await context.bot.send_message(
                                    chat_id=passenger.telegram_id,
                                    text=f"✅ *Trajet terminé !*\n\n"
                                         f"🚗 Trajet #{trip_id} : {trip.departure_city} → {trip.arrival_city}\n"
                                         f"👤 Conducteur : {driver.full_name or 'Nom non défini'}\n\n"
                                         f"Merci d'avoir voyagé avec nous ! N'hésitez pas à laisser un avis sur le conducteur.",
                                    parse_mode='Markdown'
                                )
                            except Exception as e:
                                logger.error(f"Erreur lors de l'envoi de notification au passager {passenger.telegram_id}: {e}")
                    
                    logger.info(f"Trajet {trip_id} confirmé, paiement de {driver_amount} CHF envoyé au conducteur")
                    
                else:
                    await update.message.reply_text(
                        "❌ Erreur lors de l'envoi du paiement PayPal. Veuillez contacter le support."
                    )
                    
        except Exception as e:
            logger.error(f"Erreur lors de la confirmation du trajet : {e}")
            await update.message.reply_text(
                "❌ Erreur lors de la confirmation du trajet. Veuillez réessayer plus tard."
            )
    
    @staticmethod
    async def payment_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gestionnaire pour les callbacks de paiement
        """
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        if data.startswith("cancel_payment_"):
            trip_id = int(data.split("_")[2])
            
            try:
                with get_db_session() as session:
                    # Annulation du paiement en cours
                    booking = session.query(Booking).filter(
                        Booking.trip_id == trip_id,
                        Booking.passenger_id == user_id,
                        Booking.payment_status == 'pending'
                    ).first()
                    
                    if booking:
                        booking.payment_status = 'cancelled'
                        booking.paypal_payment_id = None
                        session.commit()
                
                await query.edit_message_text(
                    f"❌ Paiement du trajet #{trip_id} annulé."
                )
                
            except Exception as e:
                logger.error(f"Erreur lors de l'annulation du paiement : {e}")
                await query.edit_message_text(
                    "❌ Erreur lors de l'annulation. Veuillez réessayer."
                )
    
    @staticmethod
    async def webhook_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Gestionnaire pour les webhooks PayPal
        Cette fonction serait appelée par un endpoint web séparé
        """
        # Cette fonction serait normalement appelée par un serveur web
        # qui reçoit les webhooks PayPal
        pass
    
    @staticmethod
    async def check_payment_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Commande /statut_paiement - Vérifier le statut des paiements
        """
        user_id = update.effective_user.id
        
        try:
            with get_db_session() as session:
                # Récupération des réservations en cours de l'utilisateur
                bookings = session.query(Booking).filter(
                    Booking.passenger_id == user_id,
                    Booking.payment_status.in_(['pending', 'paid'])
                ).join(Trip).all()
                
                if not bookings:
                    await update.message.reply_text(
                        "ℹ️ Vous n'avez aucun paiement en cours."
                    )
                    return
                
                message = "💳 *Statut de vos paiements :*\n\n"
                
                for booking in bookings:
                    trip = booking.trip
                    status_emoji = "⏳" if booking.payment_status == 'pending' else "✅"
                    status_text = "En attente" if booking.payment_status == 'pending' else "Payé"
                    
                    message += (
                        f"{status_emoji} *Trajet #{trip.id}*\n"
                        f"🚗 {trip.departure_city} → {trip.arrival_city}\n"
                        f"💰 {booking.total_price} CHF - {status_text}\n\n"
                    )
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut des paiements : {e}")
            await update.message.reply_text(
                "❌ Erreur lors de la vérification. Veuillez réessayer plus tard."
            )


# Création du ConversationHandler pour la configuration PayPal
paypal_setup_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('definirpaypal', PaymentHandlers.set_paypal_email_command)],
    states={
        WAITING_PAYPAL_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, PaymentHandlers.save_paypal_email),
            CommandHandler('cancel', PaymentHandlers.cancel_paypal_setup),
            CommandHandler('annuler', PaymentHandlers.cancel_paypal_setup),
        ],
    },
    fallbacks=[
        CommandHandler('cancel', PaymentHandlers.cancel_paypal_setup),
        CommandHandler('annuler', PaymentHandlers.cancel_paypal_setup),
    ],
    allow_reentry=True
)

# Gestionnaires de commandes
payment_command_handlers = [
    CommandHandler('payer', PaymentHandlers.pay_trip_command),
    CommandHandler('confirmer', PaymentHandlers.confirm_trip_command),
    CommandHandler('statut_paiement', PaymentHandlers.check_payment_status_command),
]

# Gestionnaire de callbacks
payment_callback_handler = CallbackQueryHandler(
    PaymentHandlers.payment_callback_handler,
    pattern=r'^(cancel_payment_|confirm_payment_)'
)


def get_payment_handlers():
    """
    Retourne tous les gestionnaires de paiement à ajouter à l'application
    """
    return {
        'conversation_handlers': [paypal_setup_conv_handler],
        'command_handlers': payment_command_handlers,
        'callback_handlers': [payment_callback_handler]
    }


if __name__ == "__main__":
    print("✅ Gestionnaires de paiement PayPal configurés")
    print("Commandes disponibles :")
    print("  /definirpaypal - Configurer l'email PayPal")
    print("  /payer <id_trajet> - Payer un trajet")
    print("  /confirmer <id_trajet> - Confirmer un trajet (conducteur)")
    print("  /statut_paiement - Vérifier le statut des paiements")
