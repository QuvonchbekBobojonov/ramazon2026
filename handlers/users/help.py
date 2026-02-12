from aiogram import types
from aiogram.filters.command import Command

from core.loader import dp

@dp.message(Command("help"))
async def bot_help(message: types.Message):
    text = ("🤖 <b>Ramazon 2026 Boti</b>\n\n"
            "Ushbu bot orqali siz quyidagi qulayliklardan foydalanishingiz mumkin:\n\n"
            "📅 <b>Kunlik taqvim:</b> Bugungi va ertangi saharlik hamda iftorlik vaqtlarini bilib oling.\n"
            "🗓 <b>To'liq taqvim:</b> Ramazon oyining to'liq taqvimini maxsus Web App orqali ko'ring.\n"
            "🤲 <b>Duolar:</b> Saharlik va iftorlik duolarini o'rganing (arabcha, o'qilishi va ma'nosi bilan).\n"
            "📍 <b>Hududiy vaqtlar:</b> O'zbekistonning barcha viloyatlari uchun aniq vaqtlar.\n\n"
            "Buyruqlar:\n"
            "/start - Botni ishga tushirish\n"
            "/help - Yordam")
    
    await message.answer(text)
