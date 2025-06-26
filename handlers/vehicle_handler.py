import json
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters, CallbackContext
)
from handlers.profile_handler import show_profile_dashboard, PROFILE_MAIN

USERS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'users.json')

# États de la conversation véhicule
(
    VEHICLE_BRAND, VEHICLE_MODEL, VEHICLE_YEAR, VEHICLE_COLOR, VEHICLE_SEATS,
    VEHICLE_FUEL, VEHICLE_SMOKING, VEHICLE_CLIM, VEHICLE_EDIT_FIELD
) = range(9)

FUEL_CHOICES = ["Essence", "Diesel", "Électrique", "Hybride"]
OUI_NON = ["Oui", "Non"]

# --- Utils ---
def load_users():
    if not os.path.exists(USERS_JSON_PATH):
        return {}
    with open(USERS_JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    tmp_path = USERS_JSON_PATH + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, USERS_JSON_PATH)

# --- Conversation Handlers ---
async def start_vehicle_wizard(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="vehicle:cancel")]]
    await update.callback_query.edit_message_text(
        "Quelle est la marque de votre voiture ?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return VEHICLE_BRAND

async def vehicle_brand(update: Update, context: CallbackContext):
    brand = update.message.text.strip()
    if not brand:
        await update.message.reply_text("Merci d'entrer une marque valide.")
        return VEHICLE_BRAND
    context.user_data['vehicle'] = {'brand': brand}
    await update.message.reply_text("Modèle de la voiture ?")
    return VEHICLE_MODEL

async def vehicle_model(update: Update, context: CallbackContext):
    model = update.message.text.strip()
    if not model:
        await update.message.reply_text("Merci d'entrer un modèle valide.")
        return VEHICLE_MODEL
    context.user_data['vehicle']['model'] = model
    await update.message.reply_text("Année du véhicule ? (ex: 2022)")
    return VEHICLE_YEAR

async def vehicle_year(update: Update, context: CallbackContext):
    year = update.message.text.strip()
    if not year.isdigit() or not (1950 <= int(year) <= 2100):
        await update.message.reply_text("Merci d'entrer une année valide (ex: 2022).")
        return VEHICLE_YEAR
    context.user_data['vehicle']['year'] = int(year)
    await update.message.reply_text("Couleur de la voiture ?")
    return VEHICLE_COLOR

async def vehicle_color(update: Update, context: CallbackContext):
    color = update.message.text.strip()
    if not color:
        await update.message.reply_text("Merci d'entrer une couleur valide.")
        return VEHICLE_COLOR
    context.user_data['vehicle']['color'] = color
    await update.message.reply_text("Nombre de places disponibles ? (1-8)")
    return VEHICLE_SEATS

async def vehicle_seats(update: Update, context: CallbackContext):
    seats = update.message.text.strip()
    if not seats.isdigit() or not (1 <= int(seats) <= 8):
        await update.message.reply_text("Merci d'entrer un nombre de places valide (1-8).")
        return VEHICLE_SEATS
    context.user_data['vehicle']['seats'] = int(seats)
    kb = ReplyKeyboardMarkup([[c] for c in FUEL_CHOICES], resize_keyboard=True)
    await update.message.reply_text("Type de carburant ?", reply_markup=kb)
    return VEHICLE_FUEL

async def vehicle_fuel(update: Update, context: CallbackContext):
    fuel = update.message.text.strip()
    if fuel not in FUEL_CHOICES:
        await update.message.reply_text(f"Merci de choisir parmi : {', '.join(FUEL_CHOICES)}.")
        return VEHICLE_FUEL
    context.user_data['vehicle']['fuel'] = fuel
    kb = ReplyKeyboardMarkup([[c] for c in OUI_NON], resize_keyboard=True)
    await update.message.reply_text("Véhicule fumeur ? (Oui/Non)", reply_markup=kb)
    return VEHICLE_SMOKING

async def vehicle_smoking(update: Update, context: CallbackContext):
    val = update.message.text.strip().lower()
    if val not in [x.lower() for x in OUI_NON]:
        await update.message.reply_text("Merci de répondre par Oui ou Non.")
        return VEHICLE_SMOKING
    context.user_data['vehicle']['smoking'] = (val == "oui")
    kb = ReplyKeyboardMarkup([[c] for c in OUI_NON], resize_keyboard=True)
    await update.message.reply_text("Climatisation ? (Oui/Non)", reply_markup=kb)
    return VEHICLE_CLIM

async def vehicle_clim(update: Update, context: CallbackContext):
    val = update.message.text.strip().lower()
    if val not in [x.lower() for x in OUI_NON]:
        await update.message.reply_text("Merci de répondre par Oui ou Non.")
        return VEHICLE_CLIM
    context.user_data['vehicle']['air_conditioning'] = (val == "oui")
    # Sauvegarde users.json
    user_id = update.effective_user.id
    users = load_users()
    user_entry = users.get(str(user_id), {})
    user_entry["vehicle"] = context.user_data['vehicle']
    users[str(user_id)] = user_entry
    save_users(users)
    v = context.user_data['vehicle']
    resume = (
        f"🚗 Véhicule enregistré :\n"
        f"Marque : {v['brand']}\n"
        f"Modèle : {v['model']}\n"
        f"Année : {v['year']}\n"
        f"Couleur : {v['color']}\n"
        f"Places dispo : {v['seats']}\n"
        f"Carburant : {v['fuel']}\n"
        f"Fumeur : {'Oui' if v['smoking'] else 'Non'}\n"
        f"Climatisation : {'Oui' if v['air_conditioning'] else 'Non'}"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]]
    # Supprime le clavier Oui/Non
    await update.message.reply_text(resume, reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(
        "Cliquez sur le bouton ci-dessous pour revenir au profil :",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data.pop('vehicle', None)
    return ConversationHandler.END

# Aperçu véhicule avec boutons de modification
async def show_vehicle_summary(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    users = load_users()
    user_entry = users.get(str(user_id), {})
    v = user_entry.get("vehicle")
    if not v:
        # Si pas de véhicule, démarrer le wizard complet
        await start_vehicle_wizard(update, context)
        return VEHICLE_BRAND
    resume = (
        f"🚗 Véhicule enregistré :\n"
        f"Marque : {v['brand']}\n"
        f"Modèle : {v['model']}\n"
        f"Année : {v['year']}\n"
        f"Couleur : {v['color']}\n"
        f"Places dispo : {v['seats']}\n"
        f"Carburant : {v['fuel']}\n"
        f"Fumeur : {'Oui' if v['smoking'] else 'Non'}\n"
        f"Climatisation : {'Oui' if v['air_conditioning'] else 'Non'}"
    )
    keyboard = [
        [InlineKeyboardButton("✏️ Marque", callback_data="vehicle:edit:brand"), InlineKeyboardButton("✏️ Modèle", callback_data="vehicle:edit:model")],
        [InlineKeyboardButton("✏️ Année", callback_data="vehicle:edit:year"), InlineKeyboardButton("✏️ Couleur", callback_data="vehicle:edit:color")],
        [InlineKeyboardButton("✏️ Places", callback_data="vehicle:edit:seats"), InlineKeyboardButton("✏️ Carburant", callback_data="vehicle:edit:fuel")],
        [InlineKeyboardButton("✏️ Fumeur", callback_data="vehicle:edit:smoking"), InlineKeyboardButton("✏️ Climatisation", callback_data="vehicle:edit:clim")],
        [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(resume, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(resume, reply_markup=InlineKeyboardMarkup(keyboard))
    return VEHICLE_EDIT_FIELD

# Handler pour chaque champ à modifier
async def vehicle_edit_field(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    field = update.callback_query.data.split(":")[-1]
    prompts = {
        "brand": "Nouvelle marque ?",
        "model": "Nouveau modèle ?",
        "year": "Nouvelle année ? (ex: 2022)",
        "color": "Nouvelle couleur ?",
        "seats": "Nouveau nombre de places ? (1-8)",
        "fuel": "Nouveau type de carburant ? (Essence, Diesel, Électrique, Hybride)",
        "smoking": "Véhicule fumeur ? (Oui/Non)",
        "clim": "Climatisation ? (Oui/Non)"
    }
    context.user_data['edit_field'] = field
    # Clavier inline Annuler
    inline_cancel = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annuler", callback_data="vehicle:cancel")]])
    # Propose un clavier si besoin
    if field == "fuel":
        kb = ReplyKeyboardMarkup([[c] for c in FUEL_CHOICES], resize_keyboard=True)
        await update.callback_query.edit_message_text(prompts[field], reply_markup=inline_cancel)
        await update.callback_query.message.reply_text("Choisissez ou tapez le carburant :", reply_markup=kb)
    elif field in ("smoking", "clim"):
        kb = ReplyKeyboardMarkup([[c] for c in OUI_NON], resize_keyboard=True)
        await update.callback_query.edit_message_text(prompts[field], reply_markup=inline_cancel)
        await update.callback_query.message.reply_text("Choisissez ou tapez Oui/Non :", reply_markup=kb)
    else:
        await update.callback_query.edit_message_text(prompts[field], reply_markup=inline_cancel)
    return VEHICLE_EDIT_FIELD

# Handler pour la saisie d'un champ modifié
async def vehicle_edit_input(update: Update, context: CallbackContext):
    field = context.user_data.get('edit_field')
    value = update.message.text.strip()
    user_id = update.effective_user.id
    users = load_users()
    user_entry = users.get(str(user_id), {})
    v = user_entry.get("vehicle", {})
    # Validation par champ
    if field == "brand":
        if not value:
            await update.message.reply_text("Merci d'entrer une marque valide.")
            return VEHICLE_EDIT_FIELD
        v['brand'] = value
    elif field == "model":
        if not value:
            await update.message.reply_text("Merci d'entrer un modèle valide.")
            return VEHICLE_EDIT_FIELD
        v['model'] = value
    elif field == "year":
        if not value.isdigit() or not (1950 <= int(value) <= 2100):
            await update.message.reply_text("Merci d'entrer une année valide (ex: 2022).")
            return VEHICLE_EDIT_FIELD
        v['year'] = int(value)
    elif field == "color":
        if not value:
            await update.message.reply_text("Merci d'entrer une couleur valide.")
            return VEHICLE_EDIT_FIELD
        v['color'] = value
    elif field == "seats":
        if not value.isdigit() or not (1 <= int(value) <= 8):
            await update.message.reply_text("Merci d'entrer un nombre de places valide (1-8).")
            return VEHICLE_EDIT_FIELD
        v['seats'] = int(value)
    elif field == "fuel":
        if value not in FUEL_CHOICES:
            await update.message.reply_text(f"Merci de choisir parmi : {', '.join(FUEL_CHOICES)}.")
            return VEHICLE_EDIT_FIELD
        v['fuel'] = value
    elif field == "smoking":
        if value.lower() not in [x.lower() for x in OUI_NON]:
            await update.message.reply_text("Merci de répondre par Oui ou Non.")
            return VEHICLE_EDIT_FIELD
        v['smoking'] = (value.lower() == "oui")
    elif field == "clim":
        if value.lower() not in [x.lower() for x in OUI_NON]:
            await update.message.reply_text("Merci de répondre par Oui ou Non.")
            return VEHICLE_EDIT_FIELD
        v['air_conditioning'] = (value.lower() == "oui")
    # Sauvegarde
    user_entry["vehicle"] = v
    users[str(user_id)] = user_entry
    save_users(users)
    context.user_data.pop('edit_field', None)
    await update.message.reply_text("✅ Modifié !", reply_markup=ReplyKeyboardRemove())
    # Affiche l'aperçu à jour
    await show_vehicle_summary(update, context)
    return VEHICLE_EDIT_FIELD

# Handler pour retour au profil depuis l'aperçu véhicule
async def back_to_profile_from_vehicle(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await show_profile_dashboard(update, context)
    return ConversationHandler.END

async def cancel_vehicle(update: Update, context: CallbackContext):
    await update.message.reply_text("🚫 Saisie du véhicule annulée.", reply_markup=ReplyKeyboardRemove())
    context.user_data.pop('vehicle', None)
    return ConversationHandler.END

# Ajoute un handler pour l'annulation par bouton inline
async def cancel_vehicle_inline(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🚫 Saisie du véhicule annulée.")
    context.user_data.pop('vehicle', None)
    return ConversationHandler.END

vehicle_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(show_vehicle_summary, pattern="^edit:vehicle$")],
    states={
        VEHICLE_EDIT_FIELD: [
            CallbackQueryHandler(vehicle_edit_field, pattern="^vehicle:edit:(brand|model|year|color|seats|fuel|smoking|clim)$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, vehicle_edit_input),
            CallbackQueryHandler(back_to_profile_from_vehicle, pattern="^profile:back_to_profile$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_vehicle), CallbackQueryHandler(cancel_vehicle_inline, pattern="^vehicle:cancel$")],
    name="vehicle_conversation",
    persistent=True,
    allow_reentry=True
)
