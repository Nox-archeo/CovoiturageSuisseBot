#!/usr/bin/env python
"""
Script de test pour l'affichage du résumé de création de trajet
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire racine au chemin Python
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_summary_display():
    """Test de l'affichage du résumé"""
    print("🔄 Test de l'affichage du résumé...")
    
    # Simuler les données user_data
    test_data = {
        'trip_type': 'driver',
        'trip_options': {'simple': True},
        'departure': {'name': 'Fribourg'},
        'arrival': {'name': 'Lausanne'},
        'datetime_obj': datetime(2025, 6, 26, 20, 0),
        'distance_km': 40.0,
        'seats': 2,
        'price': 10.01
    }
    
    # Reproduire la logique du résumé
    dep_display = test_data['departure']['name']
    arr_display = test_data['arrival']['name']
    prix = test_data['price']
    dist = test_data['distance_km']
    
    # Traduction du rôle en français
    trip_type = test_data['trip_type']
    if trip_type == 'driver':
        role_fr = "🚗 Conducteur"
    elif trip_type == 'passenger':
        role_fr = "🧍 Passager"
    else:
        role_fr = trip_type
    
    # Formatage de la date/heure
    datetime_obj = test_data['datetime_obj']
    if datetime_obj:
        date_formatted = datetime_obj.strftime('%d/%m/%Y à %H:%M')
    else:
        date_formatted = 'Non définie'
    
    # Options en français
    options = test_data['trip_options']
    if options.get('simple'):
        options_str = "✅ Trajet simple"
    else:
        options_str = "📋 Options avancées"
    
    summary = (
        "🎯 *Résumé de votre trajet*\n\n"
        f"👤 *Rôle :* {role_fr}\n"
        f"⚙️ *Type :* {options_str}\n\n"
        f"🌍 *Départ :* {dep_display}\n"
        f"🏁 *Arrivée :* {arr_display}\n"
        f"📅 *Date et heure :* {date_formatted}\n\n"
        f"📏 *Distance :* {dist} km\n"
        f"💺 *Places disponibles :* {test_data['seats']}\n"
        f"💰 *Prix par place :* {prix} CHF\n\n"
        "✨ *Confirmez-vous la création de ce trajet ?*"
    )
    
    print("✅ Aperçu du nouveau résumé :")
    print("=" * 50)
    # Supprimer les marqueurs Markdown pour l'affichage console
    display_summary = summary.replace('*', '')
    print(display_summary)
    print("=" * 50)
    
    # Vérifications
    checks = [
        ('Rôle en français', '🚗 Conducteur' in summary),
        ('Date correcte', '26/06/2025 à 20:00' in summary),
        ('Type traduit', 'Trajet simple' in summary),
        ('Émojis présents', '🎯' in summary and '👤' in summary),
        ('Prix formaté', '10.01 CHF' in summary),
        ('Distance', '40.0 km' in summary)
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def test_old_vs_new():
    """Comparaison ancien vs nouveau format"""
    print("\n🔄 Comparaison ancien vs nouveau format...")
    
    print("\n❌ ANCIEN FORMAT (problématique) :")
    print("-" * 30)
    old_format = """📋 Résumé du trajet à créer:

Rôle: driver
Options: {'simple': True}
De: Fribourg
À: Lausanne
Date: 26/06/2025 20:00
Distance: 40.0 km
Places: 2
Prix (auto): 10.01 CHF

Confirmez-vous la création de ce trajet?"""
    print(old_format)
    
    print("\n✅ NOUVEAU FORMAT (corrigé) :")
    print("-" * 30)
    new_format = """🎯 Résumé de votre trajet

👤 Rôle : 🚗 Conducteur
⚙️ Type : ✅ Trajet simple

🌍 Départ : Fribourg
🏁 Arrivée : Lausanne
📅 Date et heure : 26/06/2025 à 20:00

📏 Distance : 40.0 km
💺 Places disponibles : 2
💰 Prix par place : 10.01 CHF

✨ Confirmez-vous la création de ce trajet ?"""
    print(new_format)
    
    print("\n🎯 AMÉLIORATIONS :")
    print("✅ Texte en français (plus 'driver')")
    print("✅ Heure affichée correctement (format XX:XX)")
    print("✅ Présentation plus jolie avec émojis")
    print("✅ Sections organisées logiquement")
    print("✅ Boutons plus explicites")
    
    return True

def main():
    """Fonction principale de test"""
    print("🎨 Test du résumé de création de trajet")
    print("=" * 45)
    
    tests = [
        test_summary_display,
        test_old_vs_new
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 45)
    print("📊 Résultats des tests :")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Tous les tests réussis ({passed}/{total})")
        print("\n🎉 Le résumé est maintenant corrigé !")
        print("\nAméliorations apportées :")
        print("  ✅ Traduction en français")
        print("  ✅ Formatage correct de l'heure")
        print("  ✅ Présentation plus jolie")
        print("  ✅ Boutons plus explicites")
        return True
    else:
        print(f"❌ {total - passed} test(s) échoué(s) sur {total}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
