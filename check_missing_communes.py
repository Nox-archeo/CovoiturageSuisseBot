#!/usr/bin/env python3
"""Test des communes manquantes signalées par l'utilisateur."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pickle

def check_missing_communes():
    """Vérifie les communes manquantes signalées"""
    
    # Charger les données du bot
    try:
        with open('/Users/margaux/CovoiturageSuisse/bot_data.pickle', 'rb') as f:
            data = pickle.load(f)
            localities = data.get('localities', [])
        
        print(f"📊 Total localités chargées: {len(localities)}")
        
        # Communes à vérifier (signalées comme manquantes)
        missing_communes = [
            "Corpataux",
            "Posieux", 
            "Rossens",
            "Farvagny",
            "Vuisternens-en-Ogoz",
            "1727 Corpataux",  # Code postal + nom
        ]
        
        print("\n🔍 RECHERCHE DES COMMUNES 'MANQUANTES'")
        print("=" * 45)
        
        for commune_search in missing_communes:
            print(f"\n🎯 Recherche: '{commune_search}'")
            
            # Recherche exacte
            exact_matches = [loc for loc in localities if commune_search.lower() in loc['name'].lower()]
            
            # Recherche partielle
            partial_matches = [loc for loc in localities 
                             if any(word.lower() in loc['name'].lower() 
                                  for word in commune_search.split()) 
                             and loc not in exact_matches]
            
            # Recherche par code postal (si applicable)
            postal_matches = []
            if commune_search.startswith("1727"):
                postal_matches = [loc for loc in localities if loc.get('npa') == 1727]
            
            total_matches = exact_matches + partial_matches + postal_matches
            
            if total_matches:
                print(f"   ✅ {len(total_matches)} résultat(s) trouvé(s):")
                for match in total_matches[:5]:  # Limite à 5 résultats
                    print(f"      • {match['name']} (NPA: {match.get('npa', 'N/A')}) - Canton: {match.get('canton', 'N/A')}")
                    if 'lat' in match and 'lon' in match:
                        print(f"        Coords: {match['lat']}, {match['lon']}")
                if len(total_matches) > 5:
                    print(f"      ... et {len(total_matches) - 5} autres")
            else:
                print(f"   ❌ Aucun résultat trouvé")
                
                # Recherche élargie (toutes les communes avec un mot similaire)
                broad_search = [loc for loc in localities 
                              if any(word.lower() in loc['name'].lower() 
                                   for word in commune_search.lower().split()
                                   if len(word) > 3)]  # Mots de plus de 3 lettres
                
                if broad_search:
                    print(f"   🔍 Recherche élargie ({len(broad_search)} résultats):")
                    for match in broad_search[:3]:
                        print(f"      • {match['name']} - {match.get('canton', 'N/A')}")
        
        # Recherche spéciale pour code postal 1727
        print(f"\n📮 RECHERCHE PAR CODE POSTAL 1727")
        print("=" * 35)
        
        npa_1727 = [loc for loc in localities if str(loc.get('npa', '')).startswith('1727')]
        if npa_1727:
            print(f"✅ {len(npa_1727)} communes avec NPA 1727:")
            for loc in npa_1727:
                print(f"   • {loc['name']} (NPA: {loc['npa']}) - {loc.get('canton', 'N/A')}")
                if 'lat' in loc and 'lon' in loc:
                    print(f"     Coords: {loc['lat']}, {loc['lon']}")
        else:
            print("❌ Aucune commune avec NPA 1727 trouvée")
        
        # Statistiques par canton
        print(f"\n📊 STATISTIQUES PAR CANTON")
        print("=" * 28)
        
        canton_stats = {}
        for loc in localities:
            canton = loc.get('canton', 'Inconnu')
            canton_stats[canton] = canton_stats.get(canton, 0) + 1
        
        for canton, count in sorted(canton_stats.items()):
            print(f"   {canton}: {count} communes")
        
        # Recherche spéciale région Fribourg
        print(f"\n🏔️ COMMUNES FRIBOURGEOISES")
        print("=" * 25)
        
        fribourg_communes = [loc for loc in localities 
                           if loc.get('canton', '').lower() in ['fribourg', 'fr', 'freiburg']]
        
        print(f"Total communes fribourgeoises: {len(fribourg_communes)}")
        
        # Recherche des communes problématiques en Fribourg
        fribourg_search_terms = ['corpataux', 'posieux', 'rossens', 'farvagny', 'vuisternens']
        
        for term in fribourg_search_terms:
            matches = [loc for loc in fribourg_communes 
                      if term.lower() in loc['name'].lower()]
            if matches:
                print(f"\n   🎯 '{term}' en Fribourg:")
                for match in matches:
                    print(f"      ✅ {match['name']} (NPA: {match.get('npa', 'N/A')})")
                    if 'lat' in match and 'lon' in match:
                        print(f"         GPS: {match['lat']}, {match['lon']}")
            else:
                print(f"   ❌ '{term}' non trouvé en Fribourg")
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement des données: {e}")

if __name__ == "__main__":
    check_missing_communes()
