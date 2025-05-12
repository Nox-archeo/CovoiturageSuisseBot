import os
import shutil

def reset_bot_state():
    """Réinitialise l'état du bot en supprimant le fichier pickle"""
    pickle_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "data", 
        "conversation_states.pickle"
    )
    
    if os.path.exists(pickle_path):
        os.remove(pickle_path)
        print("✅ État du bot réinitialisé")
    else:
        print("ℹ️ Aucun état à réinitialiser")

if __name__ == "__main__":
    reset_bot_state()
