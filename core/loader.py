from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
import logging

from core.config import BOT_TOKEN, REDIS_URL

if REDIS_URL:
    try:
        storage = RedisStorage.from_url(
            REDIS_URL,
            key_builder=DefaultKeyBuilder(with_destiny=True)
        )
        logging.info("Aiogram FSM using RedisStorage")
    except Exception as e:
        logging.error(f"Failed to connect to Redis for FSM: {e}")
        storage = MemoryStorage()
else:
    storage = MemoryStorage()

dp = Dispatcher(storage=storage)
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
