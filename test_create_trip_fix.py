#!/usr/bin/env python3
"""
Test complet de la fonctionnalité de création de trajet
"""

def test_create_trip_flow():
    """Teste le flux complet de création de trajet"""
    print("🚗 TEST DU FLUX DE CRÉATION DE TRAJET")
    print("=" * 45)
    
    try:
        # Importer les modules nécessaires
        from handlers.create_trip_handler import compute_price_auto
        from utils.swiss_cities import find_locality
        
        print("✅ Imports réussis")
        
        # Simuler les données comme dans le bot
        print("\n🔍 Simulation du flux complet:")
        
        # 1. Recherche des villes
        dep_results = find_locality("Lausanne")
        arr_results = find_locality("Fribourg")
        
        if dep_results and arr_results:
            departure = dep_results[0]  # Dictionnaire
            arrival = arr_results[0]    # Dictionnaire
            
            print(f"✅ Départ trouvé: {departure['name']} ({departure['zip']})")
            print(f"✅ Arrivée trouvée: {arrival['name']} ({arrival['zip']})")
            
            # 2. Extraction des noms (comme dans le code corrigé)
            dep_name = departure.get('name', '') if isinstance(departure, dict) else str(departure)
            arr_name = arrival.get('name', '') if isinstance(arrival, dict) else str(arrival)
            
            # 3. Calcul du prix
            prix, dist = compute_price_auto(dep_name, arr_name)
            
            if prix is not None and dist is not None:
                print(f"✅ Prix calculé: {prix} CHF")
                print(f"✅ Distance: {dist} km")
                
                # 4. Simulation du message récapitulatif
                print(f"\n📋 Récapitulatif:")
                print(f"   De: {dep_name}")
                print(f"   À: {arr_name}")
                print(f"   Distance: {dist} km")
                print(f"   Prix total: {prix} CHF")
                
                # Avec différents nombres de places
                for places in [1, 2, 3, 4]:
                    prix_par_place = prix / places
                    print(f"   Prix pour {places} place(s): {prix_par_place:.2f} CHF/place")
                
                print("\n🎉 FLUX COMPLET TESTÉ AVEC SUCCÈS!")
                return True
            else:
                print("❌ Échec calcul prix/distance")
                return False
        else:
            print("❌ Villes non trouvées")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_create_trip_flow()
    if success:
        print("\n✅ Le bot peut maintenant traiter les créations de trajet sans erreur!")
    else:
        print("\n❌ Des problèmes persistent")
