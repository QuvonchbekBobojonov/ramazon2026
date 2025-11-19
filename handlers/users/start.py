from datetime import datetime

import requests

from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from core.loader import dp


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Handles /start command and shows days left until Ramadan
    """
    response = requests.get("https://ramadan.munafio.com/api/check")
    data = response.json()['data']

    next_ramadan_date = data['nextRamadan']['date']
    next_ramadan = datetime.strptime(next_ramadan_date, "%d-%m-%Y").date()

    today = datetime.today().date()
    days_left = (next_ramadan - today).days

    next_ramadan_formatted = next_ramadan.strftime("%d %B %Y")
    months_uz = {
        "January": "Yanvar", "February": "Fevral", "March": "Mart", "April": "Aprel",
        "May": "May", "June": "Iyun", "July": "Iyul", "August": "Avgust",
        "September": "Sentyabr", "October": "Oktyabr", "November": "Noyabr", "December": "Dekabr"
    }
    month_eng = next_ramadan.strftime("%B")
    next_ramadan_uz = next_ramadan.strftime(f"%d {months_uz[month_eng]} %Y")

    if days_left <= 0:
        text = f"🕌 Bugun Ramazon boshlanadi! Asaalomu alaykum, {hbold(message.from_user.full_name)}!"
    else:
        text = (
            f"<b>Asaalomu alaykum, {message.from_user.full_name}!</b>\n\n"
            f"🌙 <b>Keyingi Ramazon boshlanish sanasi:</b> <i>{next_ramadan_uz}</i>\n"
            f"⏳ <b>Ramazon boshlanishigacha qolgan kunlar:</b> <i>{days_left} kun</i>\n\n"
            f"<i>Barcha ma'lumotlar <a href='https://ramadan.munafio.com/'>munafio.com</a> saytidan olinmoqda.</i>"
        )

    await message.answer(text)