from upstash_redis import Redis
from core.config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN

redis_client = None

if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
    try:
        redis_client = Redis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)
    except Exception as e:
        print(f"Redis Connection Error: {e}")
