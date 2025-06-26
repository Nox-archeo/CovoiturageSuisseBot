#!/bin/bash
# Script de vérification des boutons du profil
# Ce script analyse les logs pour détecter si les boutons du profil fonctionnent correctement

LOG_FILE="logs/bot_run_latest.log"

# Démarrer le bot en mode debug
echo "Démarrage du bot avec journalisation des boutons..."
./start_bot.sh debug &
BOT_PID=$!

echo "Le bot est maintenant en cours d'exécution avec PID: $BOT_PID"
echo "Appuyez sur Ctrl+C pour terminer le bot après avoir testé les boutons du profil."
echo ""
echo "Instructions pour tester:"
echo "1. Allez dans votre profil Telegram"
echo "2. Cliquez sur les boutons (Mes Trajets, Mes Réservations, etc.)"
echo "3. Vérifiez que le contenu change à chaque clic"
echo ""
echo "Ce script analysera les logs en temps réel pour afficher les actions détectées."
echo "Appuyez sur Ctrl+C quand vous avez terminé les tests."

# Fonction pour analyser les logs en temps réel
analyze_logs() {
    echo "Analyse des logs pour détecter les actions des boutons du profil..."
    tail -f "$LOG_FILE" | grep --color=always -E "Action de profil sélectionnée|Message édité|Erreur|Le contenu|Mise à jour" &
}

# Fonction pour nettoyer en sortant
cleanup() {
    echo ""
    echo "Arrêt du bot et nettoyage..."
    kill $BOT_PID 2>/dev/null
    kill $TAIL_PID 2>/dev/null
    
    # Analyse rapide des logs
    echo ""
    echo "RÉSUMÉ DES ACTIONS DE PROFIL:"
    grep "Action de profil sélectionnée" "$LOG_FILE" | tail -n 10
    
    echo ""
    echo "RÉSUMÉ DES MESSAGES ÉDITÉS:"
    grep "Mise à jour du message" "$LOG_FILE" | tail -n 10
    
    echo ""
    echo "RÉSUMÉ DES ERREURS:"
    grep -i "erreur" "$LOG_FILE" | grep -i "profil" | tail -n 10
    
    echo ""
    echo "Test terminé."
    exit 0
}

# Configurer le gestionnaire de signal pour Ctrl+C
trap cleanup SIGINT

# Démarrer l'analyse des logs
analyze_logs
TAIL_PID=$!

# Attendre que l'utilisateur appuie sur Ctrl+C
wait $BOT_PID
