#!/bin/bash

# Script de démarrage sécurisé pour le bot Telegram
# Ce script s'assure qu'une seule instance du bot est en cours d'exécution

# Dossier de travail
cd "$(dirname "$0")"

# Fichier pour stocker le PID du bot
PID_FILE=".bot_pid"

# Fonction pour nettoyer et sortir
cleanup() {
  echo "Arrêt du bot..."
  if [ -f "$PID_FILE" ]; then
    rm "$PID_FILE"
  fi
  exit 0
}

# Capture des signaux pour un arrêt propre
trap cleanup SIGINT SIGTERM

# Vérifier si une instance du bot est déjà en cours d'exécution
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if ps -p $OLD_PID > /dev/null 2>&1; then
    echo "⚠️ Une instance du bot est déjà en cours d'exécution (PID: $OLD_PID)"
    echo "Voulez-vous arrêter cette instance et démarrer une nouvelle? (o/n)"
    read -r response
    if [[ "$response" =~ ^[oO]$ ]]; then
      echo "Arrêt de l'instance précédente..."
      python kill_all_bots.py
    else
      echo "Opération annulée."
      exit 1
    fi
  else
    echo "🔄 Suppression du fichier PID orphelin (le processus n'existe plus)."
  fi
fi

# Tuer toutes les instances potentiellement en cours
python kill_all_bots.py

# Démarrer le bot et enregistrer son PID
echo "🚀 Démarrage du bot CovoiturageSuisse..."
python bot.py &
BOT_PID=$!
echo $BOT_PID > "$PID_FILE"
echo "✅ Bot démarré avec succès! (PID: $BOT_PID)"
echo "📝 Logs disponibles dans le terminal."
echo "❌ Pour arrêter le bot, appuyez sur Ctrl+C"

# Attendre que le processus se termine
wait $BOT_PID

# Nettoyer à la fin
cleanup
