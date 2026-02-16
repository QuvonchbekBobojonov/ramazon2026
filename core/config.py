from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")

ADMINS = env.list("ADMINS")

WEBHOOK_HOST = env.str("WEBHOOK_HOST")
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URI = WEBHOOK_HOST + WEBHOOK_PATH

CHANNELS = ["@QuvonchbekBobojonov"]

DATABASE_URL = env.str("DATABASE_URL")

UPSTASH_REDIS_REST_URL = env.str("UPSTASH_REDIS_REST_URL", default=None)
UPSTASH_REDIS_REST_TOKEN = env.str("UPSTASH_REDIS_REST_TOKEN", default=None)

REDIS_URL = env.str("REDIS_URL", default=None)
