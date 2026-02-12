from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

ramadan_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📅 Bugungi taqvim"),
            KeyboardButton(text="⏳ Ertangi taqvim"),
        ],
        [
            KeyboardButton(text="🗓 To'liq taqvim"),
        ],
        [
            KeyboardButton(text="📍 Hududni o'zgartirish"),
        ],
    ],
    resize_keyboard=True
)
