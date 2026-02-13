from aiogram import types
from aiohttp import web
from fastapi import Request, FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from core.config import WEBHOOK_PATH, WEBHOOK_URI, BOT_TOKEN
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
async def admin_mobile(request: Request, token: str = None):

    from core.config import BOT_TOKEN, ADMINS
    # Simple security: check if token matches bot token or a secret
    if token != BOT_TOKEN:
        # In a real app, you'd check initData, but for now, we'll use a token
        return HTMLResponse("Unauthorized", status_code=403)
        
    async with async_session_maker() as session:
        # Extract bot ID from token (it's the first part before the colon)
        bot_id = int(BOT_TOKEN.split(":")[0])
        
        result = await session.execute(
            select(User).where(User.telegram_id != bot_id).order_by(User.created_at.desc())
        )
        users = result.scalars().all()

        
        from datetime import timedelta
        # Convert created_at to UZ time (UTC+5)
        for user in users:
            if user.created_at:
                user.created_at_uz = user.created_at + timedelta(hours=5)
            else:
                user.created_at_uz = None
        
        # Stats in UZ time
        from utils.ramadan_calculator import get_now_uz
        now_uz = get_now_uz()
        today_uz = now_uz.date()
        
        total_users = len(users)
        new_today = sum(1 for u in users if u.created_at_uz and u.created_at_uz.date() == today_uz)
        
    return templates.TemplateResponse("admin_mobile.html", {
        "request": request, 
        "users": users,
        "total_users": total_users,
        "new_today": new_today,
        "bot_token": BOT_TOKEN
    })






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
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != WEBHOOK_URI:
            await bot.set_webhook(WEBHOOK_URI)
        
        await set_default_commands(bot)
        await on_startup_notify(bot)
    except Exception as e:
        logger.error(f"Error during bot setup: {e}")
    
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
        try:
            is_subscribed = await check_membership(user_id)
            if not is_subscribed:
                from core.config import CHANNELS
                # Pass the first channel for the button, or the list if needed
                return templates.TemplateResponse("subscription_required.html", {
                    "request": request, 
                    "channels": CHANNELS,
                    "primary_channel": CHANNELS[0].replace("@", "") if CHANNELS else "QuvonchbekBobojonov"
                })
        except Exception as e:
            logger.error(f"Error checking membership in webapp: {e}")
            # If checking fails (e.g. rate limit), we allow access as a fallback to avoid UX break
            pass
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
