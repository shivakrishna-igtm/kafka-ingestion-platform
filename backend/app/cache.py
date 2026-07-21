"""Redis-backed cache with a transparent in-memory fallback so the app
runs identically with or without a Redis instance."""
import json
import logging
import time

from .config import settings

log = logging.getLogger("cache")


class _MemoryCache:
    def __init__(self):
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str):
        item = self._store.get(key)
        if not item:
            return None
        expires, value = item
        if time.monotonic() > expires:
            del self._store[key]
            return None
        return value

    def setex(self, key: str, ttl: int, value: str):
        self._store[key] = (time.monotonic() + ttl, value)

    def delete(self, *keys):
        for k in keys:
            self._store.pop(k, None)


def _build():
    if settings.redis_url:
        try:
            import redis
            client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            log.info("cache: connected to redis")
            return client
        except Exception as e:  # noqa: BLE001
            log.warning("cache: redis unavailable (%s), using in-memory fallback", e)
    return _MemoryCache()


_client = _build()
TTL_SECONDS = 60


def get_json(key: str):
    raw = _client.get(key)
    return json.loads(raw) if raw else None


def set_json(key: str, value, ttl: int = TTL_SECONDS):
    _client.setex(key, ttl, json.dumps(value, default=str))


def invalidate(*keys: str):
    _client.delete(*keys)
