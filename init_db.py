import os
from database.db_manager import init_db

def main():
    print("Initialisation de la base de données...")
    
    # S'assurer que le dossier database existe
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Initialiser la base de données
    init_db()

if __name__ == "__main__":
    main()
