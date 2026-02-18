from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, WebAppInfo
from aiogram.fsm.context import FSMContext

from core.loader import dp, bot
from core.config import WEBHOOK_HOST
from db.base import async_session_maker
from db.crud import add_user
from keyboards.default.ramadan_menu import get_ramadan_menu
from keyboards.inlines.regions import get_regions_keyboard
from utils.subscription import check_membership, get_subscription_keyboard, SUBSCRIPTION_TEXT

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, command: CommandObject = None, db_user=None, user=None) -> None:
    """
    Handles /start command, registers user, and checks for region.
    """
    args = command.args if command else None
    if args == "prayers":
        # If user came from the deep link, send them the WebApp invitation directly
        prayers_url = f"{WEBHOOK_HOST}/prayers?user_id={message.from_user.id}"
        await message.answer(
            "✨ <b>Duo Devoriga xush kelibsiz!</b>\n\n"
            "Pastdagi tugmani bosib niyatlar devorini ochishingiz mumkin:",
            reply_markup=get_ramadan_menu() # Default menu or custom one
        )
        # We can also use an inline button for a cleaner look
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Duo Devorini ochish", web_app=WebAppInfo(url=prayers_url))]
        ])
        await message.answer("Darchani ochish uchun bosing:", reply_markup=inline_kb)
        return
    import logging
    # message.from_user might be the bot if called from a callback (call.message)
    # in such cases, we should rely on the passed 'user' or context
    current_user = user or message.from_user
    user_id = current_user.id
    
    logging.info(f"Start handler called. User: {user_id}, db_user: {db_user}")
    
    # If db_user is not passed (e.g. called from subscription.py), try to get it
    if not db_user:
        async with async_session_maker() as session:
            from db.crud import get_user, update_user_blocked
            db_user = await get_user(session, user_id)
            
            # If user exists and was blocked, unblock them now
            if db_user and db_user.is_blocked:
                await update_user_blocked(session, user_id, False)
                db_user.is_blocked = False

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

