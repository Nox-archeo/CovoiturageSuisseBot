#!/usr/bin/env python3
"""
Bot Telegram avec webhook pour déploiement sur Render
Gestion automatisée des paiements PayPal avec webhooks
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes
from dotenv import load_dotenv

# Import des handlers
from handlers.create_trip_handler import create_trip_conv_handler, publish_trip_handler, main_menu_handler, my_trips_handler
from handlers.search_trip_handler import search_trip_conv_handler
from handlers.menu_handlers import start_command, handle_menu_buttons
from handlers.profile_handler import profile_button_handler, profile_conv_handler
from handlers.trip_handlers import register as register_trip_handlers
from handlers.booking_handlers import register as register_booking_handlers
from handlers.message_handlers import register as register_message_handlers
from handlers.verification_handlers import register as register_verification_handlers
from handlers.subscription_handlers import register as register_subscription_handlers
from handlers.admin_handlers import register as register_admin_handlers
from handlers.user_handlers import register as register_user_handlers
from handlers.contact_handlers import register as register_contact_handlers
from handlers.dispute_handlers import register as register_dispute_handlers
from handlers.trip_completion_handlers import register as register_trip_completion_handlers
from handlers.vehicle_handler import vehicle_conv_handler

# Import des modules de paiement
from payment_handlers import get_payment_handlers
from db_utils import init_payment_database
from paypal_utils import paypal_manager
from database.models import User, Trip, Booking
from database import get_db

# Configuration logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # URL de votre service Render
PAYPAL_WEBHOOK_ID = os.getenv('PAYPAL_WEBHOOK_ID')
PORT = int(os.getenv('PORT', 8000))

# FastAPI app
app = FastAPI(title="CovoiturageSuisse Bot")

# Global bot instance
telegram_app = None

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    global telegram_app
    
    logger.info("🚀 Démarrage du bot webhook...")
    
    # Initialisation de la base de données
    if not init_payment_database():
        logger.error("Erreur lors de l'initialisation de la base de données")
        return
    
    # Configuration du bot
    telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Enregistrement des handlers
    await register_all_handlers(telegram_app)
    
    # Configuration du webhook
    webhook_url = f"{WEBHOOK_URL}/webhook"
    await telegram_app.bot.set_webhook(url=webhook_url)
    
    logger.info(f"✅ Webhook configuré: {webhook_url}")

async def register_all_handlers(application):
    """Enregistre tous les handlers du bot"""
    logger.info("Enregistrement des handlers...")
    
    # Handlers principaux
    application.add_handler(CommandHandler("start", start_command))
    
    # Handler de menu (priorité haute)
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:create$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:search_trip$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:my_trips$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:help$"))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^menu:back_to_menu$"))
    
    # Handlers de fonctionnalités
    application.add_handler(profile_button_handler)
    application.add_handler(profile_conv_handler)
    application.add_handler(create_trip_conv_handler)
    application.add_handler(publish_trip_handler)
    application.add_handler(main_menu_handler)
    application.add_handler(my_trips_handler)
    application.add_handler(search_trip_conv_handler)
    
    # Autres handlers
    register_trip_handlers(application)
    register_booking_handlers(application)
    register_message_handlers(application)
    register_verification_handlers(application)
    register_subscription_handlers(application)
    register_admin_handlers(application)
    register_user_handlers(application)
    register_contact_handlers(application)
    register_dispute_handlers(application)
    register_trip_completion_handlers(application)
    
    # Handlers de paiement PayPal
    payment_handlers = get_payment_handlers()
    for conv_handler in payment_handlers['conversation_handlers']:
        application.add_handler(conv_handler)
    for cmd_handler in payment_handlers['command_handlers']:
        application.add_handler(cmd_handler)
    for callback_handler in payment_handlers['callback_handlers']:
        application.add_handler(callback_handler)
    
    application.add_handler(vehicle_conv_handler)
    
    logger.info("✅ Tous les handlers enregistrés")

@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Endpoint pour les webhooks Telegram"""
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        
        # Traitement en arrière-plan pour ne pas bloquer
        background_tasks.add_task(process_telegram_update, update)
        
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Erreur webhook Telegram: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def process_telegram_update(update: Update):
    """Traite une mise à jour Telegram"""
    try:
        await telegram_app.process_update(update)
    except Exception as e:
        logger.error(f"Erreur traitement update: {e}")

@app.post("/paypal/webhook")
async def paypal_webhook(request: Request, background_tasks: BackgroundTasks):
    """Endpoint pour les webhooks PayPal - Gestion automatisée des paiements"""
    try:
        headers = dict(request.headers)
        body = await request.body()
        
        # Vérification de la signature PayPal (sécurité)
        if not verify_paypal_signature(headers, body):
            logger.warning("Signature PayPal invalide")
            return JSONResponse({"error": "Invalid signature"}, status_code=401)
        
        data = await request.json()
        event_type = data.get('event_type')
        
        logger.info(f"Webhook PayPal reçu: {event_type}")
        
        # Traitement en arrière-plan
        background_tasks.add_task(process_paypal_webhook, event_type, data)
        
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Erreur webhook PayPal: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def process_paypal_webhook(event_type: str, data: dict):
    """Traite les événements PayPal automatiquement"""
    try:
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            await handle_payment_completed(data)
        elif event_type == "PAYMENT.CAPTURE.DENIED":
            await handle_payment_failed(data)
        # Ajouter d'autres événements selon vos besoins
            
    except Exception as e:
        logger.error(f"Erreur traitement webhook PayPal: {e}")

async def handle_payment_completed(data: dict):
    """Gère un paiement PayPal complété"""
    try:
        # Extraire les informations du paiement
        resource = data.get('resource', {})
        custom_id = resource.get('custom_id')  # ID de la réservation
        amount = float(resource.get('amount', {}).get('value', 0))
        
        if not custom_id:
            logger.error("Pas de custom_id dans le paiement PayPal")
            return
        
        db = get_db()
        
        # Trouver la réservation
        booking = db.query(Booking).filter(Booking.id == int(custom_id)).first()
        if not booking:
            logger.error(f"Réservation {custom_id} non trouvée")
            return
        
        # Marquer le paiement comme complété
        booking.payment_status = 'completed'
        booking.paid_at = datetime.utcnow()
        db.commit()
        
        # Notifier le passager
        passenger = booking.passenger
        if passenger and passenger.telegram_id:
            message = (
                f"✅ *Paiement confirmé !*\n\n"
                f"Votre réservation pour le trajet {booking.trip.departure_city} → {booking.trip.arrival_city} "
                f"le {booking.trip.departure_time.strftime('%d/%m/%Y à %H:%M')} est confirmée.\n\n"
                f"Montant payé: {amount} CHF"
            )
            await telegram_app.bot.send_message(
                chat_id=passenger.telegram_id,
                text=message,
                parse_mode="Markdown"
            )
        
        # Notifier le conducteur
        driver = booking.trip.driver
        if driver and driver.telegram_id:
            message = (
                f"💰 *Nouveau passager confirmé !*\n\n"
                f"Un passager a payé pour votre trajet {booking.trip.departure_city} → {booking.trip.arrival_city} "
                f"le {booking.trip.departure_time.strftime('%d/%m/%Y à %H:%M')}.\n\n"
                f"Passager: {passenger.first_name if passenger else 'Inconnu'}"
            )
            await telegram_app.bot.send_message(
                chat_id=driver.telegram_id,
                text=message,
                parse_mode="Markdown"
            )
        
        logger.info(f"Paiement {custom_id} traité avec succès")
        
    except Exception as e:
        logger.error(f"Erreur traitement paiement complété: {e}")

async def handle_payment_failed(data: dict):
    """Gère un paiement PayPal échoué"""
    try:
        resource = data.get('resource', {})
        custom_id = resource.get('custom_id')
        
        if not custom_id:
            return
        
        db = get_db()
        booking = db.query(Booking).filter(Booking.id == int(custom_id)).first()
        
        if booking:
            booking.payment_status = 'failed'
            db.commit()
            
            # Notifier le passager
            passenger = booking.passenger
            if passenger and passenger.telegram_id:
                message = (
                    f"❌ *Paiement échoué*\n\n"
                    f"Le paiement pour votre réservation a échoué. "
                    f"Veuillez réessayer ou contacter le support."
                )
                await telegram_app.bot.send_message(
                    chat_id=passenger.telegram_id,
                    text=message,
                    parse_mode="Markdown"
                )
        
    except Exception as e:
        logger.error(f"Erreur traitement paiement échoué: {e}")

def verify_paypal_signature(headers: dict, body: bytes) -> bool:
    """Vérifie la signature PayPal pour la sécurité"""
    # Implémentation de la vérification de signature PayPal
    # Pour l'instant, retourne True (à implémenter selon la doc PayPal)
    return True

@app.post("/trip/complete")
async def complete_trip_and_pay(request: Request):
    """API pour finaliser un trajet et déclencher le paiement au conducteur"""
    try:
        data = await request.json()
        trip_id = data.get('trip_id')
        
        if not trip_id:
            return JSONResponse({"error": "trip_id required"}, status_code=400)
        
        # Traitement du paiement au conducteur (88% à lui, 12% commission)
        await process_driver_payment(trip_id)
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Erreur finalisation trajet: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def process_driver_payment(trip_id: int):
    """Traite le paiement au conducteur après confirmation du trajet"""
    try:
        db = get_db()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            logger.error(f"Trajet {trip_id} non trouvé")
            return
        
        # Calculer le montant total des réservations payées
        bookings = db.query(Booking).filter(
            Booking.trip_id == trip_id,
            Booking.payment_status == 'completed'
        ).all()
        
        total_amount = sum(booking.trip.price_per_seat for booking in bookings)
        driver_amount = total_amount * 0.88  # 88% au conducteur
        commission = total_amount * 0.12      # 12% de commission
        
        # Effectuer le paiement au conducteur via PayPal
        if trip.driver.paypal_email:
            success = await paypal_manager.payout_to_driver(
                trip.driver.paypal_email,
                driver_amount,
                f"Paiement trajet {trip.departure_city} → {trip.arrival_city}"
            )
            
            if success:
                # Marquer le trajet comme payé
                trip.driver_paid = True
                trip.commission_amount = commission
                trip.driver_amount = driver_amount
                db.commit()
                
                # Notifier le conducteur
                message = (
                    f"💰 *Paiement reçu !*\n\n"
                    f"Vous avez reçu {driver_amount:.2f} CHF pour votre trajet "
                    f"{trip.departure_city} → {trip.arrival_city}.\n\n"
                    f"Le paiement a été envoyé sur votre compte PayPal."
                )
                await telegram_app.bot.send_message(
                    chat_id=trip.driver.telegram_id,
                    text=message,
                    parse_mode="Markdown"
                )
        
    except Exception as e:
        logger.error(f"Erreur paiement conducteur: {e}")

@app.get("/health")
async def health_check():
    """Endpoint de santé pour Render"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    """Page d'accueil"""
    return {"message": "CovoiturageSuisse Bot is running", "status": "active"}

if __name__ == "__main__":
    logger.info(f"🚀 Démarrage du serveur sur le port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
