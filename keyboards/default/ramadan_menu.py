from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from core.config import WEBHOOK_HOST

def get_ramadan_menu(region: str = "tashkent") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Bugungi taqvim"),
                KeyboardButton(text="⏳ Ertangi taqvim"),
            ],
            [
                KeyboardButton(text="🗓 To'liq taqvim", web_app=WebAppInfo(url=f"{WEBHOOK_HOST}/calendar?region={region}")),
            ],
            [
                KeyboardButton(text="📍 Hududni o'zgartirish"),
            ],
        ],
        resize_keyboard=True
    )
