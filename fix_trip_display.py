#!/usr/bin/env python3
"""
Script pour corriger l'affichage des trajets avec boutons individuels
"""

def fix_trip_display():
    with open('/Users/margaux/CovoiturageSuisse/handlers/trip_handlers.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver et remplacer la section problématique pour les conducteurs
    old_driver_section = '''            # Construire le message avec trajets
            message = f"🚗 *{title} (Conducteur)*\\n\\n"
            keyboard = []
            
            for trip in trips:
                departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
                
                # Compter les réservations
                booking_count = db.query(Booking).filter(
                    Booking.trip_id == trip.id, 
                    Booking.status.in_(["pending", "confirmed", "completed"])
                ).count()
                
                # Icône selon l'état
                icon = "🚗" if time_period == "future" else "🏁"
                
                message += (
                    f"{icon} {trip.departure_city} → {trip.arrival_city}\\n"
                    f"📅 {departure_date}\\n"
                    f"💰 {trip.price_per_seat:.2f} CHF/place • 💺 {booking_count}/{trip.seats_available}\\n\\n"
                )
                
                # Boutons individuels pour chaque trajet
                if time_period == "future":
                    # Trajets à venir : Modifier, Supprimer, Signaler
                    trip_buttons = [
                        InlineKeyboardButton("� Modifier", callback_data=f"trip:edit:{trip.id}"),
                        InlineKeyboardButton("❌ Supprimer", callback_data=f"trip:delete:{trip.id}"),
                        InlineKeyboardButton("⚠️ Signaler", callback_data=f"trip:report:{trip.id}")
                    ]
                else:
                    # Trajets passés : Voir détails, Signaler
                    trip_buttons = [
                        InlineKeyboardButton("👁️ Détails", callback_data=f"trip:view:{trip.id}"),
                        InlineKeyboardButton("⚠️ Signaler", callback_data=f"trip:report:{trip.id}")
                    ]
                
                keyboard.append(trip_buttons)'''
    
    new_driver_section = '''            # Envoyer chaque trajet avec ses boutons individuels
            header_message = f"🚗 *{title} (Conducteur)*\\n\\n📊 {len(trips)} trajet(s) trouvé(s)"
            await query.edit_message_text(header_message, parse_mode="Markdown")
            
            # Envoyer chaque trajet individuellement avec ses boutons
            for trip in trips:
                departure_date = trip.departure_time.strftime("%d/%m/%Y à %H:%M")
                
                # Compter les réservations
                booking_count = db.query(Booking).filter(
                    Booking.trip_id == trip.id, 
                    Booking.status.in_(["pending", "confirmed", "completed"])
                ).count()
                
                # Icône selon l'état
                icon = "🚗" if time_period == "future" else "🏁"
                
                trip_message = (
                    f"{icon} {trip.departure_city} → {trip.arrival_city}\\n"
                    f"📅 {departure_date}\\n"
                    f"💰 {trip.price_per_seat:.2f} CHF/place • 💺 {booking_count}/{trip.seats_available}"
                )
                
                # Boutons individuels pour CE trajet spécifique
                if time_period == "future":
                    trip_buttons = [
                        [InlineKeyboardButton("✏️ Modifier", callback_data=f"trip:edit:{trip.id}")],
                        [InlineKeyboardButton("🗑 Supprimer", callback_data=f"trip:delete:{trip.id}")],
                        [InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip.id}")]
                    ]
                else:
                    trip_buttons = [
                        [InlineKeyboardButton("👁️ Détails", callback_data=f"trip:view:{trip.id}")],
                        [InlineKeyboardButton("🚩 Signaler", callback_data=f"trip:report:{trip.id}")]
                    ]
                
                # Envoyer ce trajet avec SES boutons juste en dessous
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=trip_message,
                    reply_markup=InlineKeyboardMarkup(trip_buttons),
                    parse_mode="Markdown"
                )'''
    
    if old_driver_section in content:
        content = content.replace(old_driver_section, new_driver_section)
        print("✅ Section conducteur corrigée")
    else:
        print("❌ Section conducteur non trouvée")
    
    # Sauvegarder le fichier
    with open('/Users/margaux/CovoiturageSuisse/handlers/trip_handlers.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fichier sauvegardé")

if __name__ == "__main__":
    fix_trip_display()
