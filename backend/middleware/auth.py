from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from config import settings
from typing import Optional
import hashlib
import time

# API Key header security
api_key_header = APIKeyHeader(name=settings.api_key_header_name, auto_error=False)


def verify_api_key(api_key: str) -> bool:
    """
    Verify the API key against the configured key.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not api_key:
        return False

    # Use hashlib to do constant-time comparison
    expected_hash = hashlib.sha256(settings.api_key.encode()).hexdigest()
    provided_hash = hashlib.sha256(api_key.encode()).hexdigest()

    return expected_hash == provided_hash


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    FastAPI dependency to validate API key from header.

    Usage:
        @app.get("/protected")
        async def protected_route(api_key: str = Depends(get_api_key)):
            ...
    """
    if api_key is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Missing API Key",
                "message": f"Please provide API key in '{settings.api_key_header_name}' header",
            },
        )

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail={
                "error": "Invalid API Key",
                "message": "The provided API key is invalid",
            },
        )

    return api_key


# Simple in-memory rate limiter (for production, use Redis)
class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self._requests: dict[str, list[float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()

        if key not in self._requests:
            self._requests[key] = []

        # Clean old entries
        self._requests[key] = [
            ts for ts in self._requests[key] if now - ts < window_seconds
        ]

        if len(self._requests[key]) >= max_requests:
            return False

        self._requests[key].append(now)
        return True


rate_limiter = RateLimiter()


async def check_rate_limit(api_key: str = Depends(get_api_key)) -> str:
    """
    FastAPI dependency to check rate limits.
    Combines API key validation with rate limiting.
    """
    if not rate_limiter.is_allowed(
        api_key, settings.rate_limit_requests, settings.rate_limit_window
    ):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate Limit Exceeded",
                "message": f"Maximum {settings.rate_limit_requests} requests per {settings.rate_limit_window} seconds",
            },
        )

    return api_key
