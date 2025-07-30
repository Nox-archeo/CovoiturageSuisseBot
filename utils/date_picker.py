#!/usr/bin/env python
# filepath: /Users/margaux/CovoiturageSuisse/utils/date_picker.py
"""
Module de sélection de date et heure pour le bot CovoiturageSuisse.
Implémente un sélecteur interactif de date et d'heure avec des boutons.
"""
import calendar
import logging
import locale
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler

logger = logging.getLogger(__name__)

# Définition des patterns pour les callbacks du calendrier
CALENDAR_NAVIGATION_PATTERN = r"^calendar:(prev|next|month):\d+:\d+$"
CALENDAR_DAY_SELECTION_PATTERN = r"^calendar:day:\d+:\d+:\d+$"
CALENDAR_CANCEL_PATTERN = r"^calendar:cancel$"
TIME_SELECTION_PATTERN = r"^time:\d+:\d+$|^hour:\d+$"
# Pattern pour les options d'horaires flexibles
FLEX_TIME_PATTERN = r"^flex_time:(.+)$"

TIME_BACK_PATTERN = r"^time:back$"
TIME_CANCEL_PATTERN = r"^time:cancel$"

# Configurer le locale pour avoir les noms de mois en français
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR')
    except locale.Error:
        logger.warning("Impossible de configurer le locale français, utilisation du locale par défaut.")

# Noms de jours et mois en français (fallback si locale ne fonctionne pas)
DAYS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
MONTHS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]

def create_date_buttons():
    """Crée des boutons pour la sélection rapide de dates."""
    today = datetime.now().date()
    keyboard = []
    
    # Dates rapides : Aujourd'hui, Demain, Ce week-end
    keyboard.append([
        InlineKeyboardButton("🗓️ Aujourd'hui", callback_data=f"quick_date:{today.strftime('%Y-%m-%d')}"),
        InlineKeyboardButton("📅 Demain", callback_data=f"quick_date:{(today + timedelta(days=1)).strftime('%Y-%m-%d')}")
    ])
    
    # Prochains jours
    next_dates = []
    for i in range(2, 5):  # Jour +2, +3, +4
        date_option = today + timedelta(days=i)
        day_name = DAYS_FR[date_option.weekday()]
        date_text = f"{day_name} {date_option.day}/{date_option.month}"
        next_dates.append(InlineKeyboardButton(
            date_text, 
            callback_data=f"quick_date:{date_option.strftime('%Y-%m-%d')}"
        ))
    
    # Ajouter par paires
    for i in range(0, len(next_dates), 2):
        row = next_dates[i:i+2]
        keyboard.append(row)
    
    # Bouton calendrier complet
    keyboard.append([InlineKeyboardButton("📆 Calendrier complet", callback_data="show_calendar")])
    
    return InlineKeyboardMarkup(keyboard)

def format_date_display(date_obj):
    """Formate une date pour l'affichage."""
    if isinstance(date_obj, str):
        # Si c'est une chaîne, essayer de la parser
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except:
            return date_obj
    
    if hasattr(date_obj, 'date'):
        date_obj = date_obj.date()
    
    today = datetime.now().date()
    
    if date_obj == today:
        return "Aujourd'hui"
    elif date_obj == today + timedelta(days=1):
        return "Demain"
    else:
        day_name = DAYS_FR[date_obj.weekday()]
        return f"{day_name} {date_obj.day}/{date_obj.month}/{date_obj.year}"

def get_calendar_keyboard(year, month):
    """Génère un clavier de calendrier interactif pour le mois spécifié"""
    keyboard = []
    
    # En-tête avec mois et année
    month_name = MONTHS_FR[month-1]
    keyboard.append([
        InlineKeyboardButton("◀️", callback_data=f"calendar:prev:{year}:{month}"),
        InlineKeyboardButton(f"{month_name} {year}", callback_data=f"calendar:month:{year}:{month}"),
        InlineKeyboardButton("▶️", callback_data=f"calendar:next:{year}:{month}")
    ])
    
    # Jours de la semaine
    keyboard.append([InlineKeyboardButton(day, callback_data="calendar:ignore") for day in DAYS_FR])
    
    # Récupérer les jours du mois
    cal = calendar.monthcalendar(year, month)
    today = datetime.now().date()
    
    # Générer les boutons pour chaque jour
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                # Jour vide (hors du mois)
                row.append(InlineKeyboardButton(" ", callback_data="calendar:ignore"))
            else:
                # Vérifier si le jour est dans le passé
                current_date = datetime(year, month, day).date()
                
                if current_date < today:
                    # Jour passé - désactivé
                    row.append(InlineKeyboardButton("✖️", callback_data="calendar:ignore"))
                else:
                    # Jour valide - sélectionnable
                    row.append(InlineKeyboardButton(
                        str(day),
                        callback_data=f"calendar:day:{year}:{month}:{day}"
                    ))
        keyboard.append(row)
    
    # Bouton pour annuler
    keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="calendar:cancel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_time_keyboard(selected_date=None):
    """Renvoie le clavier pour la sélection de l'heure
    
    Args:
        selected_date (datetime, optional): La date sélectionnée. Defaults to None.
    """
    keyboard = []
    
    # Heures standards (0-23)
    for i in range(0, 24, 3):
        row = []
        for h in range(i, min(i+3, 24)):
            hour_str = f"{h:02d}"
            row.append(InlineKeyboardButton(hour_str, callback_data=f"time:{hour_str}"))
        keyboard.append(row)
    
    # Options d'horaires flexibles
    keyboard.append([
        InlineKeyboardButton("🕗 Matinée (6h-12h)", callback_data="flex_time:morning")
    ])
    keyboard.append([
        InlineKeyboardButton("🌇 Après-midi (12h-18h)", callback_data="flex_time:afternoon")
    ])
    keyboard.append([
        InlineKeyboardButton("🌙 Soirée (18h-23h)", callback_data="flex_time:evening")
    ])
    keyboard.append([
        InlineKeyboardButton("⏰ Heure à définir", callback_data="flex_time:tbd")
    ])
    
    # Boutons de navigation
    keyboard.append([
        InlineKeyboardButton("🔙 Retour", callback_data="time:back"),
        InlineKeyboardButton("❌ Annuler", callback_data="time:cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)
def get_minute_keyboard(selected_hour):
    """Génère un clavier pour sélectionner les minutes"""
    keyboard = []
    
    # Générer les minutes par intervalles de 5
    minutes = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    
    # Créer des boutons pour chaque minute (4 par ligne)
    for i in range(0, len(minutes), 4):
        row = []
        for m in minutes[i:i+4]:
            minute_str = f"{m:02d}"
            row.append(InlineKeyboardButton(
                minute_str,
                callback_data=f"minute:{selected_hour}:{m}"
            ))
        keyboard.append(row)
    
    # Bouton pour revenir au sélecteur d'heures
    keyboard.append([
        InlineKeyboardButton("🔙 Retour", callback_data="minute:back"),
        InlineKeyboardButton("❌ Annuler", callback_data="minute:cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_calendar_navigation(update: Update, context: CallbackContext):
    """Gère la navigation dans le calendrier"""
    query = update.callback_query
    await query.answer()
    
    # Extraire les données du callback
    _, action, year, month = query.data.split(':')
    year, month = int(year), int(month)
    
    if action == 'prev':
        # Mois précédent
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
    elif action == 'next':
        # Mois suivant
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
    
    # Mettre à jour le calendrier
    await query.edit_message_text(
        "📅 Sélectionnez une date pour votre trajet:",
        reply_markup=get_calendar_keyboard(year, month)
    )
    return "CALENDAR"

async def handle_day_selection(update: Update, context: CallbackContext):
    """Gère la sélection d'un jour dans le calendrier"""
    query = update.callback_query
    await query.answer()
    
    # Extraire la date sélectionnée
    _, _, year, month, day = query.data.split(':')
    selected_date = datetime(int(year), int(month), int(day))
    
    # Sauvegarder la date dans le contexte
    context.user_data['selected_date'] = selected_date
    
    # Afficher le sélecteur d'heure
    await query.edit_message_text(
        f"🕒 Sélectionnez l'heure pour le {selected_date.strftime('%d %B %Y')}:",
        reply_markup=get_time_keyboard(selected_date)
    )
    return "TIME"

async def handle_time_selection(update: Update, context: CallbackContext):
    """Gère la sélection de l'heure et redirige vers la sélection des minutes"""
    query = update.callback_query
    await query.answer()
    
    # Vérifier s'il s'agit d'une option d'horaire flexible
    if query.data.startswith("flex_time:"):
        return await handle_flex_time_selection(update, context)
    
    # Vérifier si c'est un pattern hour: ou time:
    if query.data.startswith("hour:"):
        # Nouvelle logique pour sélection de l'heure uniquement
        _, hour = query.data.split(':')
        hour = int(hour)
        
        # Stocker temporairement l'heure sélectionnée
        context.user_data['selected_hour'] = hour
        
        # Récupérer la date sélectionnée
        selected_date = context.user_data.get('selected_date')
        if not selected_date:
            logger.error("Date non trouvée dans le contexte")
            await query.edit_message_text(
                "❌ Erreur: La date n'a pas été définie. Veuillez réessayer."
            )
            return "CANCEL"
        
        # Afficher le sélecteur de minutes
        await query.edit_message_text(
            f"⏱️ Sélectionnez les minutes pour {selected_date.strftime('%d %B %Y')} à {hour:02d}h :",
            reply_markup=get_minute_keyboard(hour)
        )
        return "MINUTE"
    
    elif query.data.startswith("time:"):
        # Ancien format pour compatibilité - extraire l'heure et les minutes
        _, hour, minute = query.data.split(':')
        hour, minute = int(hour), int(minute)
        
        # Récupérer la date sélectionnée
        selected_date = context.user_data.get('selected_date')
        if not selected_date:
            logger.error("Date non trouvée dans le contexte")
            await query.edit_message_text(
                "❌ Erreur: La date n'a pas été définie. Veuillez réessayer."
            )
            return "CANCEL"
        
        # Créer l'objet datetime complet
        selected_datetime = selected_date.replace(hour=hour, minute=minute)
        context.user_data['selected_datetime'] = selected_datetime
        
        # Formater pour l'affichage
        formatted_date = selected_datetime.strftime('%d %B %Y à %H:%M')
        
        # Passer directement à l'étape de confirmation
        keyboard = [
            [InlineKeyboardButton("✅ Confirmer", callback_data="datetime:confirm")],
            [InlineKeyboardButton("🔄 Changer", callback_data="datetime:change")],
            [InlineKeyboardButton("❌ Annuler", callback_data="datetime:cancel")]
        ]
        
        await query.edit_message_text(
            f"📅 Date et heure sélectionnées:\n\n"
            f"*{formatted_date}*\n\n"
            f"Confirmer cette sélection?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return "EDIT_CONFIRM_DATETIME"
    
    # Cas imprévu
    logger.error(f"Format de données non reconnu: {query.data}")
    await query.edit_message_text("❌ Erreur: Format d'heure non reconnu.")
    return "CANCEL"

async def handle_minute_selection(update: Update, context: CallbackContext):
    """Gère la sélection des minutes"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("minute:back"):
        # Retour à la sélection de l'heure
        selected_date = context.user_data.get('selected_date')
        if not selected_date:
            logger.error("Date non trouvée dans le contexte")
            return "CANCEL"
        
        await query.edit_message_text(
            f"🕒 Sélectionnez l'heure pour le {selected_date.strftime('%d %B %Y')}:",
            reply_markup=get_time_keyboard(selected_date)
        )
        return "TIME"
    
    elif query.data.startswith("minute:cancel"):
        await query.edit_message_text("❌ Sélection de l'heure annulée.")
        return "CANCEL"
    
    # Extraire l'heure et les minutes
    _, selected_hour, selected_minute = query.data.split(':')
    hour, minute = int(selected_hour), int(selected_minute)
    
    # Récupérer la date sélectionnée
    selected_date = context.user_data.get('selected_date')
    if not selected_date:
        logger.error("Date non trouvée dans le contexte")
        await query.edit_message_text(
            "❌ Erreur: La date n'a pas été définie. Veuillez réessayer."
        )
        return "CANCEL"
    
    # Créer l'objet datetime complet
    selected_datetime = selected_date.replace(hour=hour, minute=minute)
    
    # Vérifier si on sélectionne une date de retour
    selecting_return = context.user_data.get('selecting_return', False)
    if selecting_return:
        context.user_data['return_selected_datetime'] = selected_datetime
        logger.debug(f"[DATE_PICKER] Date de RETOUR stockée: {selected_datetime}")
    else:
        context.user_data['selected_datetime'] = selected_datetime
        logger.debug(f"[DATE_PICKER] Date d'ALLER stockée: {selected_datetime}")
    
    # Formater pour l'affichage
    formatted_date = selected_datetime.strftime('%d %B %Y à %H:%M')
    
    # Afficher l'écran de confirmation
    keyboard = [
        [InlineKeyboardButton("✅ Confirmer", callback_data="datetime:confirm")],
        [InlineKeyboardButton("🔄 Changer", callback_data="datetime:change")],
        [InlineKeyboardButton("❌ Annuler", callback_data="datetime:cancel")]
    ]
    
    await query.edit_message_text(
        f"📅 Date et heure sélectionnées:\n\n"
        f"*{formatted_date}*\n\n"
        f"Confirmer cette sélection?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return "EDIT_CONFIRM_DATETIME"

async def handle_datetime_action(update: Update, context: CallbackContext, next_state=None):
    """Gère les actions après la sélection de date/heure"""
    query = update.callback_query
    await query.answer()
    
    logger.debug(f"handle_datetime_action appelé avec data={query.data}, next_state={next_state}")
    
    _, action = query.data.split(':')
    
    if action == 'confirm':
        # Récupérer la date appropriée selon le contexte
        selecting_return = context.user_data.get('selecting_return', False)
        if selecting_return:
            selected_datetime = context.user_data.get('return_selected_datetime')
            logger.debug(f"[DATE_PICKER] Confirmation date RETOUR: {selected_datetime}")
        else:
            selected_datetime = context.user_data.get('selected_datetime')
            logger.debug(f"[DATE_PICKER] Confirmation date ALLER: {selected_datetime}")
            
        if not selected_datetime:
            logger.error("Date/heure non trouvée dans le contexte")
            await query.edit_message_text("❌ Erreur: Date/heure non définie.")
            return "CANCEL"
        
        # La date a été confirmée - passez à l'étape suivante définie par le paramètre next_state
        logger.info(f"Date confirmée: {selected_datetime}, passage à l'état suivant: {next_state}")
        
        # Si next_state est une fonction, l'appeler
        if callable(next_state):
            logger.info(f"next_state est une fonction: {next_state.__name__}")
            return await next_state(update, context)
        # Sinon, c'est probablement une constante d'état
        else:
            logger.info(f"next_state est une constante: {next_state}")
            # S'assurer que nous retournons bien la valeur, même si elle est None
            return next_state
    
    elif action == 'change':
        # Revenir au sélecteur de calendrier
        now = datetime.now()
        await query.edit_message_text(
            "📅 Sélectionnez une date pour votre trajet:",
            reply_markup=get_calendar_keyboard(now.year, now.month)
        )
        return "CALENDAR"
    
    elif action == 'cancel':
        await query.edit_message_text("❌ Sélection de date annulée.")
        return "CANCEL"
    
    # Cas par défaut
    await query.edit_message_text("❌ Action non reconnue.")
    return "CANCEL"

async def start_date_selection(
    update: Update,
    context: CallbackContext,
    message: str = "Select date:",
    next_state=None,  # Utiliser ce paramètre au lieu de next_state_after_confirm
    calendar_state=None,
    time_state=None,
    minute_state=None,
    datetime_confirm_state=None,
    action_prefix="cal"
):
    """Lance la sélection de date."""
    logger.debug(f"Démarrage date_picker avec context.user_data: {context.user_data}")
    now = datetime.now()
    
    # Message par défaut si non spécifié
    if not message:
        message = "📅 Sélectionnez une date pour votre trajet:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=get_calendar_keyboard(now.year, now.month)
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=get_calendar_keyboard(now.year, now.month)
        )
    
    return "CALENDAR"

# Ne pas définir directement des handlers ici, ils doivent être créés par le module qui les utilise
# Définition des patterns regex pour les handlers
CALENDAR_NAVIGATION_PATTERN = r"^calendar:(prev|next|month):\d+:\d+$"
CALENDAR_DAY_SELECTION_PATTERN = r"^calendar:day:\d+:\d+:\d+$"
CALENDAR_CANCEL_PATTERN = r"^calendar:cancel$"
TIME_SELECTION_PATTERN = r"^time:\d+:\d+$|^hour:\d+$"
TIME_BACK_PATTERN = r"^time:back$"
TIME_CANCEL_PATTERN = r"^time:cancel$"
MINUTE_SELECTION_PATTERN = r"^minute:\d+:\d+$"
MINUTE_BACK_PATTERN = r"^minute:back$"
MINUTE_CANCEL_PATTERN = r"^minute:cancel$"
DATETIME_ACTION_PATTERN = r"^datetime:(confirm|change|cancel)$"

# Documentation pour aider à la création des handlers
"""
Pour utiliser les fonctions de ce module dans un ConversationHandler:

calendar_handlers = {
    "CALENDAR": [
        CallbackQueryHandler(handle_calendar_navigation, pattern=CALENDAR_NAVIGATION_PATTERN),
        CallbackQueryHandler(handle_day_selection, pattern=CALENDAR_DAY_SELECTION_PATTERN),
        CallbackQueryHandler(lambda u, c: "CANCEL", pattern=CALENDAR_CANCEL_PATTERN)
    ],
    "TIME": [
        CallbackQueryHandler(handle_time_selection, pattern=TIME_SELECTION_PATTERN),
        CallbackQueryHandler(lambda u, c: start_date_selection(u, c), pattern=TIME_BACK_PATTERN),
        CallbackQueryHandler(lambda u, c: "CANCEL", pattern=TIME_CANCEL_PATTERN)
    ],
    "MINUTE": [
        CallbackQueryHandler(handle_minute_selection, pattern=MINUTE_SELECTION_PATTERN),
        CallbackQueryHandler(handle_minute_selection, pattern=MINUTE_BACK_PATTERN),
        CallbackQueryHandler(lambda u, c: "CANCEL", pattern=MINUTE_CANCEL_PATTERN)
    ]
}
"""

async def handle_flex_time_selection(update: Update, context: CallbackContext):
    """Gère la sélection d'horaire flexible"""
    query = update.callback_query
    await query.answer()
    
    _, option = query.data.split(":", 1)
    
    time_mapping = {
        "morning": "Dans la matinée (6h-12h)",
        "afternoon": "L'après-midi (12h-18h)",
        "evening": "En soirée (18h-23h)",
        "tbd": "Heure à définir"
    }
    
    # Stocker l'option horaire flexible
    context.user_data['flex_time'] = option
    context.user_data['flex_time_display'] = time_mapping.get(option, "Horaire flexible")
    
    # Créer un datetime factice pour maintenir la compatibilité
    from datetime import datetime
    today = datetime.now().date()
    if option == "morning":
        hour = 9
    elif option == "afternoon":
        hour = 14
    elif option == "evening":
        hour = 20
    else:  # tbd
        hour = 12
    
    # Stocker le datetime flexible
    flex_datetime = datetime.combine(today, datetime.min.time().replace(hour=hour))
    context.user_data['selected_datetime'] = flex_datetime
    context.user_data['is_flex_time'] = True
    
    # Afficher la confirmation
    keyboard = [
        [InlineKeyboardButton("✅ Confirmer", callback_data="datetime:confirm")],
        [InlineKeyboardButton("🔄 Changer", callback_data="datetime:change")],
        [InlineKeyboardButton("❌ Annuler", callback_data="datetime:cancel")]
    ]
    
    await query.edit_message_text(
        f"📅 *Date sélectionnée:* {flex_datetime.strftime('%d/%m/%Y')}\n"
        f"⏰ *Heure:* {context.user_data['flex_time_display']}\n\n"
        "Confirmez-vous cette sélection?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return "EDIT_CONFIRM_DATETIME"
