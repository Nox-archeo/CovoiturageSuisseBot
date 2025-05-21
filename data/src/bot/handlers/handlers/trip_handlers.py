from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
import json
import os
from unidecode import unidecode  # Pour gérer les accents
import sys

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.swiss_location_service import SwissLocationService
from services.cities_db import CitiesDB

# États de la conversation
CHOOSING_TYPE = 0
CHOOSING_DEPARTURE = 1
CHOOSING_DESTINATION = 2
CHOOSING_DATE = 3  # Ajout de l'étape date
CHOOSING_TIME = 4  # Ajout de l'étape heure
CHOOSING_SEATS = 5 # Ajout du nombre de places
CHOOSING_PRICE = 6 # Ajout du prix
CONFIRMING = 7

def register(application):
    """Enregistre le handler principal pour la création de trajet"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('creer', start_trip)],
        states={
            CHOOSING_TYPE: [
                CallbackQueryHandler(handle_trip_type, pattern='^type_'),
                CommandHandler('creer', start_trip)  # Permettre de redémarrer
            ],
            CHOOSING_DEPARTURE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_input),
                CallbackQueryHandler(handle_location_callback, pattern='^loc_'),
                CommandHandler('creer', start_trip)  # Permettre de redémarrer
            ],
            CHOOSING_DESTINATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_input),
                CallbackQueryHandler(handle_location_callback, pattern='^loc_'),
                CommandHandler('creer', start_trip)  # Permettre de redémarrer
            ],
            CONFIRMING: [
                CallbackQueryHandler(handle_confirm, pattern='^confirm'),
                CallbackQueryHandler(handle_modify, pattern='^modify_'),
                CommandHandler('creer', start_trip)  # Permettre de redémarrer
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True,
        per_chat=False
    )
    
    # Supprimer tous les autres handlers pour éviter les conflits
    application.handlers.clear()
    application.add_handler(conv_handler)

async def start_trip(update: Update, context):
    """Démarre la création d'un trajet"""
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("🚗 Trajet simple", callback_data="type_simple")],
        [InlineKeyboardButton("🔄 Aller-retour", callback_data="type_return")],
        [InlineKeyboardButton("📅 Trajet régulier", callback_data="type_regular")]
    ]

    await update.message.reply_text(
        """🚗 <b>Création d'un nouveau trajet</b>

Choisissez votre type de trajet:

1️⃣ <b>Trajet simple</b>
   • Un aller uniquement
   • Une seule fois

2️⃣ <b>Aller-retour</b>
   • Aller ET retour le même jour
   • Prix pour les deux trajets

3️⃣ <b>Trajet régulier</b>
   • Se répète chaque semaine
   • Même horaire""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return CHOOSING_TYPE

async def handle_trip_type(update: Update, context):
    """Gère le choix du type de trajet"""
    query = update.callback_query
    await query.answer()
    
    trip_type = query.data.split('_')[1]
    context.user_data['trip_type'] = trip_type
    context.user_data['is_return'] = (trip_type == 'return')
    
    await query.edit_message_text(
        """🚗 <b>Création d'un trajet</b>

Étape 1: Choisissez votre ville de départ
• Par code postal (ex: 1700)
• Par nom de ville (ex: Fribourg)""",
        parse_mode='HTML'
    )
    return CHOOSING_DEPARTURE

async def start_location_search(update: Update, context):
    """Démarre la recherche de la localisation"""
    message = """🚗 <b>Création d'un nouveau trajet</b>

<b>Étape 1:</b> Point de départ 📍
─────────────────────────

Recherchez n'importe quelle ville suisse:

🔍 Par code postal:
   • <code>1700</code> (Fribourg)
   • <code>1630</code> (Bulle)
   • etc...

🌍 Par nom de ville:
   • Fribourg, Bulle, Sion...
   • Petit village ou grande ville

💡 <i>Tapez votre recherche ci-dessous</i>"""

    await update.message.reply_text(text=message, parse_mode='HTML')
    return CHOOSING_DEPARTURE

def load_swiss_cities():
    """Charge la liste des villes depuis le fichier JSON"""
    file_path = os.path.join(os.path.dirname(__file__), '../data/swiss_cities.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['cities']
    except Exception as e:
        print(f"Erreur lors du chargement des villes: {e}")
        return []

async def handle_location_input(update: Update, context):
    """Gère la recherche de ville"""
    query = update.message.text.strip()
    
    # Chemin absolu vers cities.json
    cities_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'cities.json'
    )
    
    try:
        with open(cities_file, 'r', encoding='utf-8') as f:
            cities = json.load(f)['cities']
        
        # Recherche améliorée
        results = [
            city for city in cities
            if (query == city['npa'] or 
                query.lower() in city['name'].lower())
        ][:8]
        
        if results:
            buttons = []
            for city in results:
                buttons.append([
                    InlineKeyboardButton(
                        f"🏙️ {city['name']} ({city['npa']})",
                        callback_data=f"loc_{city['npa']}_{city['name']}"
                    )
                ])
            
            await update.message.reply_text(
                "📍 <b>Villes trouvées:</b>\nSélectionnez votre ville:",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='HTML'
            )
            return context.user_data.get('current_step', CHOOSING_DEPARTURE)
        
        await update.message.reply_text(
            """❌ <b>Ville non trouvée</b>

<i>Vous pouvez chercher:</i>
• Par code postal (ex: 1700)
• Par nom de ville (ex: Fribourg)

Réessayez avec une ville suisse.""",
            parse_mode='HTML'
        )
        return context.user_data.get('current_step', CHOOSING_DEPARTURE)
        
    except Exception as e:
        logger.error(f"Erreur recherche ville: {str(e)}")
        await update.message.reply_text(
            "⚠️ Erreur technique. Tapez /cancel pour recommencer."
        )
        return ConversationHandler.END

async def handle_location_callback(update: Update, context):
    """Gère la sélection d'une ville"""
    query = update.callback_query
    await query.answer()
    
    _, zip_code, city = query.data.split('_')
    
    if context.user_data.get('current_step') == CHOOSING_DESTINATION:
        context.user_data['destination'] = {'city': city, 'zip': zip_code}
        # Afficher le résumé avec possibilité de modification
        await show_summary(update, context)
        return CONFIRMING
    else:
        context.user_data['departure'] = {'city': city, 'zip': zip_code}
        # Passer à la destination
        await ask_for_destination(update, context)
        return CHOOSING_DESTINATION

async def ask_for_destination(update: Update, context):
    """Demande la destination"""
    context.user_data['current_step'] = CHOOSING_DESTINATION
    message = """📍 <b>Choix de la destination</b>

Vous pouvez chercher:
• Par code postal (ex: 1700)
• Par nom de ville (ex: Fribourg)

<i>Tapez votre recherche</i>"""
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            text=message,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML'
        )

async def show_summary(update: Update, context):
    """Montre le résumé du trajet"""
    dep = context.user_data.get('departure', {})
    dest = context.user_data.get('destination', {})
    trip_type = context.user_data.get('trip_type', 'simple')
    
    type_text = {
        'simple': 'Trajet simple (aller)',
        'return': 'Aller-retour',
        'regular': 'Trajet régulier'
    }
    
    message = f"""🚗 <b>Résumé du trajet</b>

<b>Type:</b> {type_text[trip_type]}
📍 <b>Départ:</b> {dep.get('city')} ({dep.get('npa')})
🏁 <b>Destination:</b> {dest.get('city')} ({dest.get('npa')})

{' 🔄 Note: Le prix inclut l\'aller ET le retour' if trip_type == 'return' else ''}

<i>Vous pouvez modifier ou confirmer:</i>"""
    
    buttons = [
        [InlineKeyboardButton("✏️ Modifier départ", callback_data="modify_departure")],
        [InlineKeyboardButton("✏️ Modifier destination", callback_data="modify_destination")],
        [InlineKeyboardButton("✅ Confirmer", callback_data="confirm")]
    ]
    
    await update.callback_query.message.edit_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='HTML'
    )

async def handle_modify(update: Update, context):
    """Gère la modification d'une étape"""
    query = update.callback_query
    await query.answer()
    
    if "departure" in query.data:
        context.user_data['current_step'] = CHOOSING_DEPARTURE
        await start_trip(update, context)
    else:
        context.user_data['current_step'] = CHOOSING_DESTINATION
        await ask_for_destination(update, context)
    
    return context.user_data['current_step']

async def handle_confirm(update: Update, context):
    """Gère la confirmation du trajet"""
    await update.callback_query.message.reply_text(
        "Votre trajet a été créé avec succès ! 🚗"
    )
    return ConversationHandler.END

async def cancel(update: Update, context):
    """Annule la création du trajet"""
    await update.message.reply_text(
        "Création du trajet annulée. Tapez /creer pour recommencer."
    )
    return ConversationHandler.END

async def handle_date_input(update: Update, context):
    """Gère la saisie de la date"""
    # Validation de la date
    # ...existing code...

async def handle_time_input(update: Update, context):
    """Gère la saisie de l'heure"""
    # Validation de l'heure
    # ...existing code...

async def handle_seats_input(update: Update, context):
    """Gère le nombre de places"""
    # Validation des places
    # ...existing code...

async def handle_price_input(update: Update, context):
    """Gère le prix du trajet"""
    # Validation du prix
    # ...existing code...
