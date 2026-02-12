from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from core.config import WEBHOOK_HOST

def get_ramadan_menu(region: str = "tashkent", is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="📅 Bugungi taqvim"),
            KeyboardButton(text="⏳ Ertangi taqvim"),
        ],
        [
            KeyboardButton(text="🗓 To'liq taqvim", web_app=WebAppInfo(url=f"{WEBHOOK_HOST}/calendar?region={region}")),
            KeyboardButton(text="🤲 Ramazon duolari"),
        ],
        [
            KeyboardButton(text="📍 Hududni o'zgartirish"),
        ],
    ]
    
    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin Panel", web_app=WebAppInfo(url=f"{WEBHOOK_HOST}/admin"))])
        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

