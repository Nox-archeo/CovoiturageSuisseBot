from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

Base = declarative_base()

# Configuration de la base de données
database_path = os.path.join(os.path.dirname(__file__), 'covoiturage.db')
DATABASE_URL = f'sqlite:///{database_path}'

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialise la base de données"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Base de données initialisée avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
        raise

def get_db():
    """Retourne une session de base de données"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
