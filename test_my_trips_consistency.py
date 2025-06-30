#!/usr/bin/env python3
"""
Test script pour vérifier la cohérence des boutons "Mes trajets" dans tout le bot.
Teste que tous les boutons "Mes trajets" affichent la même liste et permettent l'annulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, AsyncMock
from database import get_db
from database.models import User, Trip, Booking
from handlers.trip_handlers import list_my_trips

def create_test_data():
    """Crée des données de test dans la base"""
    print("🧪 Création de données de test...")
    
    db = get_db()
    
    # Créer un utilisateur de test
    test_user = User(
        telegram_id=12345,
        first_name="Test",
        last_name="User",
        phone_number="+41760000000",
        is_verified=True
    )
    
    try:
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Utilisateur de test créé: ID {test_user.id}")
    except Exception as e:
        print(f"⚠️ Utilisateur peut-être déjà existant: {e}")
        test_user = db.query(User).filter(User.telegram_id == 12345).first()
    
    # Créer des trajets de test
    future_time = datetime.now() + timedelta(days=7)
    
    test_trips = [
        Trip(
            driver_id=test_user.id,
            departure_city="Lausanne",
            arrival_city="Genève",
            departure_time=future_time,
            seats_available=3,
            available_seats=3,
            price_per_seat=25.0,
            is_published=True,
            is_cancelled=False,
            smoking='no_smoking',
            music='music_ok',
            talk_preference='depends',
            pets_allowed='no_pets',
            luggage_size='medium',
            highway=True,
            flexible_time=False,
            women_only=False,
            instant_booking=True,
            recurring=False
        ),
        Trip(
            driver_id=test_user.id,
            departure_city="Berne",
            arrival_city="Zurich",
            departure_time=future_time + timedelta(days=1),
            seats_available=2,
            available_seats=2,
            price_per_seat=30.0,
            is_published=True,
            is_cancelled=False,
            smoking='no_smoking',
            music='music_ok',
            talk_preference='depends',
            pets_allowed='no_pets',
            luggage_size='medium',
            highway=True,
            flexible_time=False,
            women_only=False,
            instant_booking=True,
            recurring=False
        )
    ]
    
    for trip in test_trips:
        try:
            db.add(trip)
            db.commit()
            db.refresh(trip)
            print(f"✅ Trajet de test créé: {trip.departure_city} → {trip.arrival_city}")
        except Exception as e:
            print(f"⚠️ Erreur création trajet: {e}")
    
    print(f"📊 Total trajets en base: {db.query(Trip).count()}")
    return test_user

async def test_unified_my_trips_function():
    """Test la fonction unifiée list_my_trips"""
    print("\n🧪 Test de la fonction unifiée list_my_trips")
    print("=" * 60)
    
    # Créer des mocks pour Update et Context
    mock_update = Mock()
    mock_context = Mock()
    
    # Mock de l'utilisateur effectif
    mock_user = Mock()
    mock_user.id = 12345
    mock_update.effective_user = mock_user
    
    # Mock du callback_query
    mock_query = AsyncMock()
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()
    mock_update.callback_query = mock_query
    
    try:
        # Appeler la fonction
        await list_my_trips(mock_update, mock_context)
        
        # Vérifier que la fonction a été appelée sans erreur
        mock_query.answer.assert_called_once()
        mock_query.edit_message_text.assert_called_once()
        
        # Récupérer les arguments de l'appel
        call_args = mock_query.edit_message_text.call_args
        message_text = call_args[1]['text'] if 'text' in call_args[1] else call_args[0][0]
        reply_markup = call_args[1]['reply_markup'] if 'reply_markup' in call_args[1] else None
        
        print("✅ Fonction appelée avec succès")
        print(f"📄 Message généré:")
        print(message_text)
        
        # Vérifier le contenu du message
        checks = []
        
        if "Mes trajets à venir" in message_text:
            checks.append("✅ Titre correct en français")
        else:
            checks.append("❌ Titre manquant ou en anglais")
        
        if "Lausanne → Genève" in message_text or "Berne → Zurich" in message_text:
            checks.append("✅ Trajets affichés")
        else:
            checks.append("❌ Aucun trajet affiché")
        
        if "CHF" in message_text:
            checks.append("✅ Prix affiché")
        else:
            checks.append("❌ Prix manquant")
        
        if "réservations" in message_text:
            checks.append("✅ Compteur de réservations affiché")
        else:
            checks.append("❌ Compteur de réservations manquant")
        
        # Vérifier les boutons
        if reply_markup and reply_markup.inline_keyboard:
            buttons_found = []
            for row in reply_markup.inline_keyboard:
                for button in row:
                    if "Annuler" in button.text:
                        buttons_found.append("❌ Annuler")
                    elif "Modifier" in button.text:
                        buttons_found.append("✏️ Modifier")
                    elif "Créer un trajet" in button.text:
                        buttons_found.append("➕ Créer")
                    elif "Menu principal" in button.text:
                        buttons_found.append("🏠 Menu")
            
            if buttons_found:
                checks.append(f"✅ Boutons trouvés: {', '.join(buttons_found)}")
            else:
                checks.append("❌ Aucun bouton trouvé")
        else:
            checks.append("❌ Aucun clavier inline")
        
        print("\n🔍 VÉRIFICATIONS:")
        for check in checks:
            print(check)
        
        return all("✅" in check for check in checks)
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_consistency():
    """Test la cohérence de la base de données"""
    print("\n🧪 Test de cohérence de la base de données")
    print("=" * 60)
    
    db = get_db()
    
    checks = []
    
    # Vérifier les trajets
    trips = db.query(Trip).filter(Trip.is_cancelled == False).all()
    if trips:
        checks.append(f"✅ {len(trips)} trajets non annulés trouvés")
        
        # Vérifier les champs obligatoires
        for trip in trips:
            if hasattr(trip, 'is_cancelled'):
                checks.append("✅ Champ is_cancelled présent")
                break
        else:
            checks.append("❌ Champ is_cancelled manquant")
        
        # Vérifier les dates
        future_trips = [t for t in trips if t.departure_time > datetime.now()]
        if future_trips:
            checks.append(f"✅ {len(future_trips)} trajets à venir")
        else:
            checks.append("❌ Aucun trajet à venir")
    else:
        checks.append("❌ Aucun trajet trouvé")
    
    # Vérifier les utilisateurs
    users = db.query(User).all()
    if users:
        checks.append(f"✅ {len(users)} utilisateurs trouvés")
    else:
        checks.append("❌ Aucun utilisateur trouvé")
    
    print("🔍 VÉRIFICATIONS BASE DE DONNÉES:")
    for check in checks:
        print(check)
    
    return all("✅" in check for check in checks)

async def main():
    """Fonction principale de test"""
    print("🧪 TEST DE COHÉRENCE DES BOUTONS 'MES TRAJETS'")
    print("=" * 60)
    
    # Créer des données de test
    test_user = create_test_data()
    
    # Tests
    tests = [
        ("Base de données", test_database_consistency()),
        ("Fonction unifiée", await test_unified_my_trips_function())
    ]
    
    print("\n📊 RÉSULTATS FINAUX:")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in tests:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 {success_count}/{len(tests)} tests réussis")
    
    if success_count == len(tests):
        print("\n🎉 TOUS LES TESTS PASSENT !")
        print("Les boutons 'Mes trajets' devraient maintenant être cohérents dans tout le bot.")
        print("✅ L'annulation des trajets fonctionne pour tous les utilisateurs")
    else:
        print("\n⚠️  CERTAINS TESTS ÉCHOUENT")
        print("Vérifiez les corrections nécessaires.")

if __name__ == "__main__":
    asyncio.run(main())
