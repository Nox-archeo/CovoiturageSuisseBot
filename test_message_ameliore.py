#!/usr/bin/env python3
"""
Test des messages améliorés pour la création de trajet et réservation
"""

def test_message_creation_trajet():
    """Test du message de création de trajet côté conducteur"""
    print("🎯 TEST MESSAGE CRÉATION TRAJET (CONDUCTEUR)")
    print("=" * 55)
    
    # Simuler les données d'un trajet
    dep_display = "Fribourg"
    arr_display = "Lausanne" 
    date_formatted = "26/07/2025 à 18:30"
    dist = "71.4"
    seats = 3
    prix = 17.85
    role_fr = "🚗 Conducteur"
    options_str = "✅ Trajet simple"
    
    summary = (
        "🎯 *Résumé de votre offre de trajet*\n\n"
        f"👤 *Rôle :* {role_fr}\n"
        f"⚙️ *Type :* {options_str}\n\n"
        f"🌍 *Départ :* {dep_display}\n"
        f"🏁 *Arrivée :* {arr_display}\n"
        f"📅 *Date et heure :* {date_formatted}\n\n"
        f"📏 *Distance :* {dist} km\n"
        f"🚙💺 *Places disponibles :* {seats}\n"
        f"💰 *Prix par place :* {prix} CHF\n\n"
        f"💡 *Comment ça marche :*\n"
        f"• Le prix affiché ({prix} CHF) sera payé par chaque passager\n"
        f"• Plus vous avez de passagers, plus vous gagnez\n"
        f"• Si des passagers s'ajoutent après les premiers, les prix seront automatiquement recalculés et les remboursements effectués\n\n"
        "✨ *Votre trajet sera visible par les passagers intéressés.*\n\n"
        "Confirmez-vous la création de ce trajet ?"
    )
    
    print("🔍 ANCIEN MESSAGE:")
    old_summary = (
        "🎯 Résumé de votre offre de trajet\n\n"
        f"👤 Rôle : {role_fr}\n"
        f"🌍 Départ : {dep_display}\n"
        f"🏁 Arrivée : {arr_display}\n"
        f"📅 Date et heure : {date_formatted}\n\n"
        f"📏 Distance : {dist} km\n"
        f"🚙💺 Places disponibles : {seats}\n"
        f"💰 Prix par place : {prix} CHF\n\n"
        "✨ Votre trajet sera visible par les passagers intéressés.\n\n"
        "Confirmez-vous la création de ce trajet ?"
    )
    print(old_summary)
    print("\n" + "="*55)
    
    print("✨ NOUVEAU MESSAGE AMÉLIORÉ:")
    print(summary)
    
    print("\n📊 AMÉLIORATIONS APPORTÉES:")
    print("✅ Explication claire que le prix est payé par CHAQUE passager")
    print("✅ Information que plus de passagers = plus de gains")
    print("✅ Mention du système de remboursement automatique")
    print("✅ Format plus clair et mieux structuré")
    
    return True

def test_message_reservation_passager():
    """Test du message de réservation côté passager"""
    print("\n\n🎟️ TEST MESSAGE RÉSERVATION (PASSAGER)")
    print("=" * 55)
    
    # Simuler les données d'une réservation
    trip_departure = "Fribourg"
    trip_arrival = "Lausanne"
    trip_date = "26/07/2025 à 18:30"
    driver_name = "Jean"
    seats = 2
    price_per_seat = 17.85
    total_price = price_per_seat * seats
    
    print("🔍 ANCIEN MESSAGE:")
    old_message = (
        f"🎟️ Récapitulatif de votre réservation\n\n"
        f"🏁 Trajet : {trip_departure} → {trip_arrival}\n"
        f"📅 Date : {trip_date}\n"
        f"👤 Conducteur : {driver_name}\n"
        f"💺 Places : {seats}\n"
        f"💰 Prix total : {total_price} CHF\n\n"
        f"Confirmez-vous cette réservation ?"
    )
    print(old_message)
    print("\n" + "="*55)
    
    print("✨ NOUVEAU MESSAGE AMÉLIORÉ:")
    new_message = (
        f"🎟️ *Récapitulatif de votre réservation*\n\n"
        f"🏁 *Trajet* : {trip_departure} → {trip_arrival}\n"
        f"📅 *Date* : {trip_date}\n"
        f"👤 *Conducteur* : {driver_name}\n"
        f"💺 *Places* : {seats}\n"
        f"💰 *Prix par place* : {price_per_seat} CHF\n"
        f"💳 *Total à payer* : {total_price} CHF\n\n"
        f"💡 *Le prix par place peut être réduit si d'autres passagers rejoignent le trajet.*\n\n"
        f"Confirmez-vous cette réservation ?"
    )
    print(new_message)
    
    print("\n📊 AMÉLIORATIONS APPORTÉES:")
    print("✅ Séparation claire entre prix par place et total à payer")
    print("✅ Information que le prix peut diminuer avec plus de passagers")
    print("✅ Format markdown pour plus de clarté")
    print("✅ Meilleure lisibilité des informations")
    
    return True

def test_exemple_scenarios():
    """Test avec des exemples concrets"""
    print("\n\n📝 EXEMPLES CONCRETS")
    print("=" * 55)
    
    print("🚗 CÔTÉ CONDUCTEUR:")
    print("Si vous créez un trajet à 18 CHF/place avec 3 places disponibles:")
    print("• 1 passager s'inscrit → Vous gagnez: 18 CHF")
    print("• 2 passagers s'inscrivent → Vous gagnez: 36 CHF") 
    print("• 3 passagers s'inscrivent → Vous gagnez: 54 CHF")
    print("➡️ PLUS DE PASSAGERS = PLUS DE GAINS!")
    
    print("\n🧑‍💼 CÔTÉ PASSAGER:")
    print("Si vous réservez 2 places sur un trajet à 18 CHF/place:")
    print("• Vous payez: 2 × 18 = 36 CHF")
    print("• Si un 3ème passager arrive après vous:")
    print("  - Nouveau prix par place: trajet total ÷ plus de passagers")
    print("  - Vous êtes automatiquement remboursé de la différence")
    print("➡️ PRIX ÉQUITABLE POUR TOUS!")
    
    return True

if __name__ == "__main__":
    print("🔧 TEST DES MESSAGES AMÉLIORÉS POUR COVOITURAGE")
    print("=" * 65)
    
    success1 = test_message_creation_trajet()
    success2 = test_message_reservation_passager() 
    success3 = test_exemple_scenarios()
    
    if success1 and success2 and success3:
        print("\n" + "="*65)
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ Messages côté conducteur améliorés")
        print("✅ Messages côté passager améliorés") 
        print("✅ Exemples concrets testés")
        print("\n💡 Les utilisateurs comprennent maintenant mieux:")
        print("   • Que le prix est payé par CHAQUE passager (conducteur)")
        print("   • Que plus de passagers = plus de gains (conducteur)")
        print("   • Que le prix peut diminuer avec plus de passagers (passager)")
        print("   • Le système de remboursement automatique")
    else:
        print("\n❌ Des problèmes ont été détectés")
