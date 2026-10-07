"""Optional Redis cache for dataset queries (#26)."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)
_client = None
_stats = {"hits": 0, "misses": 0}


def get_redis():
    global _client
    if not settings.REDIS_URL:
        return None
    if _client is not None:
        return _client
    try:
        import redis

        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        _client.ping()
        return _client
    except Exception as exc:
        logger.warning("Redis unavailable: %s", exc)
        _client = False  # type: ignore
        return None


def cache_key(prefix: str, payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return f"dv:{prefix}:{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def get_json(key: str) -> Any | None:
    r = get_redis()
    if not r:
        _stats["misses"] += 1
        return None
    try:
        val = r.get(key)
        if val is None:
            _stats["misses"] += 1
            return None
        _stats["hits"] += 1
        return json.loads(val)
    except Exception:
        _stats["misses"] += 1
        return None


def set_json(key: str, value: Any, ttl: int | None = None) -> None:
    r = get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl or settings.REDIS_TTL_SECONDS, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("Redis set failed: %s", exc)


def stats() -> dict:
    return dict(_stats)
