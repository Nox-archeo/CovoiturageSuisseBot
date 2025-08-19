#!/usr/bin/env python3
"""
Script pour forcer le traitement de votre paiement de 1 CHF spécifiquement
"""

import asyncio
import sys
import os
sys.path.append('/Users/margaux/CovoiturageSuisse')

from paypal_webhook_handler import handle_payment_completion

async def force_your_1chf_payment():
    """
    Force le traitement de votre paiement de 1 CHF
    """
    print("🔧 FORCE TRAITEMENT PAIEMENT 1 CHF")
    print("=" * 40)
    
    # Vous devez remplacer par l'ID PayPal réel de votre paiement
    # Vous pouvez le trouver dans votre compte PayPal ou dans les logs
    
    paypal_payment_id = input("Entrez l'ID PayPal de votre paiement de 1 CHF: ")
    
    if not paypal_payment_id:
        print("❌ ID PayPal requis")
        return
    
    print(f"🚀 Traitement forcé du paiement: {paypal_payment_id}")
    
    # Simuler le webhook pour ce paiement
    result = await handle_payment_completion(paypal_payment_id, bot=None)
    
    if result:
        print("✅ SUCCÈS! Votre paiement a été traité!")
        print("   - Réservation confirmée")
        print("   - Statut mis à jour")
        print("   - Notifications envoyées (si bot connecté)")
    else:
        print("❌ Échec du traitement")
        print("   Vérifiez l'ID PayPal ou contactez le support")

if __name__ == "__main__":
    asyncio.run(force_your_1chf_payment())
