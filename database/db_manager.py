from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import StaticPool
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration automatique de la base de données (SQLite local ou PostgreSQL Render)
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Render/Production : Utiliser PostgreSQL
    logger.info("🚀 Utilisation PostgreSQL pour production")
    if DATABASE_URL.startswith('postgres://'):
        # Render utilise parfois postgres:// au lieu de postgresql://
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Configuration pour PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=20,          # Augmenter la taille de la pool
        max_overflow=30,       # Augmenter le overflow
        pool_timeout=60        # Timeout plus long
    )
else:
    # Local : Utiliser SQLite
    logger.info("🏠 Utilisation SQLite pour développement local")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'covoiturage.db')
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool
    )

# Création de la session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

# Création de la base
Base = declarative_base()

def get_db():
    """Retourne une session de base de données"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e

def init_db():
    """Initialise la base de données"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base de données initialisée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise
