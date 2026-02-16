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

from sqlalchemy import func, select
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
        
    return templates.TemplateResponse("admin_mobile.html", {
        "request": request, 
        "users": users,
        "total_users": total_users,
        "new_today": new_today,
        "bot_token": BOT_TOKEN,
        "search_query": q or ""
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
                "created_at_time": created_at_uz.strftime('%H:%M') if created_at_uz else '--:--'
            })
            
    return {"users": user_list}






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
        from utils.cache import redis_client
        cache_key = f"subs_check:{user_id}"
        
        # Try to get from cache first
        is_subscribed = None
        if redis_client:
            try:
                is_subscribed = redis_client.get(cache_key)
            except Exception:
                pass
        
        if is_subscribed is None:
            try:
                is_subscribed = await check_membership(user_id)
                # Cache for 10 minutes (600 seconds)
                if redis_client:
                    try:
                        redis_client.set(cache_key, "1" if is_subscribed else "0", ex=600)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error checking membership in webapp: {e}")
                is_subscribed = True # Fallback to allow access
        else:
            is_subscribed = (is_subscribed == "1" or is_subscribed == b"1")

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
    return templates.TemplateResponse("calendar.html", {"request": request, "calendar": calendar_data, "region": region})


@app.post(WEBHOOK_PATH)
async def webhook_endpoint(request: Request):
    return await handle_webhook(request)


app.add_event_handler("startup", on_startup)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
