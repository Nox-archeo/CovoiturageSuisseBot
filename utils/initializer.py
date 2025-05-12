import os
from pathlib import Path
from .cities_manager import CitiesManager

class BotInitializer:
    @staticmethod
    def init():
        """Initialise toutes les dépendances du bot"""
        # Vérifier les fichiers requis
        required_paths = [
            'src/bot/data/cities.json',
            '.env'
        ]
        
        for path in required_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"Fichier requis manquant : {path}")

        # Initialiser le gestionnaire de villes
        cities_path = Path('src/bot/data/cities.json')
        cities_manager = CitiesManager(cities_path)
        
        return {
            'cities_manager': cities_manager
        }
