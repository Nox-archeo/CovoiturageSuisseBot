import sqlite3
import requests
import os

class CitiesDB:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '../data/cities.db')
        self.init_db()
    
    def init_db(self):
        """Initialiser la base de données SQLite"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Créer la table
        c.execute('''
        CREATE TABLE IF NOT EXISTS cities
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         zip TEXT NOT NULL,
         name TEXT NOT NULL,
         canton TEXT)
        ''')
        
        # Vérifier si la table est vide
        if c.execute('SELECT COUNT(*) FROM cities').fetchone()[0] == 0:
            print("Chargement des villes suisses...")
            self.load_cities(c)
            print("Chargement terminé!")
            
        conn.commit()
        conn.close()

    def load_cities(self, cursor):
        """Charger toutes les villes suisses"""
        try:
            # URL de l'API Swiss Post pour les localités
            response = requests.get(
                'https://swisspost.opendatasoft.com/api/records/1.0/search/',
                params={
                    'dataset': 'plz_verzeichnis_v2',
                    'rows': -1  # Toutes les entrées
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                for record in data.get('records', []):
                    fields = record.get('fields', {})
                    cursor.execute(
                        'INSERT INTO cities (zip, name, canton) VALUES (?, ?, ?)',
                        (
                            str(fields.get('postleitzahl')),
                            fields.get('ortbez18'),
                            fields.get('kanton')
                        )
                    )
                print(f"✅ {len(data.get('records', []))} villes chargées")
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            # Charger des données de base au minimum
            basic_cities = [
                ('1700', 'Fribourg', 'FR'),
                ('1630', 'Bulle', 'FR'),
                ('1000', 'Lausanne', 'VD'),
                ('1200', 'Genève', 'GE')
            ]
            for city in basic_cities:
                cursor.execute('INSERT INTO cities (zip, name, canton) VALUES (?, ?, ?)', city)

    def search(self, query):
        """Rechercher une ville"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Recherche par NPA ou nom
        results = c.execute('''
            SELECT zip, name, canton FROM cities 
            WHERE zip LIKE ? OR name LIKE ?
        ''', (f"%{query}%", f"%{query}%")).fetchall()
        
        conn.close()
        return [{'zip': zip, 'name': name, 'canton': canton} for zip, name, canton in results]
