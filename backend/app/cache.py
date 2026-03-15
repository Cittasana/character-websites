"""
Redis-based API response cache.
Uses a simple key-value store with TTL for retrieve route caching.
"""
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_get(key: str) -> Any | None:
    """
    Get a cached value by key.
    Returns the deserialized value or None if not found.
    """
    try:
        client = await get_redis()
        data = await client.get(key)
        if data is None:
            return None
        return json.loads(data)
    except Exception as exc:
        logger.warning("Cache GET failed for key=%s: %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> bool:
    """
    Set a cached value with optional TTL (seconds).
    Returns True on success, False on failure.
    """
    try:
        client = await get_redis()
        serialized = json.dumps(value, default=str)
        ttl_seconds = ttl or settings.CACHE_TTL_SECONDS
        await client.setex(key, ttl_seconds, serialized)
        return True
    except Exception as exc:
        logger.warning("Cache SET failed for key=%s: %s", key, exc)
        return False


async def cache_delete(key: str) -> None:
    """Invalidate a cache entry."""
    try:
        client = await get_redis()
        await client.delete(key)
    except Exception as exc:
        logger.warning("Cache DELETE failed for key=%s: %s", key, exc)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all cache keys matching a pattern (e.g., 'website:user_id:*')."""
    try:
        client = await get_redis()
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
    except Exception as exc:
        logger.warning("Cache DELETE pattern=%s failed: %s", pattern, exc)


def make_cache_key(*parts: str) -> str:
    """Build a namespaced cache key from parts."""
    return "cw:" + ":".join(str(p) for p in parts)


async def check_redis_health() -> bool:
    """Health check — returns True if Redis is reachable."""
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception:
        return False
