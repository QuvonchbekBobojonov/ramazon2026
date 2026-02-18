import asyncio
import logging
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from core.loader import bot
from db.base import async_session_maker
from db.crud import get_all_users
from utils.ramadan_calculator import get_today_times
from utils.ramadan_data import ramadan_prayers

logger = logging.getLogger(__name__)

async def send_daily_notifications():
    async with async_session_maker() as session:
        users = await get_all_users(session)
    
    count = 0
    for user in users:
        if user.is_blocked:
            continue
        region = user.region or "tashkent"
        times = get_today_times(region)
        
        if not times:
            continue
            
        suhoor_prayers = ramadan_prayers["suhoor"]
        iftar_prayers = ramadan_prayers["iftar"]
        
        text = (f"🌙 <b>Ramazon taqvimi - {times['date']}</b>\n\n"
                f"📍 Hudud: <b>{region.capitalize()}</b>\n"
                f"🏙 Saharlik (Og'iz yopish): <b>{times['suhoor']}</b>\n"
                f"🌆 Iftorlik (Og'iz ochish): <b>{times['iftar']}</b>\n\n"
                f"🤲 <b>Saharlik duosi:</b>\n"
                f"<i>{suhoor_prayers['arabic']}</i>\n\n"
                f"🤲 <b>Iftorlik duosi:</b>\n"
                f"<i>{iftar_prayers['arabic']}</i>\n\n"
                f"Ramazon oyi barchamizga muborak bo'lsin! ✨")
        
        try:
            await bot.send_message(user.telegram_id, text)
            count += 1
            # Avoid hitting Telegram rate limits
            await asyncio.sleep(0.05)
        except TelegramForbiddenError:
            logger.warning(f"User {user.telegram_id} blocked the bot.")
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            await bot.send_message(user.telegram_id, text)
            count += 1
        except Exception as e:
            logger.error(f"Error sending notification to {user.telegram_id}: {e}")
            
    return count
