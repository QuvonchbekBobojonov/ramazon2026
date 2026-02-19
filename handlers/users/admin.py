from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from core.loader import dp, bot
from core.config import ADMINS, WEBHOOK_HOST
from db.base import async_session_maker
from db.crud import get_all_users
import asyncio

@dp.message(Command("admin"))
async def admin_panel_cmd(message: Message):
    user_id = message.from_user.id
    if str(user_id) in ADMINS or user_id in ADMINS:
        from core.config import BOT_TOKEN
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Admin Panelni ochish", web_app=WebAppInfo(url=f"{WEBHOOK_HOST}/admin-mobile?token={BOT_TOKEN}"))]
        ])

        await message.answer("🛠 <b>Admin Panelga xush kelibsiz!</b>\n\n"
                             "Quyidagi tugma orqali boshqaruv panelini ochishingiz mumkin:", 
                             reply_markup=keyboard)
    else:
        # Silently ignore or show error
        pass

@dp.callback_query(F.data == "confirm_restart_notify")
async def confirm_restart(callback: CallbackQuery):
    try:
        await callback.answer("Xabarnomalar yuborilmoqda...")
    except Exception:
        pass
    await callback.message.edit_text("⏳ <b>Foydalanuvchilarga xabar yuborilmoqda...</b>")
    
    async with async_session_maker() as session:
        users = await get_all_users(session)
    
    text = "🚀 <b>Botimiz qayta ishga tushdi!</b> \n\nXatoliklar (bug fix) muvaffaqiyatli bartaraf etildi va bot yanada yaxshi ishlamoqda. \n\nNoqulayliklar uchun uzr so'raymiz. 😊"
    
    count = 0
    for user in users:
        try:
            await bot.send_message(user.telegram_id, text)
            count += 1
            await asyncio.sleep(0.05) # Avoid flood limits
        except Exception:
            pass
            
    await callback.message.edit_text(f"✅ <b>Xabarnoma yuborildi!</b>\n\nJami: {count} ta foydalanuvchiga yuborildi.")

@dp.callback_query(F.data == "cancel_restart_notify")
async def cancel_restart(callback: CallbackQuery):
    try:
        await callback.answer("Bekor qilindi")
    except Exception:
        pass
    await callback.message.edit_text("❌ <b>Xabarnoma yuborish bekor qilindi.</b>")

@dp.message(Command("notify_features"))
async def notify_features_cmd(message: Message):
    user_id = message.from_user.id
    if str(user_id) in ADMINS or user_id in ADMINS:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_query_data="confirm_feature_notify")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_query_data="cancel_restart_notify")]
        ])
        
        await message.answer(
            "📢 <b>Yangi funksiyalar haqida xabar yuborasizmi?</b>\n\n"
            "Matn:\n"
            "✨ <b>Yangi imkoniyatlar!</b>\n\n"
            "Botimizda quyidagi yangilanishlar bo'ldi:\n"
            "🎵 <b>Audio xizmatlar</b> — Endi mp3quran.net rasmiy bazasidan eng mashhur qorilarning qiroatlarini tinglashingiz mumkin!\n"
            "❓ <b>Savol-javob (Fatvo)</b> — Ramazon oyiga oid barcha rasmiy fatvo va savollarga javoblar bo'limi yangilandi.\n\n"
            "Foydalanish uchun menyudagi tugmalarni bosing. 😊",
            reply_markup=keyboard
        )

@dp.callback_query(F.data == "confirm_feature_notify")
async def confirm_feature_notify(callback: CallbackQuery):
    try:
        await callback.answer("Yuborilmoqda...")
    except Exception:
        pass
    
    await callback.message.edit_text("⏳ <b>Yangi funksiyalar haqida xabar yuborilmoqda...</b>")
    
    async with async_session_maker() as session:
        users = await get_all_users(session)
    
    text = (
        "✨ <b>Yangi imkoniyatlar!</b>\n\n"
        "Botimizda quyidagi yangilanishlar bo'ldi:\n\n"
        "🎵 <b>Audio xizmatlar</b> — Endi mp3quran.net rasmiy bazasidan dunyoning eng mashhur qorilarining (Mishary Rashid, AbdulBaset va b.) go'zal qiroatlarini tinglashingiz mumkin!\n\n"
        "❓ <b>Savol-javob (Fatvo)</b> — Ramazon va ro'zaga oid eng ko'p beriladigan savollarga rasmiy fatvolar bo'limi yangilandi.\n\n"
        "Foydalanish uchun menyudagi tugmalardan foydalaning. 😊"
    )
    
    count = 0
    for user in users:
        try:
            await bot.send_message(user.telegram_id, text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
            
    await callback.message.edit_text(f"✅ <b>Xabarnoma yuborildi!</b>\n\nJami: {count} ta foydalanuvchiga yuborildi.")
