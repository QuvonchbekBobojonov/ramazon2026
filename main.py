from aiogram import types
from aiohttp import web
from fastapi import Request, FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


from core.config import WEBHOOK_PATH, WEBHOOK_URI, BOT_TOKEN, WEBHOOK_HOST
from core.loader import bot, dp

import handlers
from utils.notify_admins import on_startup_notify, on_shutdown_notify
from utils.set_bot_commands import set_default_commands
from utils.ramadan_calculator import get_daily_times, get_full_calendar
from utils.notifications import send_daily_notifications
from middlewares import setup_middlewares

from db.base import engine, Base


import logging
import sys
from starlette.middleware.sessions import SessionMiddleware


# Configure logging to see errors in Vercel logs
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=BOT_TOKEN)

from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_details = {
        "error": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc()
    }
    logger.error(f"Global error: {error_details}")
    return JSONResponse(
        status_code=500,
        content=error_details
    )

from sqlalchemy import func, select, String
from db.models import User
from db.base import async_session_maker

@app.get("/db-check")
async def db_check():
    async with async_session_maker() as session:
        result = await session.execute(select(func.count(User.id)))
        count = result.scalar()
        return {"total_users": count}

templates = Jinja2Templates(directory="templates")



# Admin Panel Setup



from utils.admin_panel import setup_admin

# Admin Panel Setup moved to utils/admin_panel.py
setup_admin(app, engine)

first_run = False


@app.get("/api/user-photo/{telegram_id}")
async def get_user_photo(telegram_id: int, token: str = None):
    from core.config import BOT_TOKEN
    if token != BOT_TOKEN:
        return HTMLResponse("Unauthorized", status_code=403)
    
    try:
        from core.loader import bot
        photos = await bot.get_user_profile_photos(telegram_id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id # Get the medium/large version
            file = await bot.get_file(file_id)
            photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
            from fastapi.responses import RedirectResponse
            return RedirectResponse(photo_url)
    except Exception as e:
        logger.error(f"Error fetching photo for {telegram_id}: {e}")
    
    # Return a placeholder or 404
    return HTMLResponse("Not Found", status_code=404)

@app.get("/admin-mobile")
async def admin_mobile(request: Request, token: str = None, q: str = None):
    from core.config import BOT_TOKEN
    if token != BOT_TOKEN:
        return HTMLResponse("Unauthorized", status_code=403)
        
    async with async_session_maker() as session:
        bot_id = int(BOT_TOKEN.split(":")[0])
        
        # Base query
        query = select(User).where(User.telegram_id != bot_id)
        
        # Search filter
        if q:
            search_filter = (
                (User.full_name.ilike(f"%{q}%")) | 
                (User.username.ilike(f"%{q}%")) | 
                (User.telegram_id.cast(String).ilike(f"%{q}%"))
            )
            query = query.where(search_filter)
            
        # Total counts
        total_result = await session.execute(select(func.count(User.id)).where(User.telegram_id != bot_id))
        total_users = total_result.scalar()
        
        active_result = await session.execute(select(func.count(User.id)).where((User.telegram_id != bot_id) & (User.is_blocked == False)))
        active_users = active_result.scalar()
        
        blocked_result = await session.execute(select(func.count(User.id)).where((User.telegram_id != bot_id) & (User.is_blocked == True)))
        blocked_users = blocked_result.scalar()
        
        from utils.ramadan_calculator import get_now_uz
        now_uz = get_now_uz()
        today_uz = now_uz.date()
        
        # We need to handle UZ time timezone correctly in SQL ideally, but for now we'll do it in memory for stats
        # For performance, maybe just count all today
        # new_today = ... # Simplified below
        
        # Fetch only last 10 users initially
        limit = 10
        result = await session.execute(query.order_by(User.created_at.desc()).limit(limit))
        users = result.scalars().all()
        
        from datetime import datetime, timedelta
        for user in users:
            if user.created_at:
                user.created_at_uz = user.created_at + timedelta(hours=5)
            else:
                user.created_at_uz = None
        
        # Stats
        new_today_result = await session.execute(
            select(func.count(User.id)).where(
                (User.telegram_id != bot_id) & 
                (User.created_at >= datetime.utcnow() - timedelta(days=1)) # Rough approximation
            )
        )
        new_today = new_today_result.scalar()

        # Fetch all prayers for admin management
        from db.crud import get_prayers, get_user
        prayers = await get_prayers(session, limit=100)
        for p in prayers:
            if p.created_at:
                p.uz_time = p.created_at + timedelta(hours=5)
            # Link real author info for admin eyes only
            p.real_author = await get_user(session, p.user_id)
            
    return templates.TemplateResponse("admin_mobile.html", {
        "request": request, 
        "users": users,
        "total_users": total_users,
        "active_users": active_users,
        "blocked_users": blocked_users,
        "new_today": new_today,
        "bot_token": BOT_TOKEN,
        "search_query": q or "",
        "prayers": prayers
    })

@app.get("/api/admin/users")
async def api_get_users(token: str, offset: int = 0, limit: int = 10, q: str = None):
    from core.config import BOT_TOKEN
    if token != BOT_TOKEN:
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
        
    async with async_session_maker() as session:
        bot_id = int(BOT_TOKEN.split(":")[0])
        query = select(User).where(User.telegram_id != bot_id)
        
        if q:
            search_filter = (
                (User.full_name.ilike(f"%{q}%")) | 
                (User.username.ilike(f"%{q}%")) | 
                (User.telegram_id.cast(String).ilike(f"%{q}%"))
            )
            query = query.where(search_filter)
            
        result = await session.execute(query.order_by(User.created_at.desc()).offset(offset).limit(limit))
        users = result.scalars().all()
        
        from datetime import timedelta
        user_list = []
        for u in users:
            created_at_uz = (u.created_at + timedelta(hours=5)) if u.created_at else None
            user_list.append({
                "id": u.id,
                "telegram_id": u.telegram_id,
                "full_name": u.full_name,
                "username": u.username,
                "region": u.region,
                "is_blocked": u.is_blocked,
                "created_at_time": created_at_uz.strftime('%H:%M') if created_at_uz else '--:--'
            })
            
    return {"users": user_list}


@app.post("/api/admin/broadcast/ramadan")
async def api_broadcast_ramadan(token: str):
    from core.config import BOT_TOKEN
    if token != BOT_TOKEN:
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    
    async with async_session_maker() as session:
        from db.crud import get_all_users
        users = await get_all_users(session)
    
    async def run_broadcast():
        from aiogram.types import FSInputFile
        from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
        import asyncio
        from db.base import async_session_maker
        from db.crud import update_user_blocked
        
        gif_path = "static/ramadan.gif"
        gif_file = FSInputFile(gif_path)
        gif_id = None # Store file_id after first send
        
        caption = (
            "<b>Assalomu alaykum va rahmatullohi va barokatuh!</b>\n\n"
            "Barchangizni kirib kelayotgan <b>Ramazon oyi</b> bilan chin qalbdan muborakbod etamiz! 🌙✨\n\n"
            "Ushbu muborak oy barchamizga xayrli va barokatli bo'lsin. Duolarimiz ijobat, ibodatlarimiz maqbul bo'lishini Allohdan so'rab qolamiz. 🤲\n\n"
            "Hurmat bilan, <a href='https://t.me/QuvonchbekBobojonov'>Quvonchbek Bobojonov</a>"
        )
        
        for user in users:
            if user.is_blocked:
                continue
            try:
                # Use file_id if available, otherwise upload
                sent_msg = await bot.send_animation(
                    user.telegram_id, 
                    animation=gif_id if gif_id else gif_file, 
                    caption=caption, 
                    parse_mode="HTML"
                )
                
                # Save file_id from the first successful send
                if not gif_id and sent_msg.animation:
                    gif_id = sent_msg.animation.file_id
                
                # If user was previously blocked, mark as unblocked
                if user.is_blocked:
                    async with async_session_maker() as session_inner:
                        await update_user_blocked(session_inner, user.telegram_id, False)
                
                await asyncio.sleep(0.05) # Rate limit protection
            except TelegramForbiddenError:
                async with async_session_maker() as session_inner:
                    await update_user_blocked(session_inner, user.telegram_id, True)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                try:
                    await bot.send_animation(user.telegram_id, animation=gif_id if gif_id else gif_file, caption=caption, parse_mode="HTML")
                except:
                    pass
            except Exception as e:
                logger.error(f"Broadcast error for {user.telegram_id}: {e}")
                
    import asyncio
    asyncio.create_task(run_broadcast())
    
    return {"success": True, "count": len(users)}


@app.post("/api/admin/broadcast/prayers")
async def api_broadcast_prayers(token: str):
    from core.config import BOT_TOKEN, WEBHOOK_HOST
    if token != BOT_TOKEN:
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    
    # Get bot username for deep linking
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    async with async_session_maker() as session:
        from db.crud import get_all_users
        users = await get_all_users(session)
    
    async def run_broadcast_prayers():
        from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
        import asyncio
        from db.base import async_session_maker
        from db.crud import update_user_blocked
        from keyboards.default.ramadan_menu import get_ramadan_menu
        
        # Post matni
        text = (
            "✨ <b>Yangi funksiya: Duo Devori!</b>\n\n"
            "Muborak Ramazon oyida bir-birimizning haqimizga duo qilish, niyatlarimiz bilan o'rtoqlashish va o'zaro ma'naviy bog'liqlikni his qilish uchun <b>\"Duo Devori\"</b> bo'limini ishga tushirdik. 🤲\n\n"
            "🌙 <b>Bu yerda siz:</b>\n"
            "• O'z duo va niyatlaringizni yozib qoldirishingiz;\n"
            "• Boshqalarning duolariga \"Omiyn\" deb qo'shilishingiz;\n"
            "• Ezgu niyatlarni yaqinlaringizga ulashishingiz mumkin.\n\n"
            "Duolaringiz ijobat bo'lsin! Pastdagi tugma yoki mana bu havola orqali o'tishingiz mumkin: 👇\n\n"
            f"🔗 <a href='https://t.me/{bot_username}?start=prayers'>Duo Devorini ochish</a>"
        )
        
        for user in users:
            if user.is_blocked:
                continue
            try:
                # Get the menu with the new Duo Devori button
                menu = get_ramadan_menu(region=user.region or "tashkent", is_admin=False, user_id=user.telegram_id)
                
                await bot.send_message(user.telegram_id, text=text, reply_markup=menu, parse_mode="HTML")
                
                if user.is_blocked:
                    async with async_session_maker() as session_inner:
                        await update_user_blocked(session_inner, user.telegram_id, False)
                
                await asyncio.sleep(0.05)
            except TelegramForbiddenError:
                async with async_session_maker() as session_inner:
                    await update_user_blocked(session_inner, user.telegram_id, True)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                try:
                    menu = get_ramadan_menu(region=user.region or "tashkent", is_admin=False, user_id=user.telegram_id)
                    await bot.send_message(user.telegram_id, text=text, reply_markup=menu, parse_mode="HTML")
                except:
                    pass
            except Exception as e:
                logger.error(f"Duo broadcast error for {user.telegram_id}: {e}")
                
    import asyncio
    asyncio.create_task(run_broadcast_prayers())
    
    return {"success": True, "count": len(users)}






async def set_webhook():
    await bot.set_webhook(WEBHOOK_URI)


async def handle_webhook(request: Request):
    url = str(request.url)
    index = url.rfind('/')
    token = url[index + 1:]

    if token == BOT_TOKEN:
        update = types.Update(**await request.json())
        await dp.feed_webhook_update(bot, update)
        return web.Response()
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


async def on_startup():
    global first_run
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Check for missing columns (fix schema)
    try:
        from fix_db_schema import fix_schema
        await fix_schema()
    except Exception as e:
        logger.error(f"Error fixing schema: {e}")
        
    try:
        if "your-webhook-host" not in WEBHOOK_URI and WEBHOOK_HOST:
            webhook_info = await bot.get_webhook_info()
            if webhook_info.url != WEBHOOK_URI:
                await bot.set_webhook(WEBHOOK_URI)
                logger.info(f"Webhook set to: {WEBHOOK_URI}")
        else:
            logger.warning("WEBHOOK_HOST is not configured properly. Skipping webhook setup.")
            # Optionally delete webhook if you want to use polling, 
            # but this is a FastAPI app, so it expects webhooks.
        
        await set_default_commands(bot)
        await on_startup_notify(bot)
    except Exception as e:
        logger.error(f"Error during bot setup (webhook might be invalid): {e}")
    
    setup_middlewares(dp)
    
    # Scheduler optimization
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from pytz import timezone
    
    uz_tz = timezone('Asia/Tashkent')
    scheduler = AsyncIOScheduler(timezone=uz_tz)
    
    # Schedule notifications at 05:00 and 05:30
    scheduler.add_job(send_daily_notifications, 'cron', hour=5, minute=0)
    scheduler.add_job(send_daily_notifications, 'cron', hour=5, minute=30)
    
    scheduler.start()
    logger.info("Scheduler started (05:00 and 05:30 UZ time)")




async def on_shutdown():
    global first_run
    if first_run:
        first_run = False
        await on_shutdown_notify(bot)


@app.get("/calendar", response_class=HTMLResponse)
async def get_calendar(request: Request, region: str = "tashkent", user_id: int = None):
    from utils.subscription import check_membership
    
    # If user_id is provided, check their subscription status
    if user_id:
        from core.config import ADMINS
        if str(user_id) in ADMINS or user_id in ADMINS:
             calendar_data = get_full_calendar(region)
             return templates.TemplateResponse("calendar.html", {"request": request, "calendar": calendar_data, "region": region, "user_id": user_id})

        # Bazadan tekshirish
        async with async_session_maker() as session:
             from db.crud import get_user, update_user_subscription
             db_user = await get_user(session, user_id)
             is_subscribed = db_user.is_subscribed if db_user else False

             # Agar bazada obuna bo'lmagan bo'lsa, real-time tekshiramiz
             if not is_subscribed:
                 try:
                     is_subscribed = await check_membership(user_id)
                     if is_subscribed and db_user:
                         await update_user_subscription(session, user_id, True)
                 except Exception as e:
                     logger.error(f"Error checking membership in webapp: {e}")
                     is_subscribed = True # Fallback to allow access

        if not is_subscribed:
            from core.config import CHANNELS
            return templates.TemplateResponse("subscription_required.html", {
                "request": request, 
                "channels": CHANNELS,
                "primary_channel": CHANNELS[0].replace("@", "") if CHANNELS else "QuvonchbekBobojonov"
            })

    elif not user_id:
        from core.config import CHANNELS
        return templates.TemplateResponse("subscription_required.html", {
            "request": request,
            "channels": CHANNELS,
            "primary_channel": CHANNELS[0].replace("@", "") if CHANNELS else "QuvonchbekBobojonov"
        })


    calendar_data = get_full_calendar(region)
    return templates.TemplateResponse("calendar.html", {"request": request, "calendar": calendar_data, "region": region, "user_id": user_id})


@app.get("/prayers", response_class=HTMLResponse)
async def get_prayers_page(request: Request, user_id: int = None):
    async with async_session_maker() as session:
        from db.crud import get_prayers, get_user, get_user_amens
        db_user = await get_user(session, user_id) if user_id else None
        user_name = db_user.full_name if db_user else "Mehmon"
        
        prayers = await get_prayers(session, limit=50)
        user_amens = await get_user_amens(session, user_id) if user_id else set()
        
        # Adjust timestamps to Uzbekistan time (UTC+5)
        from datetime import timedelta
        for p in prayers:
            if p.created_at:
                p.uz_time = p.created_at + timedelta(hours=5)
        
        # Admin check
        from core.config import ADMINS, BOT_TOKEN
        is_admin = str(user_id) in ADMINS or user_id in ADMINS
        
    bot_info = await bot.get_me()
    
    return templates.TemplateResponse("prayers.html", {
        "request": request, 
        "prayers": prayers, 
        "user_id": user_id or 0,
        "user_name": user_name,
        "bot_username": bot_info.username,
        "user_amens": user_amens
    })

from pydantic import BaseModel
class PrayerCreate(BaseModel):
    user_id: int
    content: str
    is_anonymous: bool
    author_name: str

@app.post("/api/prayers")
async def api_add_prayer(prayer_data: PrayerCreate):
    async with async_session_maker() as session:
        from db.crud import add_prayer
        prayer = await add_prayer(
            session, 
            user_id=prayer_data.user_id,
            author_name=prayer_data.author_name,
            content=prayer_data.content,
            is_anonymous=prayer_data.is_anonymous
        )
    if not prayer:
        return JSONResponse({"error": "Siz ushbu duoni allaqachon yuborgansiz!"}, status_code=400)
    return {"success": True}

@app.post("/api/prayers/{prayer_id}/amen")
async def api_inc_amen(prayer_id: int, user_id: int):
    async with async_session_maker() as session:
        from db.crud import increment_amen
        new_count = await increment_amen(session, prayer_id, user_id)
    return {"amen_count": new_count}

@app.delete("/api/admin/prayers/{prayer_id}")
async def api_delete_prayer(prayer_id: int, token: str):
    from core.config import BOT_TOKEN
    if token != BOT_TOKEN:
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
        
    async with async_session_maker() as session:
        from db.crud import delete_prayer
        await delete_prayer(session, prayer_id)
    return {"success": True}


@app.post(WEBHOOK_PATH)
async def webhook_endpoint(request: Request):
    return await handle_webhook(request)


app.add_event_handler("startup", on_startup)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
