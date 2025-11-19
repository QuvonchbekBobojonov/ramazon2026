from fastapi import FastAPI, Request
from aiogram import types
from mangum import Mangum

from core.config import WEBHOOK_URI, BOT_TOKEN
from core.loader import bot, dp

import handlers
from utils.set_bot_commands import set_default_commands
from utils.notify_admins import on_startup_notify, on_shutdown_notify

app = FastAPI()


# Webhook endpoint
@app.post(f"/{BOT_TOKEN}")
async def handle_webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.feed_webhook_update(bot, update)
    return {"ok": True}


# Startup and shutdown events
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URI)
    await set_default_commands(bot)
    # await on_startup_notify(bot)


@app.on_event("shutdown")
async def on_shutdown():
    await on_shutdown_notify(bot)


# For Vercel serverless
handler = Mangum(app)
