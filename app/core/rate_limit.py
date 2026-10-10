"""
Rate limiting configuration.

Uses slowapi (built on the `limits` library) with Redis as the backend.
Redis persists counters across uvicorn/celery restarts, unlike the
in-memory backend.

Rate limit tiers:
  - Anonymous IP           → 30/min (default for non-authenticated)
  - Authenticated user     → 100/min (default for logged-in)
  - Moderator              → 200/min
  - Sensitive endpoints    → much stricter (login: 5/min, etc.)
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _key_func(request) -> str:
    """
    Key rate limits by:
      - user_id if the request is authenticated (parsed from JWT)
      - IP address otherwise
    """
    # Try to get the authenticated user
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            from app.core.security import decode_access_token
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                return f"user:{payload['sub']}"
    except Exception:
        pass

    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=_key_func,
    storage_uri=settings.REDIS_URL,     # Redis-backed
    default_limits=["100/minute"],      # global default
    strategy="fixed-window",
    headers_enabled=True,               # adds X-RateLimit-* headers
)
