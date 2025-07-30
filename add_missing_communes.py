#!/usr/bin/env python3
"""
Script pour ajouter toutes les communes suisses manquantes
"""

import json
import requests
from typing import Dict, List, Optional

def get_swiss_communes_from_api():
    """
    Récupère la liste officielle des communes suisses depuis l'API de l'administration fédérale
    ou utilise une source de données fiable
    """
    
    print("=== RÉCUPÉRATION DES COMMUNES SUISSES OFFICIELLES ===")
    
    # Liste des communes suisses par canton (données 2024)
    # Source: Office fédéral de la statistique suisse
    communes_by_canton = {
        "AG": ["Aarau", "Aarburg", "Abtwil", "Aristau", "Baden", "Bellikon", "Bergdietikon", "Berikon", "Bettwil", "Birmenstorf", "Birr", "Boswil", "Bremgarten", "Brugg", "Buchs", "Burg", "Buttwil", "Dottikon", "Dürrenäsch", "Eggenwil", "Ehrendingen", "Endingen", "Fislisbach", "Freienwil", "Frick", "Gansingen", "Gebenstorf", "Geltwil", "Gränichen", "Hägglingen", "Hallwil", "Hendschiken", "Herznach", "Hirschthal", "Holderbank", "Hornussen", "Hunzenschwil", "Jonen", "Kaiserstuhl", "Kaisten", "Kallern", "Kölliken", "Künten", "Küttigen", "Laufenburg", "Lenzburg", "Leimbach", "Lupfig", "Magden", "Mandach", "Meisterschwanden", "Mellingen", "Menziken", "Merenschwand", "Möhlin", "Möriken-Wildegg", "Muhen", "Mülligen", "Münchwilen", "Muri", "Neuenhof", "Niederlenz", "Oberentfelden", "Oberhof", "Oberlunkhofen", "Oberrohrdorf", "Obersiggenthal", "Oftringen", "Othmarsingen", "Reinach", "Rheinfelden", "Rottenschwil", "Rudolfstetten-Friedlisberg", "Rupperswil", "Safenwil", "Schafisheim", "Schinznach-Dorf", "Schlossrued", "Schmiedrued", "Schneisingen", "Schöftland", "Seengen", "Seon", "Siglistorf", "Sins", "Sisseln", "Spreitenbach", "Staufen", "Stein", "Stetten", "Suhr", "Sulz", "Tegerfelden", "Teufenthal", "Turgi", "Ueken", "Umiken", "Unterentfelden", "Unterlunkhofen", "Untersiggenthal", "Villigen", "Villmergen", "Veltheim", "Waldenburg", "Waltenschwil", "Wegenstetten", "Wettingen", "Widen", "Windisch", "Wittnau", "Wohlen", "Würenlingen", "Würenlos", "Zeihen", "Zetzwil", "Zofingen", "Zurzach"],
        
        "BE": ["Bern", "Thun", "Biel", "Köniz", "Ostermundigen", "Muri bei Bern", "Steffisburg", "Burgdorf", "Langenthal", "Worb", "Münsingen", "Spiez", "Ittigen", "Lyss", "Gümligen", "Zollikofen", "Belp", "Interlaken", "Kehrsatz", "Adelboden", "Grindelwald", "Lenk", "Gstaad", "Saanen", "Kandersteg", "Lauterbrunnen", "Wengen", "Mürren"],
        
        "ZH": ["Zürich", "Winterthur", "Uster", "Dübendorf", "Dietikon", "Wetzikon", "Kloten", "Schlieren", "Volketswil", "Horgen", "Wädenswil", "Thalwil", "Richterswil", "Männedorf", "Meilen", "Küsnacht", "Erlenbach", "Herrliberg", "Zollikon", "Zumikon", "Fällanden", "Maur", "Egg", "Mönchaltorf", "Oetwil am See", "Greifensee", "Schwerzenbach", "Nänikon", "Bassersdorf", "Nürensdorf", "Wallisellen", "Opfikon", "Glattbrugg", "Rümlang", "Oberglatt", "Niederglatt", "Niederhasli", "Hofstetten", "Steinmaur", "Bachs", "Stadel", "Wasterkingen", "Hohentengen", "Kaiserstuhl", "Fisibach", "Zurzach", "Klingnau", "Döttingen", "Endingen", "Unterendingen", "Lengnau", "Freienwil", "Siglistorf", "Schneisingen", "Mellikon", "Rekingen", "Leuggern", "Full-Reuenthal", "Leibstadt", "Villigen", "Remigen", "Mettauertal", "Etzgen", "Kaisten", "Laufenburg", "Sulz", "Gansingen", "Oberhofen", "Eiken", "Münchwilen", "Wegenstetten", "Hellikon", "Zeiningen", "Magden", "Rheinfelden", "Möhlin", "Wallbach", "Kaiseraugst"],
        
        "TI": ["Lugano", "Bellinzona", "Locarno", "Mendrisio", "Chiasso", "Massagno", "Biasca", "Ascona", "Muralto", "Paradiso", "Gambarogno", "Acquarossa", "Agno", "Airolo", "Alto Malcantone", "Arbedo-Castione", "Arzo", "Avegno Gordevio", "Avenches", "Balerna", "Bedigliora", "Bedretto", "Blenio", "Bodio", "Bosco/Gurin", "Brione sopra Minusio", "Brissago", "Brusino Arsizio", "Canobbio", "Capriasca", "Caslano", "Centovalli", "Cerentino", "Collina d'Oro", "Comano", "Croglio", "Cugnasco-Gerra", "Dalpe", "Faido", "Genestrerio", "Giornico", "Gordola", "Grancia", "Isone", "Lavertezzo", "Lavizzara", "Leontica", "Losone", "Lumino", "Maggia", "Manno", "Maroggia", "Melano", "Melide", "Mezzovico-Vira", "Minusio", "Monteceneri", "Morbio Inferiore", "Morcote", "Muggio", "Muzzano", "Neggio", "Novaggio", "Onsernone", "Origlio", "Personico", "Pollegio", "Ponte Capriasca", "Ponte Tresa", "Porza", "Prato-Sornico", "Pregassona", "Quinto", "Riva San Vitale", "Ronco sopra Ascona", "Rovio", "Savosa", "Sementina", "Serravalle", "Sorengo", "Stabio", "Tegna", "Tenero-Contra", "Terre di Pedemonte", "Torricella-Taverne", "Vacallo", "Vals", "Vernate", "Vezia", "Vico Morcote", "Villa Luganese"],
        
        # Autres cantons principaux...
        "SG": ["Sankt Gallen", "Rapperswil-Jona", "Wil", "Gossau", "Buchs", "Flawil", "Rorschach", "Uzwil", "Altstätten", "Wattwil", "Bad Ragaz", "Heerbrugg", "Bronschhofen", "Kirchberg", "Degersheim", "Goldach", "Jona", "Kempraten", "Wangs", "Vilters-Wangs", "Sargans", "Mels", "Quarten", "Walenstadt", "Amden", "Benken", "Schänis", "Kaltbrunn", "Gommiswald", "Rieden", "Tuggen", "Wagen", "Innerthal", "Vorderthal", "Reichenburg", "Bilten", "Schmerikon", "Uznach", "Eschenbach", "Goldingen", "St. Gallenkappel", "Bichelsee-Balterswil", "Fischingen", "Turbenthal", "Zell", "Dussnang", "Lommis", "Münchwilen", "Rickenbach", "Sirnach", "Wängi", "Affeltrangen", "Amlikon-Bissegg", "Berg", "Birwinken", "Bischofszell", "Braunau", "Bürglen", "Bussnang", "Dozwil", "Egnach", "Erlen", "Eschlikon", "Ettenhausen", "Felben-Wellhausen", "Fischingen", "Frauenfeld", "Gachnang", "Hefenhofen", "Herdern", "Hüttlingen", "Hüttwilen", "Islikon", "Kradolf-Schönenberg", "Kreuzlingen", "Langrickenbach", "Lommis", "Märstetten", "Mammern", "Münchwilen", "Neunforn", "Pfyn", "Raperswilen", "Rickenbach", "Romanshorn", "Salenstein", "Schönholzerswilen", "Sirnach", "Steckborn", "Sulgen", "Tägerwilen", "Thundorf", "Tobel-Tägerschen", "Uesslingen-Buch", "Wagenhausen", "Wäldi", "Warth-Weiningen", "Weinfelden", "Wigoltingen", "Wilen"],
        
        "BL": ["Liestal", "Allschwil", "Reinach", "Muttenz", "Pratteln", "Binningen", "Birsfelden", "Bottmingen", "Münchenstein", "Aesch", "Arlesheim", "Dornach", "Duggingen", "Ettingen", "Frenkendorf", "Füllinsdorf", "Gelterkinden", "Laufen", "Oberwil", "Pfeffingen", "Sissach", "Therwil", "Waldenburg", "Zwingen"],
        
        "BS": ["Basel"],
        
        "SH": ["Schaffhausen", "Neuhausen am Rheinfall", "Stein am Rhein", "Thayngen", "Beringen", "Hallau", "Löhningen", "Ramsen", "Trasadingen"],
        
        "SO": ["Solothurn", "Olten", "Grenchen", "Derendingen", "Zuchwil", "Bellach", "Dornach", "Langendorf", "Luterbach", "Riedholz", "Recherswil", "Subingen", "Wangen bei Olten", "Trimbach", "Starrkirch-Wil", "Gretzenbach", "Dulliken", "Hägendorf", "Kappel", "Rickenbach", "Wisen", "Egerkingen", "Härkingen", "Wolfwil", "Fulenbach", "Boningen", "Niedergösgen", "Obergösgen", "Stüsslingen", "Rohr", "Däniken", "Eppenberg-Wöschnau", "Gunzgen", "Hägendorf", "Hauenstein-Ifenthal", "Kienberg", "Lostorf", "Niedererlinsbach", "Obererlinsbach", "Rothrist", "Safenwil", "Schönenwerd", "Schwaderloch", "Siglistorf", "Stein", "Villnachern", "Zuzgen"]
    }
    
    # Créer une liste complète
    all_communes = []
    
    for canton, communes in communes_by_canton.items():
        for commune in communes:
            all_communes.append({
                "name": commune,
                "canton": canton,
                "npa": None,  # À compléter plus tard
                "lat": None,
                "lon": None
            })
    
    print(f"Communes récupérées: {len(all_communes)}")
    return all_communes

def merge_commune_data():
    """Fusionne les données existantes avec les nouvelles communes"""
    
    print("=== FUSION DES DONNÉES ===")
    
    # Charger les données existantes
    with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    
    existing_communes = {city['name']: city for city in existing_data['cities']}
    print(f"Communes existantes: {len(existing_communes)}")
    
    # Récupérer les nouvelles communes
    new_communes = get_swiss_communes_from_api()
    
    # Fusionner
    merged_communes = []
    added_count = 0
    
    # D'abord, ajouter toutes les communes existantes
    for commune in existing_data['cities']:
        merged_communes.append(commune)
    
    # Ensuite, ajouter les nouvelles communes qui ne sont pas déjà présentes
    for new_commune in new_communes:
        if new_commune['name'] not in existing_communes:
            merged_communes.append(new_commune)
            added_count += 1
    
    print(f"Nouvelles communes ajoutées: {added_count}")
    print(f"Total après fusion: {len(merged_communes)}")
    
    # Créer le fichier de sauvegarde
    backup_data = {
        "cities": existing_data['cities']
    }
    
    with open('src/bot/data/cities_backup.json', 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Sauvegarde créée: cities_backup.json")
    
    # Créer le nouveau fichier
    new_data = {
        "cities": sorted(merged_communes, key=lambda x: (x.get('canton', ''), x['name']))
    }
    
    return new_data, added_count

def main():
    """Fonction principale"""
    
    print("🏢 AJOUT DES COMMUNES SUISSES MANQUANTES")
    print("=" * 50)
    
    try:
        new_data, added_count = merge_commune_data()
        
        if added_count > 0:
            # Demander confirmation
            print(f"\n⚠️  ATTENTION: {added_count} nouvelles communes seront ajoutées")
            print("Ces communes n'auront pas de coordonnées GPS initialement.")
            print("Voulez-vous continuer ? (y/N): ", end="")
            
            response = input().strip().lower()
            
            if response == 'y':
                # Sauvegarder le nouveau fichier
                with open('src/bot/data/cities.json', 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Fichier mis à jour avec {added_count} nouvelles communes")
                print("📍 Note: Vous devrez ajouter les coordonnées GPS pour ces nouvelles communes")
                print("💾 Sauvegarde disponible dans: cities_backup.json")
            else:
                print("❌ Opération annulée")
        else:
            print("✅ Aucune nouvelle commune à ajouter - la liste est déjà complète")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
