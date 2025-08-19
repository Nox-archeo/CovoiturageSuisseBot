#!/usr/bin/env python3
"""
VÉRIFICATION - Configuration appliquée au bon bot ?
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("""
🔍 VÉRIFICATION CONFIGURATION PAYPAL
====================================

⚠️ QUESTION IMPORTANTE : La configuration que vous venez de faire 
   s'applique-t-elle bien à votre BOT DE COVOITURAGE ?

🔧 VÉRIFICATION DES IDENTIFIANTS :

""")

# Vérification des identifiants actuels du bot
client_id = os.getenv('PAYPAL_CLIENT_ID', 'NON CONFIGURÉ')
client_secret = os.getenv('PAYPAL_CLIENT_SECRET', 'NON CONFIGURÉ')
mode = os.getenv('PAYPAL_MODE', 'sandbox')

print(f"   CLIENT_ID actuel du bot : {client_id[:20]}...")
print(f"   MODE actuel du bot : {mode}")
print()

print("""
🎯 COMPARAISON AVEC LA CONFIGURATION PAYPAL :

   Dans PayPal vous avez vu :
   Clé API : ATAZVDGqQL7xNGUAT0mg9J0Y0dUAJAaTgC_8vR0On9cAHaUIKy3U1W3ofmaZ4IcFWdjMvDd6bQy4fRVl

   Dans votre bot (.env) vous avez :
""")
print(f"   PAYPAL_CLIENT_ID = {client_id}")
print()

if "ATAZVDGqQL7xNGUAT0mg9J0Y0dUAJAaTgC" in client_id:
    print("✅ PARFAIT ! Les identifiants correspondent !")
    print("   → La configuration PayPal s'applique bien à votre bot covoiturage")
else:
    print("❌ ATTENTION ! Les identifiants ne correspondent pas !")
    print("   → Vous avez peut-être configuré une autre app PayPal")
    print("   → Il faut vérifier quelle app PayPal vous utilisez")

print("""

🚨 SI LES IDENTIFIANTS NE CORRESPONDENT PAS :

1️⃣ RETOURNEZ DANS PAYPAL
   • Vérifiez que vous êtes dans la bonne app
   • Peut-être avez-vous 2 apps : covoiturage + autre

2️⃣ VÉRIFIEZ QUELLE APP VOUS UTILISEZ
   • Dans PayPal, regardez le nom de l'app
   • Est-ce bien "covoiturage" ou "CovoiturageSuisse" ?

3️⃣ SI VOUS AVEZ CONFIGURÉ LA MAUVAISE APP
   • Refaites la même configuration
   • Mais sur la bonne app cette fois

🎯 POUR ÊTRE SÛR :
   Testez maintenant avec votre bot réel !
   Créez un trajet de test et voyez si l'option carte apparaît.

""")

def help_verification():
    """Guide pour vérifier la configuration"""
    print("💡 CONSEIL :")
    print("   La meilleure façon de vérifier : testez votre bot réel")
    print("   avec un trajet et regardez si l'option carte apparaît !")

if __name__ == "__main__":
    help_verification()
