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
    
    def create_payment(self, amount: float, currency: str = "CHF", 
                      description: str = "Paiement covoiturage",
                      return_url: str = None, cancel_url: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Crée un paiement PayPal moderne avec support carte bancaire
        
        Args:
            amount: Montant du paiement
            currency: Devise (par défaut CHF)
            description: Description du paiement
            return_url: URL de retour après succès
            cancel_url: URL de retour après annulation
            
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
                return False, None, None
            
            access_token = token_response.json()["access_token"]
            
            # Créer commande moderne avec support carte
            order_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "PayPal-Request-Id": f"covoiturage-{int(time.time())}"
            }
            
            order_data = {
                "intent": "CAPTURE",
                "application_context": {
                    "brand_name": "CovoiturageSuisse",
                    "locale": "fr-CH",
                    "landing_page": "LOGIN",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW",
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "purchase_units": [{
                    "reference_id": "covoiturage_payment",
                    "description": description,
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
