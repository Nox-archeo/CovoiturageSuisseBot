from aiogram import Dispatcher, types
from aiogram.dispatcher import filters
from aiogram.dispatcher.filters import Text

async def show_profile(callback_query: types.CallbackQuery):
    # Gestion du bouton "Profil"
    await callback_query.answer()
    # Votre logique pour afficher le profil
    await callback_query.message.edit_text("Voici votre profil. [Suite de la logique]")

async def edit_profile(callback_query: types.CallbackQuery):
    # Gestion du bouton d'édition de profil
    await callback_query.answer()
    # Votre logique pour éditer le profil
    await callback_query.message.edit_text("Vous pouvez maintenant modifier votre profil. [Suite de la logique]")

def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(show_profile, text="profile")
    dp.register_callback_query_handler(edit_profile, text="edit_profile")
    # Assurez-vous que tous les handlers de profil sont enregistrés ici