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

# FORCER PostgreSQL TOUJOURS (même en local) pour éviter les problèmes de synchronisation
if not DATABASE_URL:
    # 🚨 ERREUR: Ne jamais exposer l'URL PostgreSQL en dur !
    # L'URL doit être dans .env ou variables d'environnement Render
    logger.error("❌ DATABASE_URL manquante ! Configurez la variable d'environnement.")
    raise ValueError("DATABASE_URL doit être configurée dans .env ou variables d'environnement")

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
    # Ce code ne devrait plus jamais être exécuté
    logger.error("❌ ERREUR: PostgreSQL devrait toujours être utilisé")
    raise Exception("PostgreSQL requis pour éviter les problèmes de synchronisation")

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
