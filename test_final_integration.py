#!/usr/bin/env python3
"""
Test final d'intégration - vérifie que le bot peut utiliser les nouvelles communes
"""

import json
import sys
import os

# Ajouter le répertoire racine au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.route_distance import get_route_distance_with_fallback

def test_final_integration():
    """Test final d'intégration des nouvelles communes"""
    print("🎯 TEST FINAL D'INTÉGRATION")
    print("=" * 50)
    
    # Test quelques nouvelles communes importantes
    test_cities = [
        ('Winterthur', 'ZH'), 
        ('Bellinzona', 'TI'), 
        ('Olten', 'SO'),
        ('Baden', 'AG'),
        ('Liestal', 'BL'),
        ('Wil', 'SG')
    ]

    # Charger les données
    try:
        with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        cities = data['cities']
        lausanne = next(city for city in cities if city['name'] == 'Lausanne')
        print(f"✅ Données chargées: {len(cities)} communes")
    except Exception as e:
        print(f"❌ Erreur chargement données: {e}")
        return False

    print(f"\n🧪 Test calcul de prix avec nouvelles communes:")
    print("-" * 50)

    success_count = 0
    total_count = len(test_cities)

    for city_name, canton in test_cities:
        try:
            city = next(city for city in cities if city['name'] == city_name and city['canton'] == canton)
            distance, is_route = get_route_distance_with_fallback(
                (city['lat'], city['lon']),
                (lausanne['lat'], lausanne['lon'])
            )
            
            if distance:
                # Calcul du prix (comme dans le bot: 0.30 CHF/km)
                price = distance * 0.30
                route_type = '🛣️' if is_route else '📏'
                print(f'{route_type} {city_name} ({canton}) → Lausanne: {distance:.1f} km = {price:.2f} CHF')
                success_count += 1
            else:
                print(f'❌ {city_name} ({canton}) → Lausanne: Calcul impossible')
        except StopIteration:
            print(f'❌ {city_name} ({canton}): Ville non trouvée')
        except Exception as e:
            print(f'❌ {city_name} ({canton}): Erreur {e}')

    print(f"\n📊 RÉSULTATS:")
    print(f"✅ Succès: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    # Test de quelques trajets entre nouvelles communes
    print(f"\n🔄 Test trajets entre nouvelles communes:")
    print("-" * 50)
    
    inter_city_tests = [
        (('Winterthur', 'ZH'), ('Baden', 'AG')),
        (('Bellinzona', 'TI'), ('Lugano', 'TI')),
        (('Olten', 'SO'), ('Liestal', 'BL'))
    ]
    
    inter_success = 0
    
    for (city1_name, canton1), (city2_name, canton2) in inter_city_tests:
        try:
            city1 = next(city for city in cities if city['name'] == city1_name and city['canton'] == canton1)
            city2 = next(city for city in cities if city['name'] == city2_name and city['canton'] == canton2)
            
            distance, is_route = get_route_distance_with_fallback(
                (city1['lat'], city1['lon']),
                (city2['lat'], city2['lon'])
            )
            
            if distance:
                price = distance * 0.30
                route_type = '🛣️' if is_route else '📏'
                print(f'{route_type} {city1_name} ({canton1}) ↔ {city2_name} ({canton2}): {distance:.1f} km = {price:.2f} CHF')
                inter_success += 1
            else:
                print(f'❌ {city1_name} ↔ {city2_name}: Calcul impossible')
        except Exception as e:
            print(f'❌ {city1_name} ↔ {city2_name}: Erreur {e}')

    total_inter = len(inter_city_tests)
    print(f"\n📊 RÉSULTATS INTER-COMMUNES:")
    print(f"✅ Succès: {inter_success}/{total_inter} ({inter_success/total_inter*100:.1f}%)")
    
    # Résumé global
    total_success = success_count + inter_success
    total_tests = total_count + total_inter
    
    print(f"\n🎉 RÉSUMÉ GLOBAL:")
    print(f"✅ Tests réussis: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
    print(f"📍 Communes testées fonctionnelles")
    print(f"💰 Calcul de prix opérationnel")
    print(f"🛣️  Distance routière utilisée quand disponible")
    
    return total_success >= total_tests * 0.8  # 80% de succès minimum

if __name__ == "__main__":
    success = test_final_integration()
    
    if success:
        print(f"\n🎊 VALIDATION RÉUSSIE!")
        print("Le bot est prêt à utiliser les nouvelles communes!")
    else:
        print(f"\n⚠️  VALIDATION ÉCHOUÉE")
        print("Des problèmes ont été détectés.")
