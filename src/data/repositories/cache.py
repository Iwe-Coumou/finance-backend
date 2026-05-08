from src.logging import get_logger
from src.config import get_env_var
import json
import redis

_logger = get_logger(__name__)

_redis_client = None

def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    try:
        _redis_client = redis.from_url(get_env_var("REDIS_URL"))
        _logger.info("Redis client created")
        return _redis_client
    except Exception as e:
        _logger.error(f"Failed to create redis client: {e}")
        raise

def cache_get(key: str) -> dict | list | None:
    try:
        hit = _get_redis().get(key)
        if hit is None:
            _logger.debug(f"Cache miss | key={key}")
            return None
        _logger.info(f"Cache hit | key={key}")
        return json.loads(hit)
    except Exception as e:
        _logger.warning(f"Redis read failed | key={key} error={e}")
        return None

def cache_set(key: str, value: dict | list, ttl: int) -> None:
    try:
        _get_redis().setex(key, ttl, json.dumps(value))
        _logger.info(f"Cache set | key={key} ttl={ttl}s")
    except Exception as e:
        _logger.warning(f"Redis write failed | key={key} error={e}")

def cache_delete(key: str) -> None:
    try:
        _get_redis().delete(key)
        _logger.info(f"Cache deleted | key={key}")
    except Exception as e:
        _logger.warning(f"Redis delete failed | key={key} error={e}")