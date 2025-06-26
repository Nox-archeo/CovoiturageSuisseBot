import os
import signal
import sys

def kill_bot_processes():
    """Version améliorée qui garantit l'arrêt de tous les processus du bot"""
    try:
        # Recherche des processus Python exécutant bot.py ou module bot
        if sys.platform == 'darwin' or sys.platform == 'linux':  # macOS ou Linux
            # Arrête les processus avec bot.py dans la commande
            os.system("pkill -f 'python.*bot.py'")
            # Arrête également les processus lancés avec python -m bot
            os.system("pkill -f 'python.*-m bot'")
            # Vérification et arrêt forcé si nécessaire
            os.system("ps aux | grep -i 'python.*bot' | grep -v grep | awk '{print $2}' | xargs -r kill -9")
        elif sys.platform == 'win32':
            os.system('taskkill /f /im python.exe /fi "WINDOWTITLE eq bot.py"')
            os.system('taskkill /f /im python.exe /fi "COMMANDLINE eq *bot*"')
        
        print("Tentative d'arrêt des processus bot existants.")
        
        # Vérification finale
        import subprocess
        import time
        time.sleep(1)  # Attendre que les processus soient terminés
        
        if sys.platform == 'darwin' or sys.platform == 'linux':
            result = subprocess.run("ps aux | grep -i 'python.*bot' | grep -v grep", shell=True, capture_output=True, text=True)
            if result.stdout.strip():
                print("ATTENTION: Certains processus semblent encore actifs:")
                print(result.stdout)
                print("Tentative d'arrêt forcé...")
                pids = [line.split()[1] for line in result.stdout.splitlines()]
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        print(f"Processus {pid} arrêté.")
                    except:
                        pass
    except Exception as e:
        print(f"Erreur lors de la tentative d'arrêt des processus: {e}")

if __name__ == "__main__":
    kill_bot_processes()
