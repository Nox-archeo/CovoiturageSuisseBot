#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les caractères non-ASCII dans les variables d'environnement
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

def analyze_env_variable(var_name):
    """Analyse une variable d'environnement pour détecter les caractères problématiques"""
    value = os.getenv(var_name)
    if not value:
        print(f"❌ Variable {var_name} non définie")
        return
    
    print(f"\n🔍 Analyse de {var_name}:")
    print(f"  Longueur: {len(value)} caractères")
    
    # Détecter les caractères non-ASCII
    non_ascii_chars = []
    for i, char in enumerate(value):
        if ord(char) < 32 or ord(char) > 126:
            non_ascii_chars.append((i, char, ord(char)))
    
    if non_ascii_chars:
        print(f"  ❌ {len(non_ascii_chars)} caractères non-ASCII détectés:")
        for pos, char, code in non_ascii_chars[:10]:  # Limiter à 10 pour éviter le spam
            char_repr = repr(char)
            print(f"    Position {pos}: {char_repr} (code {code})")
    else:
        print(f"  ✅ Tous les caractères sont ASCII valides")
    
    # Vérifier les espaces en début/fin
    stripped = value.strip()
    if len(stripped) != len(value):
        print(f"  ⚠️ Espaces détectés: {len(value) - len(stripped)} caractères d'espacement")
    
    # Afficher les premiers et derniers caractères
    if len(value) > 0:
        first_chars = value[:10] if len(value) > 10 else value
        last_chars = value[-10:] if len(value) > 10 else value
        print(f"  Début: {repr(first_chars)}")
        if len(value) > 10:
            print(f"  Fin: {repr(last_chars)}")

def main():
    """Fonction principale de diagnostic"""
    print("🔍 DIAGNOSTIC DES VARIABLES D'ENVIRONNEMENT")
    print("=" * 60)
    
    # Variables à analyser
    variables = [
        'TELEGRAM_BOT_TOKEN',
        'PAYPAL_CLIENT_ID',
        'PAYPAL_CLIENT_SECRET',
        'BOT_URL',
        'WEBHOOK_URL'
    ]
    
    for var in variables:
        analyze_env_variable(var)
    
    print(f"\n📊 RÉSUMÉ:")
    print("Ce script aide à identifier les caractères non-ASCII qui causent l'erreur InvalidURL")
    print("Recherchez les caractères avec des codes < 32 ou > 126")

if __name__ == '__main__':
    main()
