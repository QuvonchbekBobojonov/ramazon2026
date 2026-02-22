from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from utils.subscription import check_membership, get_subscription_keyboard, SUBSCRIPTION_TEXT
from core.config import ADMINS
from db.base import async_session_maker
from db.crud import update_user_subscription
import logging

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        db_user = data.get("db_user")
        
        # Adminlar va botlarni tekshirmaymiz
        if not user or user.is_bot or str(user.id) in ADMINS or user.id in ADMINS:
            return await handler(event, data)

        is_subscribed = db_user.is_subscribed if db_user else False
        is_start_command = isinstance(event, Message) and event.text and event.text.startswith("/start")

        # Agar bazada obuna bo'lmagan bo'lsa yoki /start bosgan bo'lsa, qayta tekshiramiz
        if not is_subscribed or is_start_command:
            import time
            start_time = time.time()
            
            is_subscribed = await check_membership(user.id)
            
            check_duration = time.time() - start_time
            if check_duration > 2:
                logging.warning(f"Slow subscription check for {user.id}: {check_duration:.2f}s")
            
            # Bazani yangilash
            if db_user and db_user.is_subscribed != is_subscribed:
                db_start = time.time()
                async with async_session_maker() as session:
                    await update_user_subscription(session, user.id, is_subscribed)
                    db_user.is_subscribed = is_subscribed # Update in-memory for current request
                
                db_duration = time.time() - db_start
                if db_duration > 2:
                    logging.warning(f"Slow DB update for user {user.id}: {db_duration:.2f}s")
        
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
