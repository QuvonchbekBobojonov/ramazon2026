from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from core.config import CHANNELS
from core.loader import bot

class CheckSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Only check for Messages and CallbackQueries
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)
            
        user_id = event.from_user.id
        
        # Check if callback is for checking subscription
        if isinstance(event, CallbackQuery) and event.data == "check_subs":
            await event.answer()
            # We don't return here, we proceed to check status below
            
        final_status = True
        for channel in CHANNELS:
            status = await self.check(user_id, channel)
            if not status:
                final_status = False
                break
        
        if not final_status:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{channel.replace('@', '')}")],
                [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")]
            ])
            
            text = ("🌙 <b>Assalomu alaykum!</b>\n\n"
                    "Ramazon barakotlaridan to'liq bahramand bo'lish uchun homiy kanalimizga obuna bo'ling.\n"
                    "Bu bizning loyihamiz rivoji uchun juda muhim! 😊")
            
            if isinstance(event, Message):
                await event.answer(text, reply_markup=keyboard)
            elif isinstance(event, CallbackQuery):
                # If checking via button, update message or alert
                if event.data == "check_subs":
                     await event.message.edit_text(text, reply_markup=keyboard)
                else:
                     await event.message.answer(text, reply_markup=keyboard)
            
            return # Stop propagation
            
        # If subscribed, and it was a check click, delete the check message
        if isinstance(event, CallbackQuery) and event.data == "check_subs":
             await event.message.delete()
             await event.message.answer("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.")
             # We might not want to call handler here as the original event was just a button click
             return 

        return await handler(event, data)

    async def check(self, user_id, channel):
        try:
            member = await bot.get_chat_member(user_id=user_id, chat_id=channel)
            return member.status in ["creator", "administrator", "member"]
        except Exception as e:
            print(f"Error checking subscription for {user_id} in {channel}: {e}")
            # If bot is not admin or channel is private/invalid, assume subscribed to avoid blocking everyone
            return False 
