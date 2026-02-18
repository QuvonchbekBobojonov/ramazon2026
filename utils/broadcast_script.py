import asyncio
import logging
import sys
import os

# Add the project root to sys.path to allow imports
sys.path.append(os.getcwd())

from core.loader import bot
from db.base import async_session_maker
from db.crud import get_all_users, update_user_blocked
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_broadcast():
    async with async_session_maker() as session:
        users = await get_all_users(session)
    
    print(f"Barcha {len(users)} ta foydalanuvchiga xabar yuborish boshlanmoqda...")
    
    gif_path = "static/ramadan.gif"
    if not os.path.exists(gif_path):
        print(f"Xatolik: {gif_path} topilmadi!")
        return

    gif_file = FSInputFile(gif_path)
    gif_id = None
    
    caption = (
        "<b>Assalomu alaykum va rahmatullohi va barokatuh!</b>\n\n"
        "Barchangizni kirib kelayotgan <b>Ramazon oyi</b> bilan chin qalbdan muborakbod etamiz! 🌙✨\n\n"
        "Ushbu muborak oy barchamizga xayrli va barokatli bo'lsin. Duolarimiz ijobat, ibodatlarimiz maqbul bo'lishini Allohdan so'rab qolamiz. 🤲\n\n"
        "Hurmat bilan, <a href='https://t.me/QuvonchbekBobojonov'>Quvonchbek Bobojonov</a>"
    )
    
    count = 0
    blocked_count = 0
    
    for user in users:
        try:
            sent_msg = await bot.send_animation(
                user.telegram_id, 
                animation=gif_id if gif_id else gif_file, 
                caption=caption, 
                parse_mode="HTML"
            )
            
            if not gif_id and sent_msg.animation:
                gif_id = sent_msg.animation.file_id
            
            if user.is_blocked:
                async with async_session_maker() as session_inner:
                    await update_user_blocked(session_inner, user.telegram_id, False)
            
            count += 1
            if count % 10 == 0:
                print(f"Yuborildi: {count}/{len(users)}")
            
            await asyncio.sleep(0.05)
        except TelegramForbiddenError:
            blocked_count += 1
            async with async_session_maker() as session_inner:
                await update_user_blocked(session_inner, user.telegram_id, True)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_animation(user.telegram_id, animation=gif_id if gif_id else gif_file, caption=caption, parse_mode="HTML")
                count += 1
            except:
                pass
        except Exception as e:
            logger.error(f"Error for {user.telegram_id}: {e}")
            
    print(f"\nTayyor! ✅")
    print(f"Muvaffaqiyatli: {count}")
    print(f"Bloklaganlar: {blocked_count}")

if __name__ == "__main__":
    asyncio.run(run_broadcast())
