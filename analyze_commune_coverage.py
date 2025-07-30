#!/usr/bin/env python3
"""
Vérification si toutes les communes suisses sont présentes
"""

import json

def analyze_commune_coverage():
    """Analyse la couverture des communes suisses"""
    
    print("=== ANALYSE DE LA COUVERTURE DES COMMUNES ===")
    
    # Charger les communes du bot
    with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
        cities_data = json.load(f)
    
    # Analyser par canton
    by_canton = {}
    total_communes = len(cities_data['cities'])
    
    for city in cities_data['cities']:
        canton = city.get('canton', 'XX')
        if canton not in by_canton:
            by_canton[canton] = []
        by_canton[canton].append(city['name'])
    
    print(f"Total des communes dans le bot: {total_communes}")
    print(f"Cantons représentés: {len(by_canton)}")
    
    # Détail par canton
    print(f"\n=== RÉPARTITION PAR CANTON ===")
    for canton, communes in sorted(by_canton.items()):
        print(f"{canton}: {len(communes)} communes")
        # Quelques exemples
        examples = sorted(communes)[:5]
        print(f"   Exemples: {', '.join(examples)}")
        if len(communes) > 5:
            print(f"   ... et {len(communes) - 5} autres")
        print()
    
    # Vérification des principales villes suisses connues
    print(f"=== VÉRIFICATION DES PRINCIPALES VILLES SUISSES ===")
    
    principales_villes = [
        "Zürich", "Genève", "Bâle", "Lausanne", "Berne", "Winterthur",
        "Lucerne", "Saint-Gall", "Lugano", "Bienne", "Thoune", "Köniz",
        "La Chaux-de-Fonds", "Fribourg", "Schaffhouse", "Coire", "Neuchâtel",
        "Uster", "Sion", "Emmen", "Yverdon-les-Bains", "Zoug", "Kriens",
        "Rapperswil-Jona", "Dübendorf", "Montreux", "Dietikon", "Frauenfeld",
        "Wetzikon", "Aarau", "Bellinzone", "Bulle", "Olten"
    ]
    
    # Noms alternatifs pour certaines villes
    name_variants = {
        "Zürich": ["Zurich"],
        "Bâle": ["Basel", "Bale"],
        "Berne": ["Bern"],
        "Lucerne": ["Luzern"],
        "Saint-Gall": ["Sankt Gallen", "St. Gallen"],
        "Coire": ["Chur"],
        "Zoug": ["Zug"],
        "Thoune": ["Thun"],
        "Bienne": ["Biel"],
        "La Chaux-de-Fonds": ["Chaux-de-Fonds"]
    }
    
    communes_bot = set(city['name'] for city in cities_data['cities'])
    
    found = []
    missing = []
    
    for ville in principales_villes:
        # Vérifier le nom principal
        if ville in communes_bot:
            found.append(ville)
            continue
        
        # Vérifier les variantes
        found_variant = False
        if ville in name_variants:
            for variant in name_variants[ville]:
                if variant in communes_bot:
                    found.append(f"{ville} (trouvé comme {variant})")
                    found_variant = True
                    break
        
        if not found_variant:
            missing.append(ville)
    
    print(f"✅ Principales villes trouvées ({len(found)}):")
    for ville in found:
        print(f"   {ville}")
    
    if missing:
        print(f"\n❌ Principales villes manquantes ({len(missing)}):")
        for ville in missing:
            print(f"   {ville}")
    else:
        print(f"\n🎉 TOUTES les principales villes suisses sont présentes!")
    
    # Estimation de la couverture
    print(f"\n=== ESTIMATION DE LA COUVERTURE ===")
    
    # La Suisse compte environ 2'200 communes officielles (chiffre 2023)
    # Mais beaucoup ont fusionné ces dernières années
    estimated_total_swiss_communes = 2200
    
    coverage_pct = (total_communes / estimated_total_swiss_communes) * 100
    
    print(f"Communes dans le bot: {total_communes}")
    print(f"Estimation du total suisse: ~{estimated_total_swiss_communes}")
    print(f"Couverture estimée: {coverage_pct:.1f}%")
    
    if coverage_pct < 50:
        print("⚠️ Couverture faible - beaucoup de communes manquantes")
    elif coverage_pct < 80:
        print("✅ Bonne couverture - quelques communes mineures manquantes")
    else:
        print("🎉 Excellente couverture - pratiquement toutes les communes")

if __name__ == "__main__":
    analyze_commune_coverage()
