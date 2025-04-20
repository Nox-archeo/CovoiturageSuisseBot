import sqlite3
import os
import requests
from typing import List, Dict, Optional

class SwissLocationService:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '../data/swiss_cities.db')
        self._init_db()

    def _init_db(self):
        """Initialise la base de données SQLite des villes suisses"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Créer la table des villes
        c.execute('''CREATE TABLE IF NOT EXISTS cities
                    (zip TEXT, name TEXT, canton TEXT)''')
        
        # Si la table est vide, charger les données depuis l'API
        if not c.execute("SELECT COUNT(*) FROM cities").fetchone()[0]:
            self._load_cities_from_api()
            
        conn.commit()
        conn.close()

    def _load_cities_from_api(self):
        """Charge toutes les villes suisses depuis l'API officielle"""
        try:
            response = requests.get(
                'https://swisspost.opendatasoft.com/api/records/1.0/search/',
                params={
                    'dataset': 'plz_verzeichnis_v2',
                    'rows': 5000  # Maximum de villes
                }
            )
            
            if response.status_code == 200:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                
                for record in response.json().get('records', []):
                    fields = record.get('fields', {})
                    c.execute(
                        "INSERT INTO cities VALUES (?, ?, ?)",
                        (
                            str(fields.get('postleitzahl', '')),
                            fields.get('ortbez18', ''),
                            fields.get('kanton', '')
                        )
                    )
                    
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Erreur lors du chargement des villes: {e}")

    def search_locations(self, query: str) -> List[Dict[str, str]]:
        """Recherche des villes par NPA ou nom"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Recherche par NPA exact ou nom partiel
        results = c.execute(
            """SELECT zip, name, canton FROM cities 
               WHERE zip = ? OR name LIKE ?""",
            (query, f"%{query}%")
        ).fetchall()
        
        conn.close()
        
        return [
            {'zip': zip, 'name': name, 'canton': canton}
            for zip, name, canton in results
        ]
