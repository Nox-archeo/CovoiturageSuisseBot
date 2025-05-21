"""
Module de création de trajets pour CovoiturageSuisse.
COMPLÈTEMENT DÉSACTIVÉ pour résoudre le problème des boutons.
"""
# Imports originaux conservés pour compatibilité
from .driver_trip_handler import register as register_driver_handlers
from .passenger_trip_handler import register as register_passenger_handlers

def register(application):
    """
    ⚠️ FONCTION COMPLÈTEMENT DÉSACTIVÉE ⚠️
    
    Cette fonction a été désactivée intentionnellement pour résoudre le problème
    des boutons Conducteur/Passager qui ne répondent pas aux clics.
    
    Les handlers de ce module entrent en conflit avec ceux de create_trip_handler.py
    et interceptent les mêmes callbacks.
    
    Résolution appliquée le 17 mai 2025.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("⛔️ Handlers de trip_creation/__init__.py DÉSACTIVÉS intentionnellement")
    logger.warning("⛔️ Cette désactivation est nécessaire pour résoudre le problème des boutons")
    return
    
# L'ancien code est conservé en commentaire pour référence
"""
def original_register(application):
    # On enregistre d'abord le driver handler car c'est le plus prioritaire
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🔍 Enregistrement des handlers de création de trajet")
    
    # Important: enregistrer d'abord le handler driver (trip_type:driver)
    register_driver_handlers(application)
    
    # Puis enregistrer le handler passager (trip_type:passenger)
    register_passenger_handlers(application)
    
    logger.info("✅ Handlers de création de trajet enregistrés")
"""
