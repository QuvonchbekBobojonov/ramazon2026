from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from core.config import BOT_TOKEN, REDIS_URL

storage = RedisStorage.from_url(REDIS_URL)

dp = Dispatcher(storage=storage)
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
