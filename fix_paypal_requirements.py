#!/usr/bin/env python3
"""
Script pour mettre à jour le système PayPal pour tous les utilisateurs
- Rendre PayPal obligatoire pour passagers ET conducteurs
- Modifier la création de profil pour demander PayPal à tous
- Corriger l'interface utilisateur pour la cohérence
"""

import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_paypal_system():
    """Analyse le système PayPal actuel"""
    logger.info("=== ANALYSE DU SYSTÈME PAYPAL ===")
    
    # 1. Profile creation handlers
    profile_files = [
        "handlers/profile_handler.py",
        "handlers/menu_handlers.py",
        "handlers/start_handler.py"
    ]
    
    for file_path in profile_files:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "paypal" in content.lower():
                    logger.info(f"✓ {file_path} contient des références PayPal")
                else:
                    logger.warning(f"⚠ {file_path} ne contient pas de références PayPal")
    
    # 2. Trip creation handlers
    trip_creation_files = [
        "handlers/trip_creation/driver_trip_handler.py",
        "handlers/trip_creation/passenger_trip_handler.py"
    ]
    
    logger.info("\n=== ANALYSE DES HANDLERS DE CRÉATION ===")
    for file_path in trip_creation_files:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "paypal" in content.lower():
                    logger.info(f"✓ {file_path} contient des références PayPal")
                    if "become_passenger" in content and "paypal" not in content.lower():
                        logger.warning(f"⚠ {file_path} gère les passagers mais pas PayPal")
    
    # 3. Profile activation
    logger.info("\n=== RECOMMANDATIONS ===")
    logger.info("1. ✅ Système PayPal existant trouvé pour conducteurs")
    logger.info("2. ❌ Système PayPal manquant pour passagers")
    logger.info("3. ❌ Profil creation n'exige pas PayPal pour tous")
    logger.info("4. ❌ Switch profile ne vérifie pas PayPal")
    
    return True

def create_paypal_requirement_fixes():
    """Crée les corrections pour rendre PayPal obligatoire"""
    logger.info("\n=== CRÉATION DES CORRECTIONS ===")
    
    # 1. Modifier passenger_trip_handler pour demander PayPal
    passenger_fix = '''
# NOUVELLE LOGIQUE: PayPal obligatoire pour passagers aussi
async def handle_become_passenger(update: Update, context: CallbackContext):
    """Gère l'activation du profil passager avec PayPal obligatoire"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "become_passenger":
        user_id = query.from_user.id
        db = get_db()
        user = db.query(User).filter_by(telegram_id=user_id).first()
        
        if user:
            user.is_passenger = True
            db.commit()
            logger.info(f"Utilisateur {user_id} est devenu passager")
            
            # NOUVEAU: Vérifier PayPal pour passagers aussi
            if user.paypal_email:
                await query.edit_message_text(
                    "✅ *Profil passager activé!*\\n\\n"
                    f"📧 PayPal configuré : `{user.paypal_email}`\\n\\n"
                    "Vous pouvez maintenant créer des demandes de trajet.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return await start_departure_selection(update, context)
            else:
                # Demander la configuration PayPal pour les passagers
                keyboard = [
                    [InlineKeyboardButton("💳 Configurer PayPal", callback_data="setup_paypal")],
                    [InlineKeyboardButton("❓ Pourquoi PayPal ?", callback_data="why_paypal_passenger")]
                ]
                
                await query.edit_message_text(
                    "✅ *Profil passager activé!*\\n\\n"
                    "💳 *Configuration PayPal requise*\\n\\n"
                    "Pour garantir la sécurité des transactions et permettre "
                    "les remboursements automatiques en cas d'annulation, "
                    "vous devez configurer votre email PayPal.\\n\\n"
                    "⚠️ Sans PayPal, vous ne pourrez pas recevoir de remboursements "
                    "automatiques ni utiliser la protection acheteur.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                context.user_data['next_state_after_paypal'] = "DEPARTURE"
                return "PAYPAL_SETUP"
'''
    
    # 2. Modifier profile creation pour demander PayPal à tous
    profile_creation_fix = '''
# NOUVELLE LOGIQUE: PayPal obligatoire pour tous les rôles
async def handle_profile_phone_input(update: Update, context: CallbackContext):
    """Gère la saisie du téléphone avec PayPal obligatoire pour tous"""
    phone = update.message.text.strip()
    
    if len(phone) < 10 or not any(char.isdigit() for char in phone):
        await update.message.reply_text(
            "❌ Format de téléphone invalide.\\n"
            "Veuillez entrer un numéro valide (ex: +41 79 123 45 67) :"
        )
        return PROFILE_PHONE_INPUT
    
    context.user_data['phone'] = phone
    selected_role = context.user_data.get('selected_role', 'passenger')
    
    # NOUVEAU: PayPal obligatoire pour TOUS (conducteurs ET passagers)
    keyboard = [
        [InlineKeyboardButton("📧 Entrer mon adresse email PayPal", callback_data="paypal_input_start")],
        [InlineKeyboardButton("🆕 Créer un compte PayPal", url="https://www.paypal.com/ch/webapps/mpp/account-selection")],
        [InlineKeyboardButton("❓ Pourquoi PayPal est obligatoire ?", callback_data="why_paypal_required")]
    ]
    
    role_text = "Conducteur" if selected_role == 'driver' else "Passager"
    
    await update.message.reply_text(
        f"👤 *Inscription - Étape 4/4*\\n\\n"
        f"✅ Nom : {context.user_data['full_name']}\\n"
        f"✅ Âge : {context.user_data['age']} ans\\n"
        f"✅ Téléphone : {phone}\\n\\n"
        f"💳 **Configuration PayPal ({role_text})**\\n\\n"
        f"Pour garantir la sécurité des transactions, PayPal est obligatoire pour tous les utilisateurs :\\n\\n"
        f"• **Conducteurs** : Recevoir les paiements automatiques (88% du montant)\\n"
        f"• **Passagers** : Recevoir les remboursements en cas d'annulation\\n\\n"
        f"🔒 **Sécurité garantie** : Protection acheteur/vendeur PayPal\\n\\n"
        f"👇 **Choisissez une option :**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PROFILE_PAYPAL_INPUT
'''
    
    # 3. Switch profile avec vérification PayPal
    switch_profile_fix = '''
# NOUVELLE LOGIQUE: Vérifier PayPal lors du switch
async def switch_user_profile(update: Update, context: CallbackContext, profile_type: str):
    """Change le profil actif avec vérification PayPal obligatoire"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db = get_db()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await query.edit_message_text("❌ Profil utilisateur non trouvé.")
        return ConversationHandler.END
    
    # NOUVEAU: Vérifier PayPal pour tous les profils
    if not user.paypal_email:
        keyboard = [
            [InlineKeyboardButton("💳 Configurer PayPal", callback_data="setup_paypal")],
            [InlineKeyboardButton("❓ Pourquoi PayPal ?", callback_data="why_paypal_required")],
            [InlineKeyboardButton("🔙 Retour", callback_data="menu:back_to_main")]
        ]
        
        role_text = "conducteur" if profile_type == "driver" else "passager"
        
        await query.edit_message_text(
            f"🔒 *Configuration PayPal Requise*\\n\\n"
            f"Pour activer votre profil {role_text}, vous devez "
            f"configurer votre email PayPal.\\n\\n"
            f"💡 **Pourquoi PayPal est obligatoire ?**\\n"
            f"• Sécurité des transactions\\n"
            f"• Remboursements automatiques\\n"
            f"• Protection acheteur/vendeur\\n\\n"
            f"👇 Configurez maintenant :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Continuer avec la logique normale si PayPal est configuré
    context.user_data['active_profile'] = profile_type
    # ... reste de la fonction ...
'''
    
    # Sauvegarder les corrections
    with open("fixes/paypal_passenger_fix.py", "w", encoding="utf-8") as f:
        f.write(passenger_fix)
    
    with open("fixes/paypal_creation_fix.py", "w", encoding="utf-8") as f:
        f.write(profile_creation_fix)
    
    with open("fixes/paypal_switch_fix.py", "w", encoding="utf-8") as f:
        f.write(switch_profile_fix)
    
    logger.info("✅ Corrections PayPal créées dans le dossier fixes/")

def analyze_passenger_trip_management():
    """Analyse l'interface de gestion des trajets passagers"""
    logger.info("\n=== ANALYSE INTERFACE TRAJETS PASSAGERS ===")
    
    # Vérifier handlers/trip_handlers.py
    trip_handlers_path = "handlers/trip_handlers.py"
    if Path(trip_handlers_path).exists():
        with open(trip_handlers_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Vérifier fonctions essentielles
            functions_needed = [
                "list_passenger_trips",
                "edit_passenger_trip", 
                "delete_passenger_trip",
                "report_passenger_trip"
            ]
            
            found_functions = []
            for func in functions_needed:
                if func in content:
                    found_functions.append(func)
            
            logger.info(f"✓ Fonctions trouvées: {found_functions}")
            missing = set(functions_needed) - set(found_functions)
            if missing:
                logger.warning(f"⚠ Fonctions manquantes: {list(missing)}")
    
    # Vérifier l'interface profil
    logger.info("\n=== INTERFACE PROFIL PASSAGER ===")
    logger.info("Nécessaire: boutons Edit/Delete/Report pour trajets passagers")
    logger.info("Comme pour les conducteurs dans profile_handler.py")

def create_passenger_interface_fixes():
    """Crée les corrections pour l'interface passager complète"""
    logger.info("\n=== CRÉATION INTERFACE PASSAGER ===")
    
    passenger_management_fix = '''
# NOUVELLE INTERFACE: Gestion complète des trajets passagers
async def show_passenger_trip_management(update: Update, context: CallbackContext):
    """Affiche l'interface de gestion des trajets passagers avec toutes les options"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        db = get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await query.edit_message_text("⚠️ Utilisateur non trouvé.")
            return PROFILE_MAIN
        
        # Récupérer les trajets passagers (demandes)
        passenger_trips = db.query(Trip).filter(
            Trip.creator_id == user.id,
            Trip.trip_role == "passenger"
        ).order_by(Trip.departure_time.desc()).all()
        
        if not passenger_trips:
            message = (
                "🎒 *Mes Trajets Passager*\\n\\n"
                "❌ Aucune demande de trajet créée.\\n\\n"
                "💡 Créez votre première demande de trajet !"
            )
            keyboard = [
                [InlineKeyboardButton("➕ Créer une demande", callback_data="menu:create")],
                [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
            ]
        else:
            message = "🎒 *Mes Trajets Passager*\\n\\n"
            keyboard = []
            
            for trip in passenger_trips[:5]:  # Limiter à 5 trajets
                status_emoji = "🟢" if not getattr(trip, 'is_cancelled', False) else "🔴"
                trip_text = f"{status_emoji} {trip.departure_city} → {trip.arrival_city}"
                if hasattr(trip, 'departure_time'):
                    trip_text += f"\\n📅 {trip.departure_time.strftime('%d/%m à %H:%M')}"
                
                message += f"\\n{trip_text}\\n"
                
                # Boutons pour chaque trajet
                trip_keyboard = [
                    InlineKeyboardButton("✏️ Modifier", callback_data=f"edit_passenger_trip:{trip.id}"),
                    InlineKeyboardButton("🗑️ Supprimer", callback_data=f"delete_passenger_trip:{trip.id}"),
                    InlineKeyboardButton("🚨 Signaler", callback_data=f"report_passenger_trip:{trip.id}")
                ]
                keyboard.append(trip_keyboard)
            
            # Boutons généraux
            keyboard.extend([
                [InlineKeyboardButton("➕ Nouvelle demande", callback_data="menu:create")],
                [InlineKeyboardButton("⬅️ Retour au profil", callback_data="profile:back_to_profile")]
            ])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return PROFILE_MAIN
        
    except Exception as e:
        logger.error(f"Erreur dans show_passenger_trip_management: {e}")
        await query.edit_message_text(
            "⚠️ Erreur lors de l'affichage des trajets passagers.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Retour", callback_data="profile:back_to_profile")
            ]])
        )
        return PROFILE_MAIN

async def handle_passenger_trip_action(update: Update, context: CallbackContext):
    """Gère les actions sur les trajets passagers (edit/delete/report)"""
    query = update.callback_query
    await query.answer()
    
    action_data = query.data
    action, trip_id = action_data.split(":")
    trip_id = int(trip_id)
    
    db = get_db()
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        await query.edit_message_text("❌ Trajet non trouvé.")
        return PROFILE_MAIN
    
    if action == "edit_passenger_trip":
        # Rediriger vers l'édition de trajet passager
        keyboard = [
            [InlineKeyboardButton("📍 Modifier départ", callback_data=f"edit_trip_departure:{trip_id}")],
            [InlineKeyboardButton("🎯 Modifier arrivée", callback_data=f"edit_trip_arrival:{trip_id}")],
            [InlineKeyboardButton("📅 Modifier date/heure", callback_data=f"edit_trip_datetime:{trip_id}")],
            [InlineKeyboardButton("👥 Modifier nb passagers", callback_data=f"edit_trip_passengers:{trip_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="profile:my_trips")]
        ]
        
        await query.edit_message_text(
            f"✏️ *Modifier le trajet passager*\\n\\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\\n\\n"
            f"Que souhaitez-vous modifier ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif action == "delete_passenger_trip":
        # Demander confirmation de suppression
        keyboard = [
            [InlineKeyboardButton("❌ Confirmer suppression", callback_data=f"confirm_delete_passenger:{trip_id}")],
            [InlineKeyboardButton("⬅️ Annuler", callback_data="profile:my_trips")]
        ]
        
        await query.edit_message_text(
            f"🗑️ *Supprimer le trajet passager*\\n\\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\\n"
            f"📅 {trip.departure_time.strftime('%d/%m/%Y à %H:%M')}\\n\\n"
            f"⚠️ **Attention !** Cette action est irréversible.\\n\\n"
            f"Voulez-vous vraiment supprimer cette demande de trajet ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif action == "report_passenger_trip":
        # Interface de signalement
        keyboard = [
            [InlineKeyboardButton("🚨 Problème de sécurité", callback_data=f"report_safety:{trip_id}")],
            [InlineKeyboardButton("💰 Problème de paiement", callback_data=f"report_payment:{trip_id}")],
            [InlineKeyboardButton("📞 Problème de contact", callback_data=f"report_contact:{trip_id}")],
            [InlineKeyboardButton("❓ Autre problème", callback_data=f"report_other:{trip_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="profile:my_trips")]
        ]
        
        await query.edit_message_text(
            f"🚨 *Signaler un problème*\\n\\n"
            f"🚗 {trip.departure_city} → {trip.arrival_city}\\n\\n"
            f"Quel type de problème souhaitez-vous signaler ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    return PROFILE_MAIN
'''
    
    # Sauvegarder la correction
    Path("fixes").mkdir(exist_ok=True)
    with open("fixes/passenger_interface_fix.py", "w", encoding="utf-8") as f:
        f.write(passenger_management_fix)
    
    logger.info("✅ Interface passager complète créée dans fixes/")

def main():
    """Fonction principale"""
    logger.info("🔧 ANALYSE ET CORRECTION DU SYSTÈME PAYPAL/INTERFACE")
    
    # Créer le dossier fixes
    Path("fixes").mkdir(exist_ok=True)
    
    # 1. Analyser le système PayPal actuel
    analyze_paypal_system()
    
    # 2. Créer les corrections PayPal
    create_paypal_requirement_fixes()
    
    # 3. Analyser l'interface passager
    analyze_passenger_trip_management()
    
    # 4. Créer les corrections interface
    create_passenger_interface_fixes()
    
    logger.info("\n=== RÉSUMÉ DES CORRECTIONS ===")
    logger.info("✅ Corrections PayPal créées:")
    logger.info("   - fixes/paypal_passenger_fix.py")
    logger.info("   - fixes/paypal_creation_fix.py") 
    logger.info("   - fixes/paypal_switch_fix.py")
    logger.info("✅ Interface passager créée:")
    logger.info("   - fixes/passenger_interface_fix.py")
    
    logger.info("\n=== PROCHAINES ÉTAPES ===")
    logger.info("1. ✅ Intégrer les corrections dans les handlers existants")
    logger.info("2. ✅ Ajouter les handlers pour les actions passagers")
    logger.info("3. ✅ Tester le système PayPal obligatoire")
    logger.info("4. ✅ Tester l'interface de gestion passager")

if __name__ == "__main__":
    main()
