from typing import Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from core.config import CHANNELS
from core.loader import bot

async def check_membership(user_id: int):
    final_status = True
    for channel in CHANNELS:
        try:
            chat_id = channel
            if channel.startswith("http"):
                if "/+" in channel or "/joinchat/" in channel:
                    # Private invite link, bot cannot check membership easily without being in it
                    # Skip check for this channel to avoid errors, or assume success
                    continue
                chat_id = "@" + channel.split("/")[-1]
            
            member = await bot.get_chat_member(user_id=user_id, chat_id=chat_id)
            status = member.status in ["creator", "administrator", "member", "restricted"]
        except Exception as e:
            print(f"Error checking subscription for {user_id} in {channel}: {e}")
            # Fail safe: if error (e.g. bot not admin), assume subscribed to avoid locking info
            status = True

        
        if not status:
            final_status = False
            break
    return final_status

def get_subscription_keyboard():
    keyboard = []
    for channel in CHANNELS:
        if channel.startswith("http"):
            url = channel
        else:
            name = channel.replace("@", "")
            url = f"https://t.me/{name}"
        keyboard.append([InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=url)])
    
    keyboard.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

SUBSCRIPTION_TEXT = (
    "🌙 <b>Assalomu alaykum!</b>\n\n"
    "Ramazon barakotlaridan to'liq bahramand bo'lish uchun homiy kanalimizga obuna bo'ling.\n"
    "Bu bizning loyihamiz rivoji uchun juda muhim! 😊"
)
