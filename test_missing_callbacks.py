"""
Script de test pour identifier tous les callbacks manqués dans le bot
"""

import re
import os
from pathlib import Path

def find_all_callback_data():
    """Trouve tous les callback_data utilisés dans le code"""
    callback_patterns = set()
    handlers_dir = Path("handlers")
    
    # Patterns de recherche
    callback_regex = r'callback_data=["\']([^"\']+)["\']'
    
    # Parcourir tous les fichiers Python
    for py_file in handlers_dir.glob("**/*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(callback_regex, content)
                for match in matches:
                    callback_patterns.add(match)
        except Exception as e:
            print(f"Erreur lecture {py_file}: {e}")
    
    # Vérifier aussi le fichier principal
    for main_file in ["bot.py", "webhook_server.py", "payment_handlers.py"]:
        if os.path.exists(main_file):
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(callback_regex, content)
                    for match in matches:
                        callback_patterns.add(match)
            except Exception as e:
                print(f"Erreur lecture {main_file}: {e}")
    
    return sorted(callback_patterns)

def find_registered_patterns():
    """Trouve tous les patterns enregistrés dans les handlers"""
    registered_patterns = set()
    pattern_regex = r'pattern=["\']([^"\']+)["\']'
    
    # Parcourir tous les fichiers
    for py_file in Path(".").glob("**/*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(pattern_regex, content)
                for match in matches:
                    registered_patterns.add(match)
        except Exception as e:
            continue
    
    return sorted(registered_patterns)

def check_pattern_coverage(callback_data, registered_patterns):
    """Vérifie si un callback_data est couvert par un pattern"""
    for pattern in registered_patterns:
        # Convertir le pattern regex en vérification simple
        if pattern == ".*":  # Pattern général
            return True
        if pattern.startswith("^") and pattern.endswith("$"):
            # Pattern exact
            clean_pattern = pattern[1:-1]
            if clean_pattern == callback_data:
                return True
            # Pattern avec groupes
            if "|" in clean_pattern and callback_data in clean_pattern:
                return True
            # Pattern avec wildcards
            if ":" in clean_pattern and ":" in callback_data:
                pattern_prefix = clean_pattern.split(":")[0]
                callback_prefix = callback_data.split(":")[0]
                if pattern_prefix == callback_prefix:
                    return True
        elif pattern in callback_data or callback_data in pattern:
            return True
    
    return False

if __name__ == "__main__":
    print("🔍 ANALYSE DES CALLBACKS NON GÉRÉS")
    print("=" * 50)
    
    # Trouver tous les callbacks
    all_callbacks = find_all_callback_data()
    print(f"📊 Total callbacks trouvés: {len(all_callbacks)}")
    
    # Trouver tous les patterns enregistrés
    registered_patterns = find_registered_patterns()
    print(f"📊 Total patterns enregistrés: {len(registered_patterns)}")
    
    print("\n🔍 CALLBACKS PROBABLEMENT NON GÉRÉS:")
    print("-" * 40)
    
    uncovered_callbacks = []
    
    for callback in all_callbacks:
        if not check_pattern_coverage(callback, registered_patterns):
            uncovered_callbacks.append(callback)
            print(f"❌ {callback}")
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"Total callbacks: {len(all_callbacks)}")
    print(f"Callbacks non gérés: {len(uncovered_callbacks)}")
    print(f"Couverture: {((len(all_callbacks) - len(uncovered_callbacks)) / len(all_callbacks) * 100):.1f}%")
    
    print("\n🏆 CALLBACKS LES PLUS CRITIQUES À CORRIGER:")
    critical_callbacks = [cb for cb in uncovered_callbacks if any(word in cb.lower() for word in 
                         ['back', 'retour', 'menu', 'main', 'profile', 'profil'])]
    
    for callback in critical_callbacks[:10]:
        print(f"🔥 {callback}")
    
    print(f"\n💡 SOLUTION: Ajouter ces handlers dans webhook_server.py:")
    for callback in critical_callbacks[:5]:
        print(f'application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern="^{callback}$"))')
