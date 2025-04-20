from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/covoiturage.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db_session = scoped_session(SessionLocal)

Base = declarative_base()

def get_db():
    """Obtient une session de base de données"""
    try:
        db = db_session()
        return db
    except Exception as e:
        logger.error(f"Erreur de connexion à la base de données: {e}")
        raise

def init_db():
    """Initialise la base de données"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base de données initialisée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise
