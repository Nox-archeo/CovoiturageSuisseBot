# Script : Ajoute les coordonnées GPS à chaque ville du fichier cities.json
# Résultat écrit dans cities.json (modifie l'original)
# Utilise geopy + Nominatim (OpenStreetMap)

import json
import time
import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

INPUT_FILE = os.path.join(os.path.dirname(__file__), "cities.json")
OUTPUT_FILE = INPUT_FILE  # On écrase le fichier original

# Charger le fichier d'origine
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

cities = data["cities"] if "cities" in data else data

geolocator = Nominatim(user_agent="covoiturage-suisse-gps")

for city in cities:
    query = f"{city['name']}, Switzerland"
    try:
        location = geolocator.geocode(query, timeout=10)
        if location:
            city["lat"] = location.latitude
            city["lon"] = location.longitude
        else:
            print(f"Ville non trouvée : {city['name']}")
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Erreur réseau/API pour {city['name']} : {e}")
        # Ne pas supprimer la ville, laisser sans coordonnées
    time.sleep(1)  # Respecter le quota Nominatim

# Écriture du résultat dans le fichier original (cities.json)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"cities": cities}, f, ensure_ascii=False, indent=2)

# Suppression de l'ancien cities_with_coords.json si présent
try:
    os.remove("cities_with_coords.json")
    print("cities_with_coords.json supprimé.")
except FileNotFoundError:
    pass

print(f"Traitement terminé. Résultat écrit dans {OUTPUT_FILE}")
