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

        # Redis keshini tekshirish
        cache_key = f"user_sub:{user.id}"
        is_subscribed = None
        
        if redis_client:
            try:
                # Upstash-redis returns bytes or string depending on version/client
                cached_val = redis_client.get(cache_key)
                if cached_val is not None:
                    is_subscribed = str(cached_val) == "1"
            except Exception as e:
                logging.error(f"Redis cache read error: {e}")

        if is_subscribed is None:
            # Obunani Telegramdan tekshirish
            is_subscribed = await check_membership(user.id)
            
            # Keshga saqlash (masalan, 10 minutga)
            if redis_client:
                try:
                    redis_client.set(cache_key, "1" if is_subscribed else "0", ex=600)
                except Exception as e:
                    logging.error(f"Redis cache write error: {e}")
        
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
            
            await event.answer("Kanalga obuna bo'lishingiz shart!", show_alert=True)
            try:
                await event.message.edit_text(
                    SUBSCRIPTION_TEXT,
                    reply_markup=get_subscription_keyboard()
                )
            except Exception:
                pass
        
        return
