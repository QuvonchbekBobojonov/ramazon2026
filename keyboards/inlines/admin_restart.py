from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def restart_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_restart_notify"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_restart_notify")
        ]
    ])
    return keyboard
