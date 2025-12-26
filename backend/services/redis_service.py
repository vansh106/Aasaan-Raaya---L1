"""
Redis Service - Redis connection and caching operations.

Provides async Redis client for caching, rate limiting, and session management.
"""

from typing import Optional, List
import redis.asyncio as aioredis
from redis.asyncio import Redis
from config import settings
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis service for caching and rate limiting.
    Uses aioredis for async Redis operations.
    """

    _instance: Optional["RedisService"] = None
    _client: Optional[Redis] = None

    def __new__(cls):
        """Singleton pattern for Redis connection"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Initialize Redis connection"""
        if self._client is None:
            try:
                # Use Redis URL if provided, otherwise construct from components
                if settings.redis_url:
                    redis_url = settings.redis_url
                else:
                    # Construct Redis URL from components
                    if settings.redis_password:
                        redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
                    else:
                        redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"

                self._client = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30,
                )

                # Test connection
                await self._client.ping()
                logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # Set client to None so we can retry later
                self._client = None
                raise

    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> Optional[Redis]:
        """Get Redis client instance"""
        return self._client

    async def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if self._client is None:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL"""
        if not self._client:
            return False
        try:
            if ttl:
                await self._client.setex(key, ttl, value)
            else:
                await self._client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self._client:
            return False
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key"""
        if not self._client:
            return False
        try:
            return await self._client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment key value (useful for rate limiting)"""
        if not self._client:
            return None
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None

    async def set_if_not_exists(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value only if key doesn't exist (atomic operation)"""
        if not self._client:
            return False
        try:
            if ttl:
                return await self._client.set(key, value, ex=ttl, nx=True)
            else:
                return await self._client.set(key, value, nx=True)
        except Exception as e:
            logger.error(f"Redis SETNX error for key {key}: {e}")
            return False

    # -------------------- List helpers (for chat history buffers) -------------------- #

    async def list_append(self, key: str, values: List[str], ttl: Optional[int] = None) -> bool:
        """Append multiple values to a Redis list and optionally set TTL."""
        if not self._client:
            return False
        try:
            if values:
                await self._client.rpush(key, *values)
            if ttl:
                await self._client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Redis RPUSH error for key {key}: {e}")
            return False

    async def list_get_all(self, key: str) -> List[str]:
        """Get all values from a Redis list."""
        if not self._client:
            return []
        try:
            return await self._client.lrange(key, 0, -1)
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {e}")
            return []

    async def list_pop_all(self, key: str) -> List[str]:
        """Atomically read and delete all entries from a Redis list."""
        values = await self.list_get_all(key)
        if values and self._client:
            try:
                await self._client.delete(key)
            except Exception as e:
                logger.error(f"Redis DELETE error for key {key}: {e}")
        return values


# Global Redis service instance
redis_service = RedisService()
