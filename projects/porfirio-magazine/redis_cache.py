"""Portfolio excerpt, adapted. Redis cache layer for a Flask app.

Caching is best-effort: every op guards on is_available(), so a dead Redis
degrades to cache misses instead of taking the app down.
"""
from functools import wraps

import hashlib
import pickle

from flask import current_app
import redis


class RedisCache:
    """redis-py wrapper that degrades to a no-op when Redis is down."""

    def __init__(self, app=None):
        self.redis_client = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Connect at startup; leave caching off if Redis is unreachable."""
        redis_url = app.config.get('CACHE_REDIS_URL') or app.config.get('REDIS_URL')

        if not redis_url:
            app.logger.warning('Redis URL not configured. Caching disabled.')
            return

        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # pickle needs raw bytes
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self.redis_client.ping()  # from_url is lazy; this is the first real connect
            app.logger.info('Redis cache connected successfully')
        except (redis.ConnectionError, redis.TimeoutError) as exc:
            app.logger.warning(f'Redis connection failed: {exc}. Caching disabled.')
            self.redis_client = None

    def is_available(self):
        """Return True only if Redis answers a live PING."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False

    def get(self, key):
        if not self.is_available():
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                return pickle.loads(value)
        except Exception as exc:
            current_app.logger.error(f'Cache get error: {exc}')
        return None

    def set(self, key, value, timeout=300):
        if not self.is_available():
            return False
        try:
            self.redis_client.setex(key, timeout, pickle.dumps(value))
            return True
        except Exception as exc:
            current_app.logger.error(f'Cache set error: {exc}')
            return False

    def delete_pattern(self, pattern):
        """Delete every key matching a glob pattern (e.g. 'articles:*'); return the count."""
        if not self.is_available():
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            return self.redis_client.delete(*keys) if keys else 0
        except Exception as exc:
            current_app.logger.error(f'Cache delete pattern error: {exc}')
            return 0


# singleton; wire up via cache.init_app(app) at startup
cache = RedisCache()


def _make_cache_key(key_prefix, func, args, kwargs):
    """Build a stable cache key for a call.

    Keeps the function name readable and hashes the args so the key length
    is bounded and free of memory addresses. kwargs are sorted so call order
    doesn't change the key.
    """
    key = f'{key_prefix}:{func.__name__}'
    if args or kwargs:
        raw = repr((args, sorted(kwargs.items())))
        digest = hashlib.md5(raw.encode('utf-8')).hexdigest()
        key += f':{digest}'
    return key


def cached(timeout=300, key_prefix='view'):
    """Cache a function's return value, keyed by prefix + name + arg hash.

        @cached(timeout=600, key_prefix='articles')
        def get_published_articles():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _make_cache_key(key_prefix, func, args, kwargs)

            hit = cache.get(cache_key)
            if hit is not None:
                current_app.logger.debug(f'Cache HIT: {cache_key}')
                return hit

            current_app.logger.debug(f'Cache MISS: {cache_key}')
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        return wrapper
    return decorator


def invalidate_cache(pattern):
    """Drop every key matching a glob pattern after a write, e.g. invalidate_cache('articles:*')."""
    return cache.delete_pattern(pattern)
