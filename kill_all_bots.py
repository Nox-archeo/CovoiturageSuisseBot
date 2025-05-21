import os
import signal
import sys

def kill_bot_processes():
    """Version simplifiée qui n'utilise pas psutil (non installé)"""
    try:
        # Recherche des processus Python exécutant bot.py
        if sys.platform == 'darwin':  # macOS
            os.system("pkill -f 'python.*bot.py'")
        elif sys.platform == 'linux':
            os.system("pkill -f 'python.*bot.py'")
        elif sys.platform == 'win32':
            os.system('taskkill /f /im python.exe /fi "WINDOWTITLE eq bot.py"')
        
        print("Tentative d'arrêt des processus bot existants.")
    except Exception as e:
        print(f"Erreur lors de la tentative d'arrêt des processus: {e}")

if __name__ == "__main__":
    kill_bot_processes()
