import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration du bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if TELEGRAM_BOT_TOKEN:
    # Enlever les guillemets si présents
    TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN.strip('"')
    
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Token Telegram non trouvé dans le fichier .env")

# Base de données
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./covoiturage.db')

# Debug mode
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
