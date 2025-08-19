"""
Utilitaires pour l'intégration PayPal
Gestion des paiements et transferts pour la plateforme de covoiturage
"""

import os
import time
import logging
import requests
import base64
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PayPalManager:
    """Gestionnaire pour les opérations PayPal"""
    
    def __init__(self):
        """Initialise la connexion PayPal"""
        self.client_id = os.getenv('PAYPAL_CLIENT_ID')
        self.client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
        self.mode = os.getenv('PAYPAL_MODE', 'sandbox')  # 'sandbox' ou 'live'
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Les identifiants PayPal ne sont pas configurés dans le fichier .env")
        
        # URLs API selon l'environnement
        if self.mode == 'live':
            self.base_url = "https://api.paypal.com"
        else:
            self.base_url = "https://api.sandbox.paypal.com"
            
        logger.info(f"PayPal configuré en mode {self.mode}")
    
    def get_access_token(self) -> str:
        """
        Obtient un token d'accès PayPal
        
        Returns:
            str: Token d'accès ou None si erreur
        """
        try:
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            token_headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
                "Authorization": f"Basic {encoded_credentials}"
            }
            
            token_response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=token_headers,
                data="grant_type=client_credentials"
            )
            
            if token_response.status_code == 200:
                return token_response.json()["access_token"]
            else:
                logger.error(f"Erreur token PayPal : {token_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention du token PayPal : {e}")
            return None
    
    def create_payment(self, amount: float, currency: str = "CHF", 
                      description: str = "Paiement covoiturage",
                      return_url: str = None, cancel_url: str = None,
                      custom_id: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Crée un paiement PayPal moderne avec support carte bancaire
        
        Args:
            amount: Montant du paiement
            currency: Devise (par défaut CHF)
            description: Description du paiement
            return_url: URL de retour après succès
            cancel_url: URL de retour après annulation
            custom_id: ID personnalisé pour identifier la réservation
            
        Returns:
            Tuple[success, order_id, approval_url]
        """
        try:
            # URLs par défaut si non fournies
            if not return_url:
                return_url = "https://covoituragesuissebot.onrender.com/payment/success"
            if not cancel_url:
                cancel_url = "https://covoituragesuissebot.onrender.com/payment/cancel"
            
            # Obtenir token d'accès moderne
            access_token = self.get_access_token()
            if not access_token:
                logger.error("Impossible d'obtenir le token d'accès PayPal")
                return False, None, None
            
            # Créer commande moderne avec support carte
            order_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "PayPal-Request-Id": f"covoiturage-{int(time.time())}"
            }
            
            # Configuration spéciale pour FORCER l'affichage carte bancaire ET solde PayPal
            order_data = {
                "intent": "CAPTURE",
                "application_context": {
                    "brand_name": "CovoiturageSuisse",
                    "locale": "fr-CH",
                    "landing_page": "BILLING",  # 🔥 FORCER affichage toutes options de paiement
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW",
                    "payment_method": {
                        "payee_preferred": "UNRESTRICTED",  # 🔥 ACCEPTER TOUS les types de paiement
                        "payer_selected": "PAYPAL"
                    },
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "purchase_units": [{
                    "reference_id": "covoiturage_payment",
                    "description": description,
                    "custom_id": custom_id,  # 🔥 CRUCIAL: ID de la réservation pour webhook
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}"
                    }
                }]
            }
            
            order_response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=order_headers,
                json=order_data
            )
            
            if order_response.status_code == 201:
                order = order_response.json()
                order_id = order["id"]
                
                # Trouver URL d'approbation
                approval_url = None
                for link in order.get("links", []):
                    if link["rel"] == "approve":
                        approval_url = link["href"]
                        break
                
                if approval_url:
                    logger.info(f"Commande PayPal créée avec succès : {order_id}")
                    return True, order_id, approval_url
                else:
                    logger.error("URL d'approbation non trouvée")
                    return False, None, None
            else:
                logger.error(f"Erreur création commande : {order_response.status_code}")
                logger.error(order_response.text)
                return False, None, None
                
        except Exception as e:
            logger.error(f"Erreur lors de la création du paiement PayPal : {e}")
            return False, None, None

    def capture_order(self, order_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Capture une commande PayPal approuvée
        
        Args:
            order_id: ID de la commande à capturer
            
        Returns:
            Tuple[success, capture_details]
        """
        try:
            # Obtenir token d'accès
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            token_headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
                "Authorization": f"Basic {encoded_credentials}"
            }
            
            token_response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=token_headers,
                data="grant_type=client_credentials"
            )
            
            if token_response.status_code != 200:
                logger.error(f"Erreur token PayPal : {token_response.status_code}")
                return False, None
            
            access_token = token_response.json()["access_token"]
            
            # Capturer la commande
            capture_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            capture_response = requests.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers=capture_headers
            )
            
            if capture_response.status_code == 201:
                capture_data = capture_response.json()
                logger.info(f"Commande PayPal capturée avec succès : {order_id}")
                return True, capture_data
            else:
                logger.error(f"Erreur lors de la capture : {capture_response.status_code}")
                logger.error(capture_response.text)
                return False, None
                
        except Exception as e:
            logger.error(f"Erreur lors de la capture PayPal : {e}")
            return False, None

    def refund_payment(self, capture_id: str, amount: float, currency: str = "CHF") -> Tuple[bool, Optional[Dict]]:
        """
        Effectue un remboursement PayPal
        
        Args:
            capture_id: ID de la capture à rembourser
            amount: Montant à rembourser
            currency: Devise du remboursement
            
        Returns:
            Tuple[success, refund_details]
        """
        try:
            # Obtenir token d'accès
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            token_headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
                "Authorization": f"Basic {encoded_credentials}"
            }
            
            token_response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=token_headers,
                data="grant_type=client_credentials"
            )
            
            if token_response.status_code != 200:
                logger.error(f"Erreur token PayPal : {token_response.status_code}")
                return False, None
            
            access_token = token_response.json()["access_token"]
            
            # Effectuer le remboursement
            refund_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            refund_data = {
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency_code": currency
                }
            }
            
            refund_response = requests.post(
                f"{self.base_url}/v2/payments/captures/{capture_id}/refund",
                headers=refund_headers,
                json=refund_data
            )
            
            if refund_response.status_code == 201:
                refund_result = refund_response.json()
                logger.info(f"Remboursement PayPal effectué avec succès : {refund_result['id']}")
                return True, refund_result
            else:
                logger.error(f"Erreur lors du remboursement : {refund_response.status_code}")
                logger.error(refund_response.text)
                return False, None
                
        except Exception as e:
            logger.error(f"Erreur lors du remboursement PayPal : {e}")
            return False, None

    def partial_refund(self, capture_id: str, refund_amount: float, currency: str = "CHF") -> Tuple[bool, Optional[Dict]]:
        """
        Effectue un remboursement partiel (quand plusieurs passagers se partagent un trajet)
        
        Args:
            capture_id: ID de la capture à rembourser partiellement
            refund_amount: Montant du remboursement partiel
            currency: Devise
            
        Returns:
            Tuple[success, refund_details]
        """
        return self.refund_payment(
            capture_id=capture_id,
            amount=refund_amount,
            currency=currency,
            reason=f"Remboursement partiel - Partage du trajet ({refund_amount} {currency})"
        )

    def full_refund(self, capture_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Effectue un remboursement complet (annulation de trajet)
        
        Args:
            capture_id: ID de la capture à rembourser complètement
            
        Returns:
            Tuple[success, refund_details]
        """
        return self.refund_payment(
            capture_id=capture_id,
            amount=None,  # Remboursement complet
            reason="Remboursement intégral - Annulation du trajet"
        )

    # ================================
    # PAIEMENTS AUX CONDUCTEURS
    # ================================

    def send_payout(self, recipient_email: str, amount: float, currency: str = "CHF", 
                   description: str = "Paiement covoiturage") -> Tuple[bool, Optional[Dict]]:
        """
        Envoie un paiement au conducteur via PayPal Payouts API
        
        Args:
            recipient_email: Email PayPal du conducteur
            amount: Montant à envoyer
            currency: Devise
            description: Description du paiement
            
        Returns:
            Tuple[success, payout_details]
        """
        try:
            access_token = self.get_access_token()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            # Générer un ID unique pour ce payout
            sender_batch_id = f"covoiturage_payout_{int(time.time())}"
            
            payout_data = {
                "sender_batch_header": {
                    "sender_batch_id": sender_batch_id,
                    "email_subject": "Paiement CovoiturageSuisse",
                    "email_message": f"Vous avez reçu un paiement de {amount} {currency} pour votre trajet de covoiturage."
                },
                "items": [{
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": currency
                    },
                    "receiver": recipient_email,
                    "note": description,
                    "sender_item_id": f"item_{int(time.time())}"
                }]
            }
            
            response = requests.post(
                f"{self.base_url}/v1/payments/payouts",
                headers=headers,
                json=payout_data
            )
            
            if response.status_code == 201:
                payout_result = response.json()
                batch_id = payout_result["batch_header"]["payout_batch_id"]
                
                logger.info(f"✅ Paiement envoyé au conducteur : {recipient_email}")
                logger.info(f"💰 Montant : {amount} {currency}")
                logger.info(f"🆔 Batch ID : {batch_id}")
                
                return True, {
                    "batch_id": batch_id,
                    "sender_batch_id": sender_batch_id,
                    "amount": amount,
                    "currency": currency,
                    "recipient": recipient_email,
                    "full_response": payout_result
                }
            else:
                logger.error(f"Erreur envoi paiement conducteur : {response.status_code}")
                logger.error(response.text)
                return False, None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du paiement au conducteur : {e}")
            return False, None

    def payout_to_driver(self, driver_email: str, amount: float, trip_description: str) -> Tuple[bool, Optional[Dict]]:
        """
        Envoie un paiement spécifique à un conducteur (88% du total)
        
        Args:
            driver_email: Email PayPal du conducteur
            amount: Montant à envoyer (déjà calculé à 88%)
            trip_description: Description du trajet
            
        Returns:
            Tuple[success, payout_details]
        """
        return self.send_payout(
            recipient_email=driver_email,
            amount=amount,
            currency="CHF",
            description=f"Paiement conducteur - {trip_description}"
        )

    def check_payout_status(self, batch_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Vérifie le statut d'un paiement envoyé à un conducteur
        
        Args:
            batch_id: ID du batch de paiement
            
        Returns:
            Tuple[success, status_details]
        """
        try:
            access_token = self.get_access_token()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.get(
                f"{self.base_url}/v1/payments/payouts/{batch_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                status_data = response.json()
                batch_status = status_data["batch_header"]["batch_status"]
                
                logger.info(f"✅ Statut payout {batch_id} : {batch_status}")
                
                return True, {
                    "batch_status": batch_status,
                    "batch_id": batch_id,
                    "full_response": status_data
                }
            else:
                logger.error(f"Erreur vérification statut payout : {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut payout : {e}")
            return False, None

    # ================================
    # FONCTIONS DE COMPATIBILITÉ (ANCIEN SYSTÈME)
    # ================================

    def execute_payment(self, order_id: str, payer_id: str = None) -> Tuple[bool, Optional[Dict]]:
        """
        Fonction de compatibilité - utilise maintenant capture_order
        
        Args:
            order_id: ID de la commande (nouveau système)
            payer_id: Non utilisé dans le nouveau système
            
        Returns:
            Tuple[success, payment_details]
        """
        logger.info(f"🔄 Conversion execute_payment -> capture_order pour {order_id}")
        return self.capture_order(order_id)

    def find_payment(self, payment_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Fonction de compatibilité pour retrouver un paiement
        
        Args:
            payment_id: ID du paiement/commande
            
        Returns:
            Tuple[success, payment_details]
        """
        try:
            access_token = self.get_access_token()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            # Essayer d'abord comme commande
            response = requests.get(
                f"{self.base_url}/v2/checkout/orders/{payment_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                order_data = response.json()
                logger.info(f"✅ Commande trouvée : {payment_id}")
                return True, order_data
            else:
                logger.warning(f"Commande non trouvée : {payment_id}")
                return False, None
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche du paiement : {e}")
            return False, None

# ================================
# FONCTIONS DE COMPATIBILITÉ ET RACCOURCIS
# ================================

def pay_driver(driver_email: str, trip_amount: float) -> Tuple[bool, Optional[str]]:
    """
    Fonction de raccourci pour payer un conducteur (88% du montant total)
    
    Args:
        driver_email: Email PayPal du conducteur
        trip_amount: Montant total du trajet
        
    Returns:
        Tuple[success, payout_batch_id]
    """
    try:
        paypal_manager = PayPalManager()
        
        # Calculer 88% pour le conducteur
        driver_amount = round(trip_amount * 0.88, 2)
        
        success, payout_data = paypal_manager.payout_to_driver(
            driver_email=driver_email,
            amount=driver_amount,
            trip_description=f"Paiement trajet ({trip_amount} CHF total)"
        )
        
        if success:
            batch_id = payout_data.get('batch_id')
            logger.info(f"✅ Paiement conducteur: {driver_amount} CHF envoyé à {driver_email}")
            return True, batch_id
        else:
            logger.error(f"❌ Échec paiement conducteur: {driver_email}")
            return False, None
            
    except Exception as e:
        logger.error(f"Erreur pay_driver: {e}")
        return False, None

def create_trip_payment(amount: float, description: str, return_url: str = None, cancel_url: str = None, custom_id: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Fonction de raccourci pour créer un paiement de trajet
    
    Args:
        amount: Montant du paiement
        description: Description du trajet
        return_url: URL de retour après succès
        cancel_url: URL de retour après annulation
        custom_id: ID de la réservation pour identification webhook
        
    Returns:
        Tuple[success, order_id, approval_url]
    """
    try:
        paypal_manager = PayPalManager()
        
        return paypal_manager.create_payment(
            amount=amount,
            currency="CHF",
            description=description,
            return_url=return_url,
            cancel_url=cancel_url,
            custom_id=custom_id  # 🔥 PASS CUSTOM_ID
        )
        
    except Exception as e:
        logger.error(f"Erreur create_trip_payment: {e}")
        return False, None, None

def execute_payment(payment_id: str, payer_id: str) -> Tuple[bool, Optional[Dict]]:
    """
    Fonction de compatibilité pour exécuter un paiement (capture)
    
    Args:
        payment_id: ID du paiement PayPal
        payer_id: ID du payeur
        
    Returns:
        Tuple[success, capture_data]
    """
    try:
        paypal_manager = PayPalManager()
        
        # Dans la nouvelle API, on capture directement avec l'order_id
        return paypal_manager.capture_order(payment_id)
        
    except Exception as e:
        logger.error(f"Erreur execute_payment: {e}")
        return False, None
