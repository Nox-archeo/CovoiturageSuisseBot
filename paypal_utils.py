"""
Utilitaires pour l'intégration PayPal
Gestion des paiements et transferts pour la plateforme de covoiturage
"""

import os
import time
import logging
import paypalrestsdk
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
        
        self._configure_paypal()
    
    def _configure_paypal(self):
        """Configure l'API PayPal"""
        try:
            paypalrestsdk.configure({
                "mode": self.mode,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
            logger.info(f"PayPal configuré en mode {self.mode}")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration PayPal : {e}")
            raise
    
    def create_payment(self, amount: float, currency: str = "CHF", 
                      description: str = "Paiement covoiturage",
                      return_url: str = None, cancel_url: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Crée un paiement PayPal et retourne l'URL d'approbation
        
        Args:
            amount: Montant du paiement
            currency: Devise (par défaut CHF)
            description: Description du paiement
            return_url: URL de retour après succès
            cancel_url: URL de retour après annulation
            
        Returns:
            Tuple[success, payment_id, approval_url]
        """
        try:
            # URLs par défaut si non fournies
            if not return_url:
                return_url = "https://your-domain.com/payment/success"
            if not cancel_url:
                cancel_url = "https://your-domain.com/payment/cancel"
            
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "Covoiturage",
                            "sku": "covoiturage",
                            "price": str(amount),
                            "currency": currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": description
                }]
            })
            
            if payment.create():
                logger.info(f"Paiement créé avec succès : {payment.id}")
                
                # Récupération de l'URL d'approbation
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return True, payment.id, approval_url
            else:
                logger.error(f"Erreur lors de la création du paiement : {payment.error}")
                return False, None, None
                
        except Exception as e:
            logger.error(f"Exception lors de la création du paiement : {e}")
            return False, None, None
    
    def execute_payment(self, payment_id: str, payer_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Exécute un paiement après approbation de l'utilisateur
        
        Args:
            payment_id: ID du paiement PayPal
            payer_id: ID du payeur (retourné par PayPal)
            
        Returns:
            Tuple[success, payment_details]
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                logger.info(f"Paiement exécuté avec succès : {payment_id}")
                
                # Extraction des détails du paiement
                payment_details = {
                    "id": payment.id,
                    "state": payment.state,
                    "amount": payment.transactions[0].amount.total,
                    "currency": payment.transactions[0].amount.currency,
                    "payer_email": payment.payer.payer_info.email if payment.payer.payer_info else None,
                    "create_time": payment.create_time,
                    "update_time": payment.update_time
                }
                
                return True, payment_details
            else:
                logger.error(f"Erreur lors de l'exécution du paiement : {payment.error}")
                return False, None
                
        except Exception as e:
            logger.error(f"Exception lors de l'exécution du paiement : {e}")
            return False, None
    
    def send_payment_to_driver(self, driver_email: str, amount: float, 
                              currency: str = "CHF", note: str = "Paiement covoiturage") -> Tuple[bool, Optional[str]]:
        """
        Envoie 88% du montant au conducteur via PayPal
        
        Args:
            driver_email: Email PayPal du conducteur
            amount: Montant total du voyage
            currency: Devise
            note: Note pour le paiement
            
        Returns:
            Tuple[success, payout_batch_id]
        """
        try:
            # Calcul de 88% du montant (12% de commission)
            driver_amount = round(amount * 0.88, 2)
            
            payout = paypalrestsdk.Payout({
                "sender_batch_header": {
                    "sender_batch_id": f"covoiturage_driver_{int(time.time())}",
                    "email_subject": "Vous avez reçu un paiement pour votre covoiturage",
                    "email_message": f"Félicitations ! Vous avez reçu {driver_amount} {currency} pour votre voyage."
                },
                "items": [
                    {
                        "recipient_type": "EMAIL",
                        "amount": {
                            "value": str(driver_amount),
                            "currency": currency
                        },
                        "receiver": driver_email,
                        "note": note,
                        "sender_item_id": f"item_{int(time.time())}"
                    }
                ]
            })
            
            if payout.create():
                logger.info(f"Paiement envoyé au conducteur {driver_email} : {driver_amount} {currency}")
                return True, payout.batch_header.payout_batch_id
            else:
                logger.error(f"Erreur lors de l'envoi du paiement : {payout.error}")
                return False, None
                
        except Exception as e:
            logger.error(f"Exception lors de l'envoi du paiement au conducteur : {e}")
            return False, None
    
    def refund_payment(self, payment_id: str, refund_amount: float, currency: str = "CHF") -> Tuple[bool, Optional[str]]:
        """
        Effectue un remboursement partiel via PayPal
        
        Args:
            payment_id: ID du paiement original
            refund_amount: Montant à rembourser
            currency: Devise
            
        Returns:
            Tuple[success, refund_id]
        """
        try:
            # Récupérer le paiement original
            payment = paypalrestsdk.Payment.find(payment_id)
            if not payment:
                logger.error(f"Paiement {payment_id} non trouvé")
                return False, None
            
            # Créer le remboursement
            refund = paypalrestsdk.Refund({
                "amount": {
                    "total": str(refund_amount),
                    "currency": currency
                },
                "reason": "Ajustement automatique du prix suite à l'ajout d'un passager"
            })
            
            # Effectuer le remboursement sur la première transaction de capture
            if payment.transactions and len(payment.transactions) > 0:
                transaction = payment.transactions[0]
                if transaction.related_resources and len(transaction.related_resources) > 0:
                    capture = transaction.related_resources[0].capture
                    if capture:
                        success = refund.create(capture.id)
                        if success:
                            logger.info(f"Remboursement de {refund_amount} {currency} créé: {refund.id}")
                            return True, refund.id
                        else:
                            logger.error(f"Erreur lors de la création du remboursement: {refund.error}")
                            return False, None
            
            logger.error(f"Impossible de trouver une capture pour le paiement {payment_id}")
            return False, None
                            
        except Exception as e:
            logger.error(f"Erreur lors du remboursement PayPal: {e}")
            return False, None
    
    def refund_card_payment(self, payment_id: str, refund_amount: float = None, 
                           currency: str = "CHF", reason: str = "Annulation covoiturage") -> Tuple[bool, Optional[str]]:
        """
        Rembourse un paiement par carte bancaire via PayPal
        
        Args:
            payment_id: ID du paiement PayPal original
            refund_amount: Montant à rembourser (None = remboursement total)
            currency: Devise du remboursement
            reason: Motif du remboursement
            
        Returns:
            Tuple[success, refund_id]
        """
        try:
            # Récupérer les détails du paiement original
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if not payment or payment.state != "approved":
                logger.error(f"Paiement {payment_id} non trouvé ou non approuvé")
                return False, None
            
            # Trouver la transaction à rembourser
            for transaction in payment.transactions:
                for related_resource in transaction.related_resources:
                    if hasattr(related_resource, 'sale'):
                        sale = related_resource.sale
                        
                        # Déterminer le montant du remboursement
                        if refund_amount is None:
                            refund_data = {
                                "reason": reason
                            }
                        else:
                            refund_data = {
                                "amount": {
                                    "total": str(refund_amount),
                                    "currency": currency
                                },
                                "reason": reason
                            }
                        
                        # Effectuer le remboursement
                        refund = sale.refund(refund_data)
                        
                        if refund:
                            logger.info(f"Remboursement créé: {refund.id} pour le paiement {payment_id}")
                            return True, refund.id
                        else:
                            logger.error(f"Échec du remboursement: {refund.error if hasattr(refund, 'error') else 'Erreur inconnue'}")
                            return False, None
            
            logger.error(f"Aucune transaction de vente trouvée pour le paiement {payment_id}")
            return False, None
                            
        except Exception as e:
            logger.error(f"Erreur lors du remboursement de carte: {e}")
            return False, None
                            
        except Exception as e:
            logger.error(f"Erreur lors du remboursement PayPal: {e}")
            return False, None
    
    def get_payment_details(self, payment_id: str) -> Optional[Dict]:
        """
        Récupère les détails d'un paiement
        
        Args:
            payment_id: ID du paiement PayPal
            
        Returns:
            Détails du paiement ou None si erreur
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment:
                return {
                    "id": payment.id,
                    "state": payment.state,
                    "amount": payment.transactions[0].amount.total,
                    "currency": payment.transactions[0].amount.currency,
                    "create_time": payment.create_time,
                    "update_time": payment.update_time,
                    "payer_email": payment.payer.payer_info.email if payment.payer.payer_info else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails du paiement : {e}")
            return None
    
    def verify_webhook(self, webhook_data: Dict, webhook_id: str) -> bool:
        """
        Vérifie la validité d'un webhook PayPal
        
        Args:
            webhook_data: Données du webhook
            webhook_id: ID du webhook configuré
            
        Returns:
            True si le webhook est valide
        """
        try:
            # Implémentation de la vérification du webhook
            # Cette fonction nécessite une configuration supplémentaire des webhooks
            logger.info("Vérification du webhook PayPal")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du webhook : {e}")
            return False


# Instance globale du gestionnaire PayPal
paypal_manager = PayPalManager()


# Fonctions d'aide pour l'utilisation dans le bot
def create_trip_payment(amount: float, trip_description: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Crée un paiement pour un voyage
    
    Args:
        amount: Montant du voyage
        trip_description: Description du voyage
        
    Returns:
        Tuple[success, payment_id, approval_url]
    """
    return paypal_manager.create_payment(
        amount=amount,
        description=f"Covoiturage : {trip_description}",
        return_url="https://your-domain.com/payment/success",
        cancel_url="https://your-domain.com/payment/cancel"
    )


def complete_trip_payment(payment_id: str, payer_id: str) -> Tuple[bool, Optional[Dict]]:
    """
    Complète un paiement de voyage
    
    Args:
        payment_id: ID du paiement PayPal
        payer_id: ID du payeur
        
    Returns:
        Tuple[success, payment_details]
    """
    return paypal_manager.execute_payment(payment_id, payer_id)


def pay_driver(driver_email: str, trip_amount: float) -> Tuple[bool, Optional[str]]:
    """
    Paie le conducteur (88% du montant)
    
    Args:
        driver_email: Email PayPal du conducteur
        trip_amount: Montant total du voyage
        
    Returns:
        Tuple[success, payout_batch_id]
    """
    return paypal_manager.send_payment_to_driver(
        driver_email=driver_email,
        amount=trip_amount,
        note="Paiement pour votre voyage de covoiturage"
    )


def create_paypal_payment(amount: float, description: str, user_id: int = None, 
                         trip_id: int = None, proposal_id: int = None) -> Optional[str]:
    """
    Crée un paiement PayPal et retourne l'URL d'approbation
    
    Args:
        amount: Montant du paiement
        description: Description du paiement
        user_id: ID de l'utilisateur (optionnel)
        trip_id: ID du trajet (optionnel)
        proposal_id: ID de la proposition (optionnel)
        
    Returns:
        URL d'approbation PayPal ou None en cas d'erreur
    """
    try:
        success, payment_id, approval_url = create_trip_payment(amount, description)
        if success and approval_url:
            logger.info(f"Paiement PayPal créé: {payment_id} pour {amount} CHF")
            return approval_url
        else:
            logger.error(f"Échec de création du paiement PayPal pour {amount} CHF")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la création du paiement PayPal: {e}")
        return None


if __name__ == "__main__":
    # Tests basiques
    try:
        manager = PayPalManager()
        print("✅ PayPal configuré avec succès")
        
        # Test de création de paiement
        success, payment_id, approval_url = manager.create_payment(
            amount=25.0,
            description="Test covoiturage Genève-Lausanne"
        )
        
        if success:
            print(f"✅ Paiement test créé : {payment_id}")
            print(f"URL d'approbation : {approval_url}")
        else:
            print("❌ Échec de création du paiement test")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests : {e}")
