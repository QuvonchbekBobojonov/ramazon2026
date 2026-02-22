import json
import redis.asyncio as redis
from core.config import REDIS_URL
import logging

logger = logging.getLogger(__name__)

# Initialize Redis client with timeouts to prevent hangs (in seconds)
redis_client = redis.from_url(
    REDIS_URL, 
    decode_responses=True,
    socket_timeout=5.0,
    socket_connect_timeout=5.0
)

async def set_cache(key: str, value: dict, expire: int = 3600):
    try:
        await redis_client.set(key, json.dumps(value), ex=expire)
    except Exception as e:
        logger.error(f"Redis set error: {e}")

async def get_cache(key: str) -> dict:
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.error(f"Redis get error: {e}")
    return None

async def delete_cache(key: str):
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.error(f"Redis delete error: {e}")
