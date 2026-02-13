from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from db.base import async_session_maker
from db.crud import add_user
from core.config import ADMINS
from core.loader import bot

class UserRegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        import logging
        user = data.get("event_from_user")
        logging.info(f"Middleware called for user: {user.id if user else 'None'}")
        
        if user and not user.is_bot:


            async with async_session_maker() as session:
                db_user, is_new = await add_user(
                    session, 
                    user.id, 
                    user.full_name, 
                    user.username
                )
                data["db_user"] = db_user
                
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
        
        return await handler(event, data)
