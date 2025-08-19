#!/usr/bin/env python3
"""
PayPal Modern Integration - Nouveau système PayPal Checkout
Compatible avec les paiements par carte sans compte PayPal
Utilise l'API PayPal Orders v2 (moderne)
"""

import os
import requests
import base64
import json
import logging
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PayPalModernManager:
    """Gestionnaire moderne pour PayPal avec support carte bancaire"""
    
    def __init__(self):
        """Initialise la connexion PayPal moderne"""
        self.client_id = os.getenv('PAYPAL_CLIENT_ID')
        self.client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
        self.mode = os.getenv('PAYPAL_MODE', 'sandbox')  # 'sandbox' ou 'live'
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Les identifiants PayPal ne sont pas configurés dans le fichier .env")
        
        # URLs API selon l'environnement
        if self.mode == 'live':
            self.base_url = "https://api.paypal.com"
            self.checkout_url = "https://www.paypal.com/checkoutnow"
        else:
            self.base_url = "https://api.sandbox.paypal.com"
            self.checkout_url = "https://www.sandbox.paypal.com/checkoutnow"
            
        self.access_token = None
        logger.info(f"PayPal Modern configuré en mode {self.mode}")
    
    def get_access_token(self) -> str:
        """Obtient un token d'accès OAuth2"""
        try:
            # Encodage des credentials
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
                "Authorization": f"Basic {encoded_credentials}"
            }
            
            data = "grant_type=client_credentials"
            
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                logger.info("Token d'accès PayPal obtenu avec succès")
                return self.access_token
            else:
                logger.error(f"Erreur lors de l'obtention du token : {response.status_code}")
                logger.error(response.text)
                raise Exception(f"Impossible d'obtenir le token PayPal : {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification PayPal : {e}")
            raise
    
    def create_order(self, amount: float, currency: str = "CHF", 
                    description: str = "Paiement covoiturage",
                    return_url: str = None, cancel_url: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Crée une commande PayPal moderne avec support carte bancaire
        
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
            # Obtenir le token d'accès
            if not self.access_token:
                self.get_access_token()
            
            # URLs par défaut si non fournies
            if not return_url:
                return_url = "https://covoituragesuissebot.onrender.com/payment/success"
            if not cancel_url:
                cancel_url = "https://covoituragesuissebot.onrender.com/payment/cancel"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "PayPal-Request-Id": f"covoiturage-{int(time.time())}"
            }
            
            # Structure de commande moderne PayPal
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
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=headers,
                json=order_data
            )
            
            if response.status_code == 201:
                order = response.json()
                order_id = order["id"]
                
                # Trouver l'URL d'approbation
                approval_url = None
                for link in order.get("links", []):
                    if link["rel"] == "approve":
                        approval_url = link["href"]
                        break
                
                if approval_url:
                    logger.info(f"Commande PayPal créée avec succès : {order_id}")
                    return True, order_id, approval_url
                else:
                    logger.error("URL d'approbation non trouvée dans la réponse")
                    return False, None, None
                    
            else:
                logger.error(f"Erreur lors de la création de la commande : {response.status_code}")
                logger.error(response.text)
                return False, None, None
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de la commande PayPal : {e}")
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
            if not self.access_token:
                self.get_access_token()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers=headers
            )
            
            if response.status_code == 201:
                capture_data = response.json()
                logger.info(f"Commande PayPal capturée avec succès : {order_id}")
                return True, capture_data
            else:
                logger.error(f"Erreur lors de la capture : {response.status_code}")
                logger.error(response.text)
                return False, None
                
        except Exception as e:
            logger.error(f"Erreur lors de la capture PayPal : {e}")
            return False, None

# Import nécessaire pour la compatibilité
import time

if __name__ == "__main__":
    print("🚀 TEST - PayPal Modern Manager")
    print("=" * 50)
    
    try:
        manager = PayPalModernManager()
        
        print("🔄 Création d'une commande de test...")
        success, order_id, approval_url = manager.create_order(
            amount=1.00,
            currency="CHF",
            description="Test paiement carte moderne",
            return_url="https://covoituragesuissebot.onrender.com/payment/test/success",
            cancel_url="https://covoituragesuissebot.onrender.com/payment/test/cancel"
        )
        
        if success and approval_url:
            print("✅ Commande créée avec succès !")
            print(f"   Order ID: {order_id}")
            print(f"   URL de paiement: {approval_url}")
            print()
            print("🎯 TESTEZ CETTE URL EN NAVIGATION PRIVÉE :")
            print(f"   {approval_url}")
            print()
            print("💳 VOUS DEVRIEZ VOIR L'OPTION CARTE BANCAIRE !")
        else:
            print("❌ Erreur lors de la création de la commande")
            
    except Exception as e:
        print(f"⚠️ Erreur : {e}")
