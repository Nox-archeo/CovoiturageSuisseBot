# CovoiturageSuisse Bot - Déploiement Render avec PayPal

Ce guide vous explique comment déployer le bot sur Render avec un système de paiement PayPal entièrement automatisé.

## 🎯 Fonctionnalités automatisées

### Processus de réservation et paiement
1. **Réservation** : Un passager réserve un trajet
2. **Paiement automatique** : Le système génère automatiquement un lien PayPal
3. **Confirmation** : Après paiement, la réservation est confirmée
4. **Notification** : Le conducteur est notifié de la nouvelle réservation

### Processus de finalisation et paiement du conducteur
1. **Rappel automatique** : 24h après la fin du trajet, rappel de confirmation
2. **Confirmation** : Le conducteur confirme que le trajet s'est bien passé
3. **Paiement automatique** : 88% du montant total est envoyé au conducteur
4. **Commission** : 12% reste comme commission de la plateforme

## 🚀 Configuration Render

### 1. Préparation du dépôt GitHub
```bash
# Assurez-vous que tous les fichiers sont commités
git add .
git commit -m "Préparation déploiement Render avec PayPal"
git push origin main
```

### 2. Configuration PayPal Developer

1. Allez sur [PayPal Developer](https://developer.paypal.com/)
2. Créez une nouvelle application
3. Notez votre `Client ID` et `Client Secret`
4. Configurez un webhook :
   - URL : `https://votre-app.onrender.com/paypal/webhook`
   - Événements : `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`
5. Notez l'ID du webhook

### 3. Création du service Render

1. Connectez-vous à [Render](https://render.com/)
2. Cliquez sur "New +" → "Web Service"
3. Connectez votre dépôt GitHub
4. Configuration :
   - **Name** : `covoiturage-suisse-bot`
   - **Environment** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `python start_render.py`

### 4. Variables d'environnement Render

Ajoutez ces variables dans les settings de votre service :

```env
# Bot Telegram
TELEGRAM_BOT_TOKEN=votre_token_bot_telegram

# Webhook (URL de votre service Render)
WEBHOOK_URL=https://votre-app.onrender.com

# PayPal Configuration
PAYPAL_CLIENT_ID=votre_client_id_paypal
PAYPAL_CLIENT_SECRET=votre_client_secret_paypal
PAYPAL_WEBHOOK_ID=votre_webhook_id_paypal
PAYPAL_MODE=sandbox  # ou 'live' pour la production

# Base de données (Render créera automatiquement une PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Optionnel : Configuration avancée
PORT=8000  # Render le définit automatiquement
PYTHON_VERSION=3.11.4
```

### 5. Configuration de la base de données

Render peut créer automatiquement une base PostgreSQL :
1. Dans votre dashboard, cliquez sur "New +" → "PostgreSQL"
2. Connectez-la à votre service web
3. L'URL sera automatiquement ajoutée comme `DATABASE_URL`

## 🔧 Configuration Bot Telegram

### 1. Webhook Telegram

Le webhook Telegram sera automatiquement configuré au démarrage :
- URL : `https://votre-app.onrender.com/webhook`

### 2. Commandes Bot

Le bot supporte ces commandes :
- `/start` - Démarrer le bot
- `/definirpaypal` - Configurer email PayPal (conducteurs)
- `/payer <id_trajet>` - Payer un trajet (passagers)
- `/confirmer <id_trajet>` - Confirmer un trajet (conducteurs)
- `/mes_reservations` - Voir ses réservations

## 💳 Flux de paiement automatisé

### Pour les passagers :
1. Recherche et réservation d'un trajet
2. **Paiement automatique** : Lien PayPal généré automatiquement
3. Confirmation instantanée après paiement
4. Notification au conducteur

### Pour les conducteurs :
1. Configuration de l'email PayPal avec `/definirpaypal`
2. Réception automatique des notifications de réservation
3. Rappel automatique 24h après le trajet
4. **Paiement automatique** après confirmation (88% du montant)

## 🛠️ Monitoring et Logs

### Endpoints de santé
- `https://votre-app.onrender.com/health` - Status du service
- `https://votre-app.onrender.com/` - Page d'accueil

### Logs importantes à surveiller
```
✅ Webhook configuré: https://votre-app.onrender.com/webhook
💰 Paiement automatique effectué pour le trajet 123
🎉 Nouvelle réservation avec paiement PayPal: booking_id=456
```

## 🔒 Sécurité

### Vérification des webhooks PayPal
Le système vérifie automatiquement :
- Signature des webhooks PayPal
- Origine des requêtes
- Intégrité des données

### Protection des données
- Emails PayPal chiffrés en base
- Tokens de session sécurisés
- Validation stricte des entrées

## 🚨 Résolution de problèmes

### Bot ne répond pas
1. Vérifiez les logs Render
2. Vérifiez que le webhook Telegram est configuré
3. Testez : `curl https://votre-app.onrender.com/health`

### Paiements PayPal échouent
1. Vérifiez les credentials PayPal
2. Vérifiez le mode (sandbox/live)
3. Vérifiez les logs du webhook PayPal

### Service se déconnecte
- Render endort les services gratuits après 15min d'inactivité
- Utilisez un service payant pour éviter cela
- Ou configurez un ping automatique

## 📞 Support

En cas de problème :
1. Vérifiez les logs dans le dashboard Render
2. Testez les endpoints manuellement
3. Vérifiez la configuration PayPal
4. Consultez la documentation Render

## 🎉 Test du déploiement

Après déploiement :
1. Tapez `/start` dans Telegram
2. Créez un trajet test
3. Réservez le trajet avec un autre compte
4. Vérifiez que le lien PayPal est généré
5. Testez le paiement en mode sandbox

Le système est maintenant entièrement automatisé ! 🚀
