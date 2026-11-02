import logging

from redis.exceptions import RedisError

from app.core.redis_client import redis_client
from app.schemas.product import ProductResponse
from app.models.product import Product

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60


def get_cached_product(product_id: str):
    cache_key = f"product:{product_id}"

    try:
        cached_data = redis_client.get(cache_key)

        if cached_data is None:
            return None

        return ProductResponse.model_validate_json(cached_data)

    except RedisError:
        logger.exception("Redis read failed")
        return None

    except ValueError:
        logger.exception("Invalid cached product data")
        return None


def cache_product(product: Product):
    cache_key = f"product:{product.id}"

    try:
        response = ProductResponse.model_validate(product)

        redis_client.setex(
            cache_key,
            CACHE_TTL_SECONDS,
            response.model_dump_json()
        )

    except RedisError:
        logger.exception("Redis write failed")


def invalidate_product_cache(product_id: str):
    cache_key = f"product:{product_id}"

    try:
        redis_client.delete(cache_key)

    except RedisError:
        logger.exception("Redis cache invalidation failed")