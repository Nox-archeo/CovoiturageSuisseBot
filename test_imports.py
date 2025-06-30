#!/usr/bin/env python3
"""
Test de validation du déploiement
Vérifie que toutes les dépendances peuvent être importées
"""

def test_imports():
    """Test d'import de toutes les dépendances critiques"""
    try:
        print("Testing imports...")
        
        # Test telegram bot
        import telegram
        print("✅ telegram imported successfully")
        
        # Test dotenv
        import dotenv
        print("✅ dotenv imported successfully")
        
        # Test sqlalchemy
        import sqlalchemy
        print("✅ sqlalchemy imported successfully")
        
        # Test paypal
        import paypalrestsdk
        print("✅ paypalrestsdk imported successfully")
        
        # Test fastapi
        import fastapi
        print("✅ fastapi imported successfully")
        
        # Test uvicorn
        import uvicorn
        print("✅ uvicorn imported successfully")
        
        # Test pydantic
        import pydantic
        print("✅ pydantic imported successfully")
        
        # Test geopy
        import geopy
        print("✅ geopy imported successfully")
        
        # Test pytz
        import pytz
        print("✅ pytz imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    test_imports()
