import requests
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from core.loader import dp
from db.base import async_session_maker
from db.crud import add_user
from keyboards.default.ramadan_menu import get_ramadan_menu
from keyboards.inlines.regions import get_regions_keyboard
from utils.subscription import check_membership, get_subscription_keyboard, SUBSCRIPTION_TEXT

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, db_user=None, user=None) -> None:
    """
    Handles /start command, registers user, and checks for region.
    """
    import logging
    # message.from_user might be the bot if called from a callback (call.message)
    # in such cases, we should rely on the passed 'user' or context
    current_user = user or message.from_user
    user_id = current_user.id
    
    logging.info(f"Start handler called. User: {user_id}, db_user: {db_user}")
    
    # If db_user is not passed (e.g. called from subscription.py), try to get it
    if not db_user:
        async with async_session_maker() as session:
            from db.crud import get_user
            db_user = await get_user(session, user_id)

    # Check subscription first
    is_subscribed = await check_membership(user_id)
    if not is_subscribed:
        await message.answer(SUBSCRIPTION_TEXT, reply_markup=get_subscription_keyboard())
        return
        
    if db_user and db_user.region:
        from core.config import ADMINS
        is_admin = str(user_id) in ADMINS or user_id in ADMINS
        
        await state.update_data(region=db_user.region)
        await message.answer(f"🌙 <b>Ramazon 2026 botiga xush kelibsiz!</b>\n\n"
                             f"📍 Hudud: <b>{db_user.region.capitalize()}</b>\n"
                             f"⬇️ Quyidagi menyudan foydalanishingiz mumkin:",
                             reply_markup=get_ramadan_menu(db_user.region, is_admin, user_id=user_id))

    else:
        await message.answer(f"👋 Assalomu alaykum, {current_user.full_name}!\n"
                             f"🌙 Ramazon 2026 botiga xush kelibsiz.\n\n"
                             f"🌍 Iltimos, davom etish uchun <b>o'z hududingizni tanlang:</b>",
                             reply_markup=get_regions_keyboard())

