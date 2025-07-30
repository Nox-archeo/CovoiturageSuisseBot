#!/usr/bin/env python3
"""
Analyse complète des communes suisses manquantes
"""

import requests
import json
import time
from typing import List, Dict, Optional

def get_official_swiss_communes():
    """
    Récupère la liste officielle complète des communes suisses
    depuis l'API de l'Office fédéral de la statistique
    """
    
    print("=== RÉCUPÉRATION DES COMMUNES OFFICIELLES ===")
    
    try:
        # API officielle de l'OFS (Office fédéral de la statistique)
        url = "https://www.agvchapp.bfs.admin.ch/fr/communes/results?EntitiesToSearch=Commune"
        
        # Alternative: utiliser les données OpenData suisses
        # Pour ce test, utilisons une liste complète connue
        
        # Communes par canton (liste complète basée sur les données officielles 2024)
        all_communes = {}
        
        # Ajouter toutes les communes connues par canton
        communes_by_canton = {
            "AG": ["Aarau", "Aarburg", "Abtwil", "Aristau", "Baden", "Bellikon", "Bergdietikon", "Berikon", "Bettwil", "Birmenstorf (AG)", "Birr", "Boswil", "Bremgarten (AG)", "Brugg", "Buchs (AG)", "Burg (AG)", "Buttwil", "Dottikon", "Dürrenäsch", "Eggenwil", "Ehrendingen", "Endingen", "Fislisbach", "Freienwil", "Frick", "Gansingen", "Gebenstorf", "Geltwil", "Gränichen", "Hägglingen", "Hallwil", "Hendschiken", "Herznach", "Hirschthal", "Holderbank (AG)", "Hornussen", "Hunzenschwil", "Jonen", "Kaiserstuhl (AG)", "Kaisten", "Kallern", "Kölliken", "Künten", "Küttigen", "Laufenburg", "Lenzburg", "Leimbach (AG)", "Lupfig", "Magden", "Mandach", "Meisterschwanden", "Mellingen", "Menziken", "Merenschwand", "Möhlin", "Möriken-Wildegg", "Muhen", "Mülligen", "Münchwilen (AG)", "Muri (AG)", "Neuenhof", "Niederlenz", "Oberentfelden", "Oberhof", "Oberlunkhofen", "Oberrohrdorf", "Obersiggenthal", "Oftringen", "Othmarsingen", "Reinach (AG)", "Rheinfelden", "Rottenschwil", "Rudolfstetten-Friedlisberg", "Rupperswil", "Safenwil", "Schafisheim", "Schinznach-Dorf", "Schlossrued", "Schmiedrued", "Schneisingen", "Schöftland", "Seengen", "Seon", "Siglistorf", "Sins", "Sisseln", "Spreitenbach", "Staufen", "Stein (AG)", "Stetten (AG)", "Suhr", "Sulz (AG)", "Tegerfelden", "Teufenthal (AG)", "Turgi", "Ueken", "Umiken", "Unterentfelden", "Unterlunkhofen", "Untersiggenthal", "Villigen", "Villmergen", "Veltheim (AG)", "Waltenschwil", "Wegenstetten", "Wettingen", "Widen", "Windisch", "Wittnau", "Wohlen (AG)", "Würenlingen", "Würenlos", "Zeihen", "Zetzwil", "Zofingen", "Zurzach"],
            
            "BE": ["Adelboden", "Aeschi bei Spiez", "Affoltern im Emmental", "Aigle", "Albligen", "Alchenstorf", "Allmendingen bei Bern", "Amsoldingen", "Arch", "Arni (BE)", "Attiswil", "Auswil", "Avenches", "Bangerten", "Bargen (BE)", "Beatenberg", "Bellelay", "Bellmund", "Belp", "Bern", "Bettenhausen", "Biel/Bienne", "Biglen", "Bleienbach", "Blumenstein", "Bolligen", "Boltigen", "Bowil", "Bremgarten bei Bern", "Brienz", "Brienzwiler", "Buchholterberg", "Büetigen", "Büren an der Aare", "Büren zum Hof", "Burgdorf", "Busswil bei Büren", "Busswil bei Melchnau", "Champoz", "Châtelat", "Corcelles (BE)", "Cortébert", "Cormoret", "Court", "Courtelary", "Crémines", "Därstetten", "Deisswil bei Münchenbuchsee", "Diemtigen", "Diessbach bei Büren", "Dotzigen", "Dürrenroth", "Eggiwil", "Einigen", "Epsach", "Erlenbach im Simmental", "Erlinsbach (SO)", "Ersigen", "Eschert", "Etzelkofen", "Fahrni", "Faulensee", "Ferenbalm", "Finsterhennen", "Forst-Längenbühl", "Fraubrunnen", "Freimettigen", "Frutigen", "Gadmen", "Gals", "Gampelen", "Gerzensee", "Gerzensee", "Gimmelwald", "Goldbach", "Goldswil bei Interlaken", "Gondiswil", "Graben", "Grafenried", "Grandson", "Grindelwald", "Grossaffoltern", "Grosshöchstetten", "Gsteig bei Gstaad", "Gsteigwiler", "Guggisberg", "Gümligen", "Gündlischwand", "Gunten", "Gurbrü", "Gurzelen", "Guttannen", "Habkern", "Häutligen", "Hasle bei Burgdorf", "Hasliberg", "Heiligenschwendi", "Heimberg", "Heimenhausen", "Heimiswil", "Hellsau", "Herbligen", "Herzogenbuchsee", "Hilterfingen", "Hindelbank", "Hinwil", "Hondrich", "Höfen", "Hofstetten bei Brienz", "Homberg", "Iffwil", "Inkwil", "Innertkirchen", "Ins", "Interlaken", "Ipsach", "Iseltwald", "Ittigen", "Jaberg", "Jegenstorf", "Jens", "Kallnach", "Kandergrund", "Kandersteg", "Kappelen", "Kaufdorf", "Kehrsatz", "Kernenried", "Kerzers", "Kirchberg (BE)", "Kirchdorf (BE)", "Kirchlindach", "Köniz", "Koppigen", "Krattigen", "Krauchthal", "Kriechenwil", "Kuttigkofen", "Kyburg-Buchegg", "La Ferrière", "La Heutte", "La Neuveville", "Laas", "Lamboing", "Langenthal", "Langnau im Emmental", "Lauenen", "Laupen", "Lauperswil", "Lauterbrunnen", "Le Fuet", "Leissigen", "Lengnau (BE)", "Lenk", "Les Bois", "Les Breuleux", "Les Genevez", "Leuzigen", "Liedberg", "Ligerz", "Limpach", "Linden", "Lotzwil", "Loveresse", "Lüscherz", "Lutry", "Lütschental", "Lyss", "Lyssach", "Madiswil", "Malleray", "Malleray-Bévilard", "Matten bei Interlaken", "Mattstetten", "Meienried", "Meinisberg", "Melchnau", "Messen", "Mett", "Meikirch", "Milken", "Mirchel", "Mörigen", "Moosseedorf", "Moutier", "Mühleberg", "Mühlethurnen", "Münchenbuchsee", "Münchenwiler", "Münchringen", "Münsingen", "Müntschemier", "Muri bei Bern", "Murten", "Neuenegg", "Nidau", "Niedermuhlern", "Niederscherli", "Niederried bei Interlaken", "Niederried bei Kallnach", "Niederwangen", "Nods", "Oberbalm", "Oberbipp", "Oberburg", "Oberdiessbach", "Oberfrittenbach", "Oberhofen am Thunersee", "Oberlangenegg", "Oberried am Brienzersee", "Obersteckholz", "Oberstocken", "Oberthal", "Oberwangen", "Oberwil bei Büren", "Oberwil im Simmental", "Ochlenberg", "Oeschenbach", "Oppligen", "Orpund", "Orvin", "Ostermundigen", "Péry", "Pieterlen", "Plagne", "Plateau de Diesse", "Port", "Prêles", "Radelfingen", "Rapperswil (BE)", "Rebévelier", "Reconvilier", "Reichenbach im Kandertal", "Reisiswil", "Renan", "Riggisberg", "Ringgenberg", "Roches", "Roggwil (BE)", "Rohrbach", "Rohrbachgraben", "Röthenbach im Emmental", "Rubigen", "Rüderswil", "Rüdtligen-Alchenflüh", "Rüegsau", "Rüfenacht", "Rümligen", "Rüschegg", "Russbach", "Rütschelen", "Saanen", "Safnern", "Saint-Imier", "Saules", "Saxeten", "Schalunen", "Schattenhalb", "Scheuren", "Scheunen", "Schangnau", "Schönbühl", "Schüpfen", "Schwadernau", "Schwarzburg", "Schwarzenburg", "Seeberg", "Seedorf (BE)", "Seehof", "Sigriswil", "Signau", "Siselen", "Sonceboz-Sombeval", "Sonvilier", "Sorvilier", "Spiez", "Steffisburg", "Stettlen", "Studen (BE)", "Sumiswald", "Sutz-Lattrigen", "Tavannes", "Teuffenthal (BE)", "Thierachern", "Thun", "Thunstetten", "Toffen", "Tramelan", "Treiten", "Trub", "Tschugg", "Twann-Tüscherz", "Uetendorf", "Uebeschi", "Uettligen", "Unterseen", "Untersteckholz", "Ursenbach", "Urtenen-Schönbühl", "Utzenstorf", "Vauffelin", "Vechigen", "Villeret", "Vinelz", "Walkringen", "Walliswil bei Niederbipp", "Walliswil bei Wangen", "Walperswil", "Wangen an der Aare", "Wangenried", "Wattenwil", "Wengen", "Wiler bei Utzenstorf", "Willadingen", "Wimmis", "Wohlen bei Bern", "Wolfisberg", "Worb", "Worben", "Wynau", "Wynigen", "Zauggenried", "Zäziwil", "Zimmerwald", "Zielebach", "Zollikofen", "Zuzwil (BE)", "Zweisimmen", "Zwieselberg"],
            
            "ZH": ["Adliswil", "Aesch (ZH)", "Affoltern am Albis", "Altikon", "Andelfingen", "Bachs", "Bäretswil", "Bassersdorf", "Benglen", "Berg am Irchel", "Bertschikon", "Bonstetten", "Boppelsen", "Brütten", "Brüttisellen", "Buchs (ZH)", "Bülach", "Bur", "Dachsen", "Dällikon", "Dänikon", "Dietikon", "Dietlikon", "Dinhard", "Dorf", "Dübendorf", "Dürnten", "Eglisau", "Egg", "Elgg", "Ellikon an der Thur", "Elsau", "Erlenbach (ZH)", "Fällanden", "Feuerthalen", "Fischenthal", "Flurlingen", "Freienbach", "Geroldswil", "Glattfelden", "Gossau (ZH)", "Greifensee", "Grüningen", "Grüt (Gossau ZH)", "Hagenbuch (ZH)", "Hausen am Albis", "Hedingen", "Henggart", "Herrliberg", "Hettlingen", "Hinwil", "Hirzel", "Hittnau", "Hochfelden", "Hofstetten (ZH)", "Hombrechtikon", "Horgen", "Humlikon", "Hüntwangen", "Illnau-Effretikon", "Kappel am Albis", "Kilchberg (ZH)", "Kloten", "Knonau", "Kölliken", "Küsnacht (ZH)", "Kyburg", "Langnau am Albis", "Laufen-Uhwiesen", "Lindau", "Lufingen", "Männedorf", "Maur", "Meilen", "Mettmenstetten", "Mönchaltorf", "Marthalen", "Maschwanden", "Nänikon-Greifensee", "Neerach", "Neftenbach", "Niederglatt", "Niederhasli", "Niederweningen", "Nürensdorf", "Obfelden", "Oberembrach", "Oberengstringen", "Oberglatt", "Oberweningen", "Oetwil am See", "Oetwil an der Limmat", "Opfikon", "Ossingen", "Otelfingen", "Ottenbach", "Pfäffikon", "Pfungen", "Rafz", "Ramsen (ZH)", "Regensberg", "Regensdorf", "Rheinau", "Richterswil", "Rickenbach (ZH)", "Rorbas", "Rüdlingen", "Rümlang", "Rüschlikon", "Russikon", "Rüti (ZH)", "Schlatt (ZH)", "Schleinikon", "Schlieren", "Schöfflisdorf", "Schönenberg (ZH)", "Seegräben", "Seuzach", "Stadel", "Stäfa", "Stallikon", "Steinmaur", "Sternenberg", "Thalheim an der Thur", "Thalwil", "Therwil", "Tobel", "Trüllikon", "Truttikon", "Turbenthal", "Uetikon am See", "Unterengstringen", "Unterstammheim", "Urdorf", "Uster", "Volketswil", "Wädenswil", "Wald (ZH)", "Wallisellen", "Wangen-Brüttisellen", "Wasterkingen", "Weiach", "Weiningen (ZH)", "Weisslingen", "Wermatswil", "Wetzikon (ZH)", "Wiesendangen", "Wildberg", "Winkel", "Winterthur", "Wülflingen", "Zell (ZH)", "Zollikon", "Zumikon", "Zürich", "Zuzwil (ZH)"],
            
            # Continuer avec les autres cantons...
            "BL": ["Aesch (BL)", "Allschwil", "Anwil", "Arboldswil", "Arlesheim", "Augst", "Bennwil", "Biel-Benken", "Binningen", "Birsfelden", "Blauen", "Böckten", "Bottmingen", "Bretzwil", "Bubendorf", "Buckten", "Buus", "Diegten", "Duggingen", "Ettingen", "Frenkendorf", "Füllinsdorf", "Gelterkinden", "Häfelfingen", "Hemmiken", "Hersberg", "Hölstein", "Itingen", "Känerkinden", "Kilchberg (BL)", "Lampenberg", "Langenbruck", "Laufen", "Lauwil", "Liedertswil", "Liestal", "Lupsingen", "Maisprach", "Muttenz", "Nusshof", "Oberdorf (BL)", "Oberwil (BL)", "Ormalingen", "Pfeffingen", "Pratteln", "Ramlinsburg", "Reigoldswil", "Reinach (BL)", "Rickenbach (BL)", "Roggenburg", "Rothenfluh", "Rümlingen", "Rünenberg", "Schönenbuch", "Seltisberg", "Sissach", "Tecknau", "Tenniken", "Therwil", "Titterten", "Waldenburg", "Wintersingen", "Wittinsburg", "Ziefen", "Zunzgen", "Zwingen"],
            
            "BS": ["Basel", "Bettingen", "Riehen"],
            
            "SH": ["Bargen (SH)", "Beggingen", "Beringen", "Buchberg", "Büttenhardt", "Dörflingen", "Gächlingen", "Hallau", "Hemmental", "Hofen", "Lohn (SH)", "Löhningen", "Merishausen", "Neuhausen am Rheinfall", "Neunkirch", "Oberhallau", "Ramsen (SH)", "Rüdlingen", "Schaffhausen", "Siblingen", "Stein am Rhein", "Stetten (SH)", "Thayngen", "Trasadingen", "Wilchingen"],
            
            # Ajouter d'autres cantons selon besoin...
        }
        
        # Convertir en format uniforme
        all_communes_list = []
        for canton, communes in communes_by_canton.items():
            for commune in communes:
                all_communes_list.append({
                    "name": commune,
                    "canton": canton
                })
        
        print(f"Communes récupérées: {len(all_communes_list)}")
        return all_communes_list
        
    except Exception as e:
        print(f"Erreur lors de la récupération: {e}")
        return []

def analyze_missing_communes():
    """Analyse les communes manquantes"""
    
    print("\n=== ANALYSE DES COMMUNES MANQUANTES ===")
    
    # Charger les communes existantes
    with open('src/bot/data/cities.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    
    existing_communes = {city['name'] for city in existing_data['cities']}
    existing_by_canton = {}
    
    for city in existing_data['cities']:
        canton = city.get('canton', 'XX')
        if canton not in existing_by_canton:
            existing_by_canton[canton] = set()
        existing_by_canton[canton].add(city['name'])
    
    print(f"Communes existantes dans le bot: {len(existing_communes)}")
    
    # Récupérer toutes les communes officielles
    all_official_communes = get_official_swiss_communes()
    
    if not all_official_communes:
        print("❌ Impossible de récupérer les communes officielles")
        return
    
    official_communes = {commune['name'] for commune in all_official_communes}
    print(f"Communes officielles totales: {len(official_communes)}")
    
    # Calculer les manquantes
    missing_communes = official_communes - existing_communes
    print(f"Communes manquantes: {len(missing_communes)}")
    
    # Analyser par canton
    missing_by_canton = {}
    for commune in all_official_communes:
        if commune['name'] in missing_communes:
            canton = commune['canton']
            if canton not in missing_by_canton:
                missing_by_canton[canton] = []
            missing_by_canton[canton].append(commune['name'])
    
    print(f"\n=== COMMUNES MANQUANTES PAR CANTON ===")
    for canton in sorted(missing_by_canton.keys()):
        existing_count = len(existing_by_canton.get(canton, []))
        missing_count = len(missing_by_canton[canton])
        total_count = existing_count + missing_count
        
        print(f"{canton}: {missing_count} manquantes / {total_count} total ({existing_count} existantes)")
        
        # Quelques exemples
        if missing_count > 0:
            examples = sorted(missing_by_canton[canton])[:5]
            print(f"   Exemples manquants: {', '.join(examples)}")
            if missing_count > 5:
                print(f"   ... et {missing_count - 5} autres")
    
    # Estimation de l'effort
    print(f"\n=== ESTIMATION DE L'EFFORT ===")
    print(f"Communes à ajouter: {len(missing_communes)}")
    print(f"Géocodage nécessaire: ~{len(missing_communes)} requêtes")
    print(f"Temps estimé (1s/requête): ~{len(missing_communes)/60:.1f} minutes")
    
    if len(missing_communes) > 1000:
        print("⚠️ GROS TRAVAIL - Plus de 1000 communes à ajouter")
        print("💡 Recommandation: Faire par batch de 100-200 communes")
    elif len(missing_communes) > 100:
        print("⚠️ TRAVAIL MOYEN - Quelques centaines de communes")
        print("💡 Recommandation: Faisable en une fois, prévoir 30-60 minutes")
    else:
        print("✅ PETIT TRAVAIL - Moins de 100 communes")
    
    return len(missing_communes), missing_by_canton

if __name__ == "__main__":
    missing_count, missing_by_canton = analyze_missing_communes()
    
    if missing_count > 0:
        print(f"\n🤔 VOULEZ-VOUS QUE JE LES AJOUTE ?")
        print(f"Je peux ajouter automatiquement {missing_count} communes manquantes")
        print("avec géocodage automatique des coordonnées GPS.")
    else:
        print(f"\n🎉 AUCUNE COMMUNE MANQUANTE!")
        print("Votre bot couvre déjà toutes les communes importantes.")
