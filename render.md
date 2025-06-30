# Configuration pour le déploiement sur Render

# Variables d'environnement nécessaires:
# TELEGRAM_BOT_TOKEN=votre_token_telegram
# WEBHOOK_URL=https://votre-service.onrender.com
# PAYPAL_CLIENT_ID=votre_client_id_paypal
# PAYPAL_CLIENT_SECRET=votre_client_secret_paypal
# PAYPAL_WEBHOOK_ID=votre_webhook_id_paypal
# DATABASE_URL=votre_url_base_de_donnees
# PORT=8000 (défini automatiquement par Render)

# Pour configurer les webhooks PayPal:
# 1. Allez sur https://developer.paypal.com/
# 2. Créez une application
# 3. Configurez un webhook avec l'URL: https://votre-service.onrender.com/paypal/webhook
# 4. Sélectionnez les événements: PAYMENT.CAPTURE.COMPLETED, PAYMENT.CAPTURE.DENIED
# 5. Copiez l'ID du webhook dans PAYPAL_WEBHOOK_ID

# Pour déployer:
# 1. Connectez votre dépôt GitHub à Render
# 2. Créez un nouveau Web Service
# 3. Définissez la commande de build: pip install -r requirements.txt
# 4. Définissez la commande de démarrage: python webhook_bot.py
# 5. Ajoutez toutes les variables d'environnement ci-dessus
