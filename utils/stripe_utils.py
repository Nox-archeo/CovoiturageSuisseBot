import os
import stripe
import logging
from datetime import datetime

# Configuration du logger
logger = logging.getLogger(__name__)

# Configuration de Stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')

# Constantes
PLATFORM_FEE_PERCENTAGE = 12  # 12% de commission pour la plateforme

async def create_checkout_session(trip, passenger, seats=1, success_url=None, cancel_url=None):
    """
    Crée une session de paiement Stripe pour la réservation d'un trajet.
    
    Args:
        trip: L'objet Trip représentant le trajet à réserver
        passenger: L'objet User représentant le passager qui fait la réservation
        seats: Le nombre de places à réserver
        success_url: URL de redirection en cas de succès
        cancel_url: URL de redirection en cas d'annulation
    
    Returns:
        L'URL de la session de paiement Stripe ou None en cas d'erreur
    """
    try:
        # Vérifier que le conducteur a un compte Stripe
        from database import get_db
        db = get_db()
        driver = db.query('User').get(trip.driver_id)
        
        if not driver.stripe_account_id:
            logger.error(f"Le conducteur (ID: {trip.driver_id}) n'a pas de compte Stripe")
            return None
            
        # Calculer le montant total et la commission
        amount = int(trip.price_per_seat * seats * 100)  # Conversion en centimes
        application_fee = int(amount * PLATFORM_FEE_PERCENTAGE / 100)
        
        # Créer une session de paiement avec Stripe Connect
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'chf',
                    'product_data': {
                        'name': f'Trajet de {trip.departure_city} à {trip.arrival_city}',
                        'description': f'Départ le {trip.departure_time.strftime("%d/%m/%Y à %H:%M")}',
                    },
                    'unit_amount': int(trip.price_per_seat * 100),  # En centimes
                },
                'quantity': seats,
            }],
            mode='payment',
            success_url=success_url or 'https://t.me/VotreBot',
            cancel_url=cancel_url or 'https://t.me/VotreBot',
            payment_intent_data={
                'application_fee_amount': application_fee,
                'transfer_data': {
                    'destination': driver.stripe_account_id,
                },
                'metadata': {
                    'trip_id': trip.id,
                    'passenger_id': passenger.id,
                    'seats': seats,
                    'booking_date': datetime.now().isoformat()
                }
            },
            metadata={
                'trip_id': trip.id,
                'passenger_id': passenger.id,
                'seats': seats,
                'booking_date': datetime.now().isoformat()
            }
        )
        
        # Retourner l'URL de la session de paiement
        return checkout_session.url
        
    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe lors de la création de la session de paiement: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la création de la session de paiement: {str(e)}")
        return None

async def create_onboarding_link(user, redirect_url=None):
    """
    Crée un lien d'onboarding Stripe Connect Express pour un conducteur.
    
    Args:
        user: L'objet User représentant le conducteur
        redirect_url: URL de redirection après l'onboarding
    
    Returns:
        L'URL du lien d'onboarding Stripe ou None en cas d'erreur
    """
    try:
        # Créer ou récupérer un compte Stripe Connect pour le conducteur
        if user.stripe_account_id:
            account = stripe.Account.retrieve(user.stripe_account_id)
        else:
            # Créer un nouveau compte Stripe Connect Express
            account = stripe.Account.create(
                type='express',
                country='CH',
                email=user.email,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
                metadata={
                    'user_id': user.id,
                    'telegram_id': user.telegram_id
                }
            )
            
            # Sauvegarder l'ID du compte Stripe dans la base de données
            from database import get_db
            db = get_db()
            user.stripe_account_id = account.id
            db.commit()
        
        # Créer un lien d'onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=redirect_url or 'https://t.me/VotreBot',
            return_url=redirect_url or 'https://t.me/VotreBot',
            type='account_onboarding',
        )
        
        return account_link.url
        
    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe lors de la création du lien d'onboarding: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la création du lien d'onboarding: {str(e)}")
        return None

async def check_driver_stripe_account(user):
    """
    Vérifie si un conducteur a un compte Stripe actif et correctement configuré.
    
    Args:
        user: L'objet User représentant le conducteur
    
    Returns:
        True si le compte est actif, False sinon
    """
    if not user.stripe_account_id:
        return False
    
    try:
        account = stripe.Account.retrieve(user.stripe_account_id)
        return account.charges_enabled and account.payouts_enabled
    except stripe.error.StripeError:
        return False
