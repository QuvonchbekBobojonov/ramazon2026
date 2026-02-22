from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from db.base import async_session_maker
from db.crud import add_user
from core.config import ADMINS
from core.loader import bot

from utils.cache import get_cache, set_cache
from types import SimpleNamespace

class UserRegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        import logging
        user = data.get("event_from_user")
        
        if user and not user.is_bot:
            # Check Redis cache first
            cache_key = f"user:{user.id}"
            cached_user = await get_cache(cache_key)
            
            if cached_user:
                # Convert dict to object-like structure
                db_user = SimpleNamespace(**cached_user)
            else:
                logging.info(f"Redis cache miss for user: {user.id}. Querying DB...")
                async with async_session_maker() as session:
                    db_user, is_new = await add_user(
                        session, 
                        user.id, 
                        user.full_name, 
                        user.username
                    )
                    
                    # Convert SQLAlchemy model to dict for caching
                    user_dict = {
                        "id": db_user.id,
                        "telegram_id": db_user.telegram_id,
                        "full_name": db_user.full_name,
                        "username": db_user.username,
                        "region": db_user.region,
                        "is_subscribed": db_user.is_subscribed,
                        "is_blocked": db_user.is_blocked
                    }
                    
                    # Cache the user data for 1 hour
                    await set_cache(cache_key, user_dict, expire=3600)
                    
                    if is_new:
                        admin_text = (f"👤 <b>Yangi foydalanuvchi!</b>\n\n"
                                      f"🆔 ID: <code>{user.id}</code>\n"
                                      f"👤 Name: {user.full_name}\n"
                                      f"🔗 Username: @{user.username if user.username else 'yoq'}")
                        for admin_id in ADMINS:
                            try:
                                await bot.send_message(admin_id, admin_text)
                            except Exception:
                                pass
            
            data["db_user"] = db_user
        
        return await handler(event, data)
