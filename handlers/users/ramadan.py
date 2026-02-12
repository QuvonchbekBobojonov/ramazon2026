from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.loader import dp
from keyboards.default.ramadan_menu import get_ramadan_menu
from keyboards.inlines.regions import get_regions_keyboard
from utils.ramadan_calculator import get_today_times, get_tomorrow_times, get_daily_times, calculate_time, get_region_offset
from utils.ramadan_data import ramadan_data, ramadan_prayers
from db.base import async_session_maker
from db.crud import get_user, update_user_region

@dp.callback_query(F.data.startswith("region:"))
async def select_region(call: CallbackQuery, state: FSMContext):
    region = call.data.split(":")[1]
    async with async_session_maker() as session:
        await update_user_region(session, call.from_user.id, region)
        
    await state.update_data(region=region)
    await call.message.answer(f"✅ Siz {region.capitalize()} hududini tanladingiz.\n"
                              f"⬇️ Quyidagi menyudan foydalanishingiz mumkin:",
                              reply_markup=get_ramadan_menu(region))
    await call.answer()
    await call.message.delete()

async def get_user_region(user_id: int, state: FSMContext):
    data = await state.get_data()
    region = data.get("region")
    if not region:
        async with async_session_maker() as session:
            user = await get_user(session, user_id)
            if user and user.region:
                region = user.region
                await state.update_data(region=region)
    return region or "tashkent"

@dp.message(F.text == "📅 Bugungi taqvim")
async def today_calendar(message: Message, state: FSMContext):
    region = await get_user_region(message.from_user.id, state)
    times = get_today_times(region)
    
    if times:
        response = (f"📅 <b>Bugungi taqvim ({times['date']})</b>\n\n"
                    f"📍 <b>Hudud:</b> {region.capitalize()}\n"
                    f"🏙 <b>Saharlik:</b> <b>{times['suhoor']}</b>\n"
                    f"🌆 <b>Iftorlik:</b> <b>{times['iftar']}</b>\n")
        if times.get("note"):
            response += f"\n💡 <b>Eslatma:</b> {times['note']}"
    else:
        response = "⚠️ Bugun uchun ma'lumot topilmadi."
    
    await message.answer(response)

@dp.message(F.text == "⏳ Ertangi taqvim")
async def tomorrow_calendar(message: Message, state: FSMContext):
    region = await get_user_region(message.from_user.id, state)
    times = get_tomorrow_times(region)
    
    if times:
        response = (f"⏳ <b>Ertangi taqvim ({times['date']})</b>\n\n"
                    f"📍 <b>Hudud:</b> {region.capitalize()}\n"
                    f"🏙 <b>Saharlik:</b> <b>{times['suhoor']}</b>\n"
                    f"🌆 <b>Iftorlik:</b> <b>{times['iftar']}</b>\n")
        if times.get("note"):
            response += f"\n💡 <b>Eslatma:</b> {times['note']}"
    else:
        response = "⚠️ Ertaga uchun ma'lumot topilmadi."
        
    await message.answer(response)



@dp.message(F.text == "📍 Hududni o'zgartirish")
async def change_region_cmd(message: Message):
    await message.answer("🌍 Iltimos, o'z hududingizni tanlang:", reply_markup=get_regions_keyboard())


@dp.message(F.text == "🤲 Ramazon duolari")
async def ramadan_prayers_handler(message: Message):
    suhoor = ramadan_prayers["suhoor"]
    iftar = ramadan_prayers["iftar"]
    
    response = (f"🏙 <b>Saharlik duosi:</b>\n"
                f"<i>{suhoor['arabic']}</i>\n\n"
                f"<b>O'qilishi:</b> {suhoor['transliteration']}\n\n"
                f"<b>Ma'nosi:</b> {suhoor['translation']}\n\n"
                f"➖➖➖➖➖➖➖➖➖➖\n\n"
                f"🌆 <b>Iftorlik duosi:</b>\n"
                f"<i>{iftar['arabic']}</i>\n\n"
                f"<b>O'qilishi:</b> {iftar['transliteration']}\n\n"
                f"<b>Ma'nosi:</b> {iftar['translation']}")
    
    await message.answer(response)
