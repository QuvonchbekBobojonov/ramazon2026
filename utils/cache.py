import os
import logging
from core.config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN, REDIS_URL

redis_client = None

# Prioritize local Redis for speed
if REDIS_URL:
    try:
        from redis import Redis
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        logging.info("Using local Redis for caching")
    except Exception as e:
        logging.error(f"Failed to connect to local Redis: {e}")

# Fallback to Upstash if local Redis is not available
if not redis_client and UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
    try:
        from upstash_redis import Redis as UpstashRedis
        redis_client = UpstashRedis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)
        logging.info("Using Upstash Redis for caching")
    except Exception as e:
        logging.error(f"Upstash Redis Connection Error: {e}")
