#!/bin/bash

echo "🚀 Redémarrage forcé du bot avec cache cleared"
echo "=============================================="

# Kill tous les processus Python
pkill -f bot.py
pkill -f start_render.py
sleep 2

# Clear le cache Python
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Export des variables d'environnement si nécessaire
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

echo "🧹 Cache Python nettoyé"

# Diagnostic des méthodes PayPal
echo "🔍 Diagnostic PayPal..."
python debug_paypal_methods.py

echo "🎯 Redémarrage du bot..."
# Démarrer le bot
python start_render.py

echo "✅ Bot redémarré avec diagnostic complet"
