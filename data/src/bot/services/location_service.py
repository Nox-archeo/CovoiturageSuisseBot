import requests
from dataclasses import dataclass

@dataclass
class Location:
    name: str
    zipcode: str
    canton: str

class LocationService:
    @staticmethod
    def search_locations(query: str) -> list[Location]:
        try:
            # Utilisation de l'API officielle des communes suisses
            response = requests.get(
                'https://api.ch.ch/addresses/locations',
                params={
                    'searchtext': query,
                    'lang': 'fr',
                    'limit': 10
                },
                headers={
                    'Accept': 'application/json'
                }
            )
            
            if response.status_code != 200:
                return []

            results = response.json()
            return [
                Location(
                    name=loc['name'],
                    zipcode=loc['zip'],
                    canton=loc['canton']
                )
                for loc in results
            ]
        except Exception as e:
            print(f"Erreur de recherche: {e}")
            return []
