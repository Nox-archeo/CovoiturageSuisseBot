#!/bin/bash
echo "🚀 Lancement du bot avec debug..."
cd /Users/margaux/CovoiturageSuisse

# Activer l'environnement virtuel s'il existe
if [ -d "venv" ]; then
    echo "📦 Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Installer les dépendances si nécessaire
if ! python3 -c "import telegram" 2>/dev/null; then
    echo "📋 Installation des dépendances..."
    pip3 install -r requirements.txt
fi

# Lancer le bot
echo "🤖 Démarrage du bot..."
python3 bot.py
