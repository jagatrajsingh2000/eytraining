"""
Rate limiting for NutriGuard backend API.

Uses slowapi (token bucket algorithm) with in-memory storage by default.
Key strategy:
  - Authenticated endpoints  → keyed by user_id (from JWT)
  - Unauthenticated endpoints → keyed by client IP (login, signup)

Limits by tier:
  - auth      : 10 req/minute  (login, signup — brute-force protection)
  - write     : 30 req/minute  (POST /meals, profile writes)
  - read      : 120 req/minute (GET endpoints)
  - feedback  : 60 req/minute  (meal feedback)

To switch to Redis (recommended for multi-instance / production):
  1. Add redis==5.0.8 to requirements.txt
  2. Set REDIS_URL env var, e.g. redis://redis:6379
  3. Uncomment the Redis storage block below and remove the in-memory block.
"""

import os
import logging
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("nutriguard.backend.rate_limiter")


def _rate_limit_key(request: Request) -> str:
    """
    Returns a string key used to bucket this request.

    For authenticated requests: "user:<id>" — so each user has their own quota.
    For unauthenticated requests: falls back to the client IP address.
    """
    # slowapi calls key functions with the raw Request object.
    # The JWT payload is already decoded by get_current_user, but that
    # dependency runs after the limiter check, so we do a lightweight
    # header decode here (no DB round-trip, no full validation).
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            import jwt
            from app.auth import JWT_SECRET, JWT_ALGORITHM
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            # Expired / invalid token — fall through to IP keying.
            # Auth validation will reject it properly downstream.
            pass

    return get_remote_address(request)


# ---------------------------------------------------------------------------
# In-memory limiter (default — single instance / local dev)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=_rate_limit_key)

# ---------------------------------------------------------------------------
# Redis limiter (uncomment for multi-instance / production)
# ---------------------------------------------------------------------------
# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
# from slowapi import Limiter
# from limits.storage import RedisStorage
# limiter = Limiter(
#     key_func=_rate_limit_key,
#     storage_uri=REDIS_URL,
# )

# ---------------------------------------------------------------------------
# Rate limit strings — import these in route files
# ---------------------------------------------------------------------------

# Unauthenticated auth endpoints (login / signup) — keyed by IP
LIMIT_AUTH = "10/minute"

# Meal submission — expensive, triggers AI pipeline
LIMIT_MEAL_WRITE = "30/minute"

# Feedback writes
LIMIT_FEEDBACK_WRITE = "60/minute"

# Profile writes
LIMIT_PROFILE_WRITE = "30/minute"

# General read endpoints
LIMIT_READ = "120/minute"
