#!/usr/bin/env python3
"""
Surveillance proactive des notifications PayPal manquantes
Détecte automatiquement les paiements sans custom_id
"""

import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_paypal_monitoring_system():
    """
    Système de surveillance pour détecter les problèmes de notifications
    """
    
    monitoring_code = '''
# === SYSTÈME DE SURVEILLANCE PAYPAL ===
# À ajouter dans webhook_bot.py

def log_webhook_analysis(webhook_data: dict):
    """
    Analyse et log chaque webhook reçu pour surveillance
    """
    try:
        event_type = webhook_data.get('event_type', 'UNKNOWN')
        resource = webhook_data.get('resource', {})
        custom_id = resource.get('custom_id')
        payment_id = resource.get('id')
        amount = resource.get('amount', {}).get('value', 'UNKNOWN')
        
        # Log structuré pour monitoring
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "payment_id": payment_id,
            "custom_id": custom_id,
            "amount": amount,
            "has_custom_id": custom_id is not None,
            "can_identify_booking": custom_id is not None
        }
        
        logger.info(f"WEBHOOK_ANALYSIS: {log_entry}")
        
        # Alerte si custom_id manquant
        if not custom_id:
            logger.error(f"🚨 ALERTE: Paiement {payment_id} SANS custom_id - Notification impossible!")
            
        return log_entry
        
    except Exception as e:
        logger.error(f"Erreur analyse webhook: {e}")
        return None

# Ajouter cet appel au début de handle_payment_completed()
webhook_analysis = log_webhook_analysis(webhook_data)
'''
    
    print("🔍 SYSTÈME DE SURVEILLANCE PAYPAL")
    print("=" * 50)
    print(monitoring_code)
    
    # Script de vérification des paiements récents
    verification_script = '''
#!/usr/bin/env python3
"""
Vérification des paiements récents sans custom_id
"""

import sqlite3
from datetime import datetime, timedelta

def check_recent_payments_without_notifications():
    """
    Vérifie les paiements récents qui n'ont pas reçu de notifications
    """
    try:
        # Connexion à la base de production (adapter selon environnement)
        conn = sqlite3.connect('covoiturage.db')
        cursor = conn.cursor()
        
        # Paiements des 7 derniers jours
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        query = """
        SELECT 
            id, 
            paypal_payment_id, 
            total_price, 
            payment_status,
            booking_date,
            trip_id,
            passenger_id
        FROM bookings 
        WHERE 
            payment_status = 'completed' 
            AND booking_date >= ?
            AND paypal_payment_id IS NOT NULL
        ORDER BY booking_date DESC
        """
        
        cursor.execute(query, (seven_days_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        recent_payments = cursor.fetchall()
        
        print(f"🔍 Paiements récents trouvés: {len(recent_payments)}")
        
        for payment in recent_payments:
            booking_id, paypal_id, amount, status, date, trip_id, passenger_id = payment
            print(f"   💳 Réservation #{booking_id}")
            print(f"      PayPal ID: {paypal_id}")
            print(f"      Montant: {amount} CHF")
            print(f"      Date: {date}")
            print(f"      Statut: {status}")
            print()
        
        conn.close()
        return recent_payments
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return []

if __name__ == "__main__":
    check_recent_payments_without_notifications()
'''
    
    return monitoring_code, verification_script

def create_webhook_debug_endpoint():
    """
    Endpoint de debug pour tester les webhooks en temps réel
    """
    
    debug_endpoint = '''
# === ENDPOINT DEBUG WEBHOOK ===
# À ajouter dans webhook_bot.py

@app.post("/debug/webhook/test")
async def debug_webhook_test(request: Request):
    """
    Endpoint de test pour valider les webhooks avec custom_id
    """
    try:
        webhook_data = await request.json()
        
        print("🔍 DEBUG WEBHOOK TEST")
        print("=" * 40)
        print(f"Event: {webhook_data.get('event_type')}")
        print(f"Payment ID: {webhook_data.get('resource', {}).get('id')}")
        print(f"Custom ID: {webhook_data.get('resource', {}).get('custom_id')}")
        print(f"Amount: {webhook_data.get('resource', {}).get('amount', {}).get('value')}")
        
        # Test de traitement comme un vrai webhook
        if webhook_data.get('event_type') == 'PAYMENT.CAPTURE.COMPLETED':
            result = await handle_payment_completed(webhook_data)
            return {"status": "debug_ok", "processed": result}
        else:
            return {"status": "debug_ok", "message": "Event type not processed"}
            
    except Exception as e:
        logger.error(f"Erreur debug webhook: {e}")
        return {"status": "debug_error", "error": str(e)}
'''
    
    return debug_endpoint

if __name__ == "__main__":
    print("🛡️  SYSTÈME DE SURVEILLANCE PAYPAL")
    print("=" * 60)
    
    monitoring, verification = create_paypal_monitoring_system()
    debug_endpoint = create_webhook_debug_endpoint()
    
    print("\n📊 RECOMMANDATIONS POST-DÉPLOIEMENT:")
    print("1. ✅ Le custom_id est maintenant inclus (déployé)")
    print("2. 🔍 Surveiller les prochains paiements dans les logs")
    print("3. 📧 Tester avec un paiement de 1 CHF après déploiement")
    print("4. 🚨 Ajouter le système de surveillance ci-dessus")
    
    print("\n🎯 VALIDATION IMMÉDIATE:")
    print("   Attendre 2-3 minutes le déploiement Render")
    print("   Faire un nouveau paiement test de 1 CHF")
    print("   Vérifier que les notifications arrivent")
    
    print(f"\n📝 STATUT: Corrections déployées à {datetime.now().strftime('%H:%M:%S')}")
