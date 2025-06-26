import sqlite3

# Connexion à la base SQLite
conn = sqlite3.connect('covoiturage.db')
cur = conn.cursor()

# Ajout de la colonne is_cancelled si elle n'existe pas déjà
try:
    cur.execute("ALTER TABLE trips ADD COLUMN is_cancelled BOOLEAN DEFAULT 0;")
    print("Colonne is_cancelled ajoutée avec succès.")
except Exception as e:
    if 'duplicate column name' in str(e):
        print("La colonne is_cancelled existe déjà.")
    else:
        print(f"Erreur lors de l'ajout de la colonne: {e}")

conn.commit()
conn.close()
