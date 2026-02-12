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

from db.base import engine, Base

import logging
import sys
from starlette.middleware.sessions import SessionMiddleware


# Configure logging to see errors in Vercel logs
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=BOT_TOKEN)
templates = Jinja2Templates(directory="templates")

@app.get("/debug")
async def debug_info():
    return {"status": "ok", "python_version": sys.version}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__}
    )

from fastapi.responses import JSONResponse


# Admin Panel Setup


from utils.admin_panel import setup_admin

# Admin Panel Setup moved to utils/admin_panel.py
setup_admin(app, engine)

first_run = False


@app.post("/api/send-notifications")
async def trigger_notifications(request: Request):
    # Optional: check for a secret header to prevent unauthorized access
    # auth_header = request.headers.get("Authorization")
    # if auth_header != f"Bearer {os.getenv('CRON_SECRET')}":
    #    raise HTTPException(status_code=403, detail="Unauthorized")
    
    count = await send_daily_notifications()
    return {"status": "success", "users_notified": count}



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
        
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URI:
        await bot.set_webhook(WEBHOOK_URI)
    
    await set_default_commands(bot)
    await on_startup_notify(bot)


async def on_shutdown():
    global first_run
    if first_run:
        first_run = False
        await on_shutdown_notify(bot)


@app.get("/calendar", response_class=HTMLResponse)
async def get_calendar(request: Request, region: str = "tashkent"):
    calendar_data = get_full_calendar(region)
    return templates.TemplateResponse("calendar.html", {"request": request, "calendar": calendar_data, "region": region})

@app.post(WEBHOOK_PATH)
async def webhook_endpoint(request: Request):
    return await handle_webhook(request)


app.add_event_handler("startup", on_startup)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
