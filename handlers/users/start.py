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
async def command_start_handler(message: Message, state: FSMContext, db_user=None) -> None:
    """
    Handles /start command, registers user, and checks for region.
    """
    import logging
    logging.info(f"Start handler called. User: {message.from_user.id}, db_user: {db_user}")
    if db_user:
        logging.info(f"db_user region: {db_user.region}")

    # Check subscription first
    is_subscribed = await check_membership(message.from_user.id)
    if not is_subscribed:
        await message.answer(SUBSCRIPTION_TEXT, reply_markup=get_subscription_keyboard())
        return
        
    if db_user and db_user.region:
        from core.config import ADMINS
        user_id = message.from_user.id
        is_admin = str(user_id) in ADMINS or user_id in ADMINS
        
        await state.update_data(region=db_user.region)
        await message.answer(f"🌙 <b>Ramazon 2026 botiga xush kelibsiz!</b>\n\n"
                             f"📍 Hudud: <b>{db_user.region.capitalize()}</b>\n"
                             f"⬇️ Quyidagi menyudan foydalanishingiz mumkin:",
                             reply_markup=get_ramadan_menu(db_user.region, is_admin))

    else:
        await message.answer(f"👋 Assalomu alaykum, {message.from_user.full_name}!\n"
                             f"🌙 Ramazon 2026 botiga xush kelibsiz.\n\n"
                             f"🌍 Iltimos, davom etish uchun <b>o'z hududingizni tanlang:</b>",
                             reply_markup=get_regions_keyboard())

