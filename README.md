# CovoiturageSuisse - Bot Telegram

Ce bot Telegram permet de gérer une plateforme de covoiturage en Suisse. Il offre des fonctionnalités pour créer, rechercher et gérer des trajets.

## Fonctionnalités principales

### Création de trajets
- **En tant que conducteur** : proposez vos trajets avec tous les détails (points de départ/arrivée, date, heure, places disponibles, tarif, etc.)
- **En tant que passager** : créez des demandes de trajet pour que les conducteurs puissent vous contacter
- **Préférences de trajet** : indiquez vos préférences (fumeur/non-fumeur, musique, animaux, etc.)
- **Trajets réguliers** : configurez des trajets récurrents (ex: trajets domicile-travail)

### Recherche de trajets
- **Filtres avancés** : recherchez des trajets selon divers critères
- **Sélection géographique** : recherche par ville ou région
- **Filtres de date et heure** : plages horaires flexibles
- **Préférences personnalisées** : filtrez selon vos besoins spécifiques

### Gestion des trajets
- **Réservation** : réservez des places directement via le bot
- **Paiement** : système intégré de traitement des paiements
- **Confirmations** : système de confirmation automatique
- **Évaluations** : notez vos covoitureurs après le trajet

## Architecture technique

Le bot est structuré de manière modulaire pour faciliter la maintenance et les évolutions:

- **Modules principaux**:
  - `utils/`: Composants d'interface utilisateur réutilisables (date_picker, location_picker)
  - `handlers/`: Gestion des commandes et interactions
    - `trip_creation/`: Création de trajets (conducteur/passager)
    - `trip_search/`: Recherche avancée de trajets
    - `preferences/`: Gestion des préférences utilisateurs
  - `database/`: Interaction avec la base de données
  - `models/`: Modèles de données

## Commandes disponibles

- `/start` - Démarrer le bot et afficher le menu principal
- `/creer` - Proposer un nouveau trajet en tant que conducteur
- `/demander` - Créer une demande de trajet en tant que passager
- `/chercher` - Rechercher un trajet avec filtres avancés
- `/mes_trajets` - Voir vos trajets actifs et historique
- `/profil` - Gérer votre profil et préférences
- `/annuler` - Annuler l'opération en cours

## Installation et configuration

1. Cloner ce dépôt
2. Installer les dépendances: `pip install -r requirements.txt`
3. Configurer les variables d'environnement (fichier `.env`):
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```
4. Initialiser la base de données: `python init_db.py`
5. Démarrer le bot: `python bot.py`

## Contribution

Les contributions sont les bienvenues! Vous pouvez contribuer en:
1. Signalant des problèmes (issues)
2. Proposant des améliorations via des pull requests
3. Améliorant la documentation

## Licence

Ce projet est sous licence [MIT](LICENSE).
