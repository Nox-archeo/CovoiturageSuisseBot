import os
from database.db_manager import engine, Base
from database.models import User, Trip, Booking, Message, Review

def reset_database():
    # Supprimer la base de données existante
    db_path = 'database/covoiturage.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Créer les tables
    Base.metadata.create_all(engine)
    print("Base de données réinitialisée avec succès!")

if __name__ == "__main__":
    reset_database()
