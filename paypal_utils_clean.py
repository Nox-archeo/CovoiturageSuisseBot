"""
Utilitaires pour l'intégration PayPal - Version propre et fonctionnelle
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
            logger.error(f"Erreur lors de la récupération du token : {e}")
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
                    "custom_id": custom_id,  # Ajouter l'ID personnalisé
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

    def find_payment(self, payment_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Trouve les détails d'un paiement PayPal par son ID
        
        Args:
            payment_id: ID du paiement PayPal
            
        Returns:
            Tuple[success, payment_details]
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False, None
            
            # Récupérer les détails du paiement/commande
            payment_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            # Essayer d'abord comme commande v2
            payment_response = requests.get(
                f"{self.base_url}/v2/checkout/orders/{payment_id}",
                headers=payment_headers
            )
            
            if payment_response.status_code == 200:
                payment_data = payment_response.json()
                logger.info(f"Détails de commande PayPal récupérés : {payment_id}")
                return True, payment_data
            else:
                # Essayer comme capture directe
                capture_response = requests.get(
                    f"{self.base_url}/v2/payments/captures/{payment_id}",
                    headers=payment_headers
                )
                
                if capture_response.status_code == 200:
                    capture_data = capture_response.json()
                    logger.info(f"Détails de capture PayPal récupérés : {payment_id}")
                    return True, capture_data
                else:
                    logger.error(f"Paiement PayPal non trouvé : {payment_id}")
                    return False, None
                    
        except Exception as e:
            logger.error(f"Erreur lors de la recherche du paiement PayPal : {e}")
            return False, None

    def capture_order(self, order_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Capture une commande PayPal approuvée
        
        Args:
            order_id: ID de la commande à capturer
            
        Returns:
            Tuple[success, capture_details]
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False, None
            
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
            access_token = self.get_access_token()
            if not access_token:
                return False, None
            
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

    async def process_refund(self, payment_id: str, refund_amount: float, recipient_email: str, reason: str = None) -> Dict[str, Any]:
        """
        Traite un remboursement automatique pour une annulation de réservation
        
        Args:
            payment_id: ID du paiement PayPal original
            refund_amount: Montant à rembourser
            recipient_email: Email PayPal du destinataire
            reason: Raison du remboursement
            
        Returns:
            Dict contenant success (bool), refund_id, error message
        """
        try:
            logger.info(f"🔄 Traitement remboursement: {refund_amount:.2f} CHF vers {recipient_email}")
            
            # Récupérer les détails du paiement pour trouver le capture_id
            success, payment_details = self.find_payment(payment_id)
            
            if not success or not payment_details:
                return {
                    'success': False,
                    'error': 'Paiement original non trouvé'
                }
            
            # Extraire le capture_id depuis les détails du paiement
            capture_id = None
            
            # Structure pour commandes v2
            if 'purchase_units' in payment_details:
                for unit in payment_details['purchase_units']:
                    if 'payments' in unit and 'captures' in unit['payments']:
                        for capture in unit['payments']['captures']:
                            if capture.get('status') == 'COMPLETED':
                                capture_id = capture['id']
                                break
                    if capture_id:
                        break
            
            if not capture_id:
                return {
                    'success': False,
                    'error': 'Aucune capture trouvée pour ce paiement'
                }
            
            logger.info(f"💡 Capture ID trouvé: {capture_id}")
            
            # Effectuer le remboursement
            success, refund_data = self.refund_payment(
                capture_id=capture_id,
                amount=refund_amount,
                currency="CHF"
            )
            
            if success and refund_data:
                return {
                    'success': True,
                    'refund_id': refund_data.get('id'),
                    'status': refund_data.get('status'),
                    'amount': refund_amount,
                    'currency': 'CHF',
                    'recipient_email': recipient_email
                }
            else:
                return {
                    'success': False,
                    'error': 'Échec du traitement PayPal'
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur process_refund: {e}")
            return {
                'success': False,
                'error': f'Erreur technique: {str(e)}'
            }

# Instance globale
paypal_manager = PayPalManager()
