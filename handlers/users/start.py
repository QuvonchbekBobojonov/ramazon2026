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
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    Handles /start command, registers user, and checks for region.
    """
    # Check subscription first
    is_subscribed = await check_membership(message.from_user.id)
    if not is_subscribed:
        await message.answer(SUBSCRIPTION_TEXT, reply_markup=get_subscription_keyboard())
        return
    async with async_session_maker() as session:
        user, is_new = await add_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        
        if is_new:
            from core.config import ADMINS
            from core.loader import bot
            admin_text = (f"👤 <b>Yangi foydalanuvchi!</b>\n\n"
                          f"🆔 ID: <code>{message.from_user.id}</code>\n"
                          f"👤 Name: {message.from_user.full_name}\n"
                          f"🔗 Username: @{message.from_user.username if message.from_user.username else 'yoq'}")
            for admin_id in ADMINS:
                try:
                    await bot.send_message(admin_id, admin_text)
                except Exception:
                    pass

        if user.region:

            await state.update_data(region=user.region)
            await message.answer(f"👋 Assalomu alaykum, {message.from_user.full_name}!\n"
                                 f"📍 Sizning hududingiz: {user.region.capitalize()}.\n"
                                 f"⬇️ Quyidagi menyudan foydalanishingiz mumkin:",
                                 reply_markup=get_ramadan_menu(user.region))
        else:
            await message.answer(f"👋 Assalomu alaykum, {message.from_user.full_name}!\n"
                                 f"🌙 Ramazon 2026 botiga xush kelibsiz.\n"
                                 f"🌍 Iltimos, o'z hududingizni tanlang:",
                                 reply_markup=get_regions_keyboard())