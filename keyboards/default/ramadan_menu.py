from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from core.config import WEBHOOK_HOST

def get_ramadan_menu(region: str = "tashkent", is_admin: bool = False, user_id: int = None) -> ReplyKeyboardMarkup:
    # Build the calendar URL with user_id for subscription check
    calendar_url = f"{WEBHOOK_HOST}/calendar?region={region}"
    if user_id:
        calendar_url += f"&user_id={user_id}"

    keyboard = [
        [
            KeyboardButton(text="📅 Bugungi taqvim"),
            KeyboardButton(text="⏳ Ertangi taqvim"),
        ],
        [
            KeyboardButton(text="🗓 To'liq taqvim", web_app=WebAppInfo(url=calendar_url)),
            KeyboardButton(text="🤲 Ramazon duolari"),
        ],
        [
            KeyboardButton(text="📍 Hududni o'zgartirish"),
        ],
    ]

    
    if is_admin:
        from core.config import BOT_TOKEN
        keyboard.append([KeyboardButton(text="⚙️ Admin Panel", web_app=WebAppInfo(url=f"{WEBHOOK_HOST}/admin-mobile?token={BOT_TOKEN}"))])

        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

