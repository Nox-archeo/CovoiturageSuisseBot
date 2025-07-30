#!/bin/bash

# Script de démarrage rapide et sécurisé du bot

echo "🤖 DÉMARRAGE DU BOT DE COVOITURAGE SUISSE"
echo "=========================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "bot.py" ]; then
    echo "❌ Erreur: bot.py non trouvé. Exécutez ce script depuis le répertoire du bot."
    exit 1
fi

# Activer l'environnement virtuel si disponible
if [ -d "venv" ]; then
    echo "🔄 Activation de l'environnement virtuel..."
    source venv/bin/activate
    echo "✅ Environnement virtuel activé"
fi

# Démarrage sécurisé avec correction automatique
echo "🚀 Démarrage du bot..."
python3 start_safe_bot.py

echo "👋 Bot arrêté"
