#!/usr/bin/env python3
"""
GUIDE - Comment choisir la bonne app PayPal
"""

print("""
🔍 GUIDE POUR TROUVER LA BONNE APP PAYPAL
=========================================

✅ VOUS AVEZ RAISON ! Il faut aller sur le tableau de bord DÉVELOPPEUR !

📋 ÉTAPES PRÉCISES :

1️⃣ ALLER SUR LE TABLEAU DE BORD DÉVELOPPEUR :
   • URL : https://developer.paypal.com/dashboard/
   • Connectez-vous avec votre compte PayPal

2️⃣ SECTION "APPLICATIONS ET IDENTIFIANTS" :
   • Sur la gauche : cliquez "Applications et identifiants"
   • OU "Applications and credentials"

3️⃣ VÉRIFIER LE MODE :
   • En haut : assurez-vous d'être en mode "Live" (pas Sandbox)
   • Votre bot utilise le mode LIVE

4️⃣ VOIR TOUTES VOS APPS :
   Vous devriez voir une liste comme :
   
   📱 App 1: "Default Application"
      Client ID: AYdK4-rJwHJ0tt286aVh... ← CELLE DE VOTRE BOT !
      
   📱 App 2: "Autre App" 
      Client ID: ATAZVDGqQL7xNGUAT0mg... ← Celle que vous venez de configurer

5️⃣ IDENTIFIER LA BONNE APP :
   • Cherchez l'app avec l'ID : AYdK4-rJwHJ0tt286aVh...
   • C'est celle utilisée par votre bot covoiturage !

6️⃣ CONFIGURER LA BONNE APP :
   • Cliquez sur cette app
   • Suivez le même processus qu'avant
   • Mais cette fois sur la BONNE app !

🎯 CE QUE VOUS CHERCHEZ DANS LES APPS :

   App correcte = Client ID commence par : AYdK4-rJwHJ0tt286aVh
   
   Cette app doit avoir :
   • Le nom de votre bot (covoiturage, telegram, etc.)
   • Status "Live"
   • Les bonnes permissions

🔧 UNE FOIS LA BONNE APP TROUVÉE :

   1. Cliquez dessus
   2. Cherchez "Features" ou "Caractéristiques" 
   3. Activez "Accept Payments" ou "Accepter les paiements"
   4. Puis "Advanced Credit and Debit Card Payments"
   5. OU cherchez "Guest Checkout" dans les paramètres

⚠️ IMPORTANT :
   Si vous ne trouvez que une seule app, c'est que la deuxième
   était peut-être sur votre autre compte PayPal (celui des abonnements).

🎯 OBJECTIF :
   Configurer l'app qui a l'ID : AYdK4-rJwHJ0tt286aVh...
   pour qu'elle accepte les paiements par carte !

""")

def guide_apps():
    """Guide pour naviguer dans les apps PayPal"""
    print("💡 ASTUCE :")
    print("   Si vous voyez plusieurs apps, regardez leur nom")
    print("   et leur date de création pour identifier celle du covoiturage !")

if __name__ == "__main__":
    guide_apps()
