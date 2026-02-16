from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from utils.subscription import check_membership, get_subscription_keyboard, SUBSCRIPTION_TEXT
from core.config import ADMINS
from utils.cache import redis_client
import logging

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        
        # Adminlar va botlarni tekshirmaymiz
        if not user or user.is_bot or str(user.id) in ADMINS or user.id in ADMINS:
            return await handler(event, data)

        # Obunani real-time rejimda Telegramdan tekshirish (keshsiz)
        is_subscribed = await check_membership(user.id)
        
        if is_subscribed:
            return await handler(event, data)
        
        # Agar obuna bo'lmagan bo'lsa
        if isinstance(event, Message):
            await event.answer(
                SUBSCRIPTION_TEXT,
                reply_markup=get_subscription_keyboard()
            )
        elif isinstance(event, CallbackQuery):
            if event.data == "check_subs":
                return await handler(event, data)
            
            try:
                await event.answer("Kanalga obuna bo'lishingiz shart!", show_alert=True)
            except Exception:
                pass
            try:
                await event.message.edit_text(
                    SUBSCRIPTION_TEXT,
                    reply_markup=get_subscription_keyboard()
                )
            except Exception:
                pass
        
        return
