import redis

from app.core.config import settings


redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1
)


def check_redis_connection() -> bool:
    try:
        return redis_client.ping()
    except redis.RedisError:
        return False