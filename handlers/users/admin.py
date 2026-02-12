from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from core.loader import dp
from core.config import ADMINS, WEBHOOK_HOST

@dp.message(Command("admin"))
async def admin_panel_cmd(message: Message):
    user_id = message.from_user.id
    if str(user_id) in ADMINS or user_id in ADMINS:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Admin Panelni ochish", web_app=WebAppInfo(url=f"{WEBHOOK_HOST}/admin"))]
        ])
        await message.answer("🛠 <b>Admin Panelga xush kelibsiz!</b>\n\n"
                             "Quyidagi tugma orqali boshqaruv panelini ochishingiz mumkin:", 
                             reply_markup=keyboard)
    else:
        # Silently ignore or show error
        pass
