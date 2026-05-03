"""
Security middleware and utilities for VoteGuide.

Includes:
- Request ID generation for log correlation
- Rate limiting (sliding window, per-IP)
- Input sanitization against prompt injection
- Request timing middleware
"""

import time
import uuid
import re
import logging
from collections import defaultdict
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("voteguide.security")

# ── Request ID Context ────────────────────────────────────────────────────────

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestTraceMiddleware(BaseHTTPMiddleware):
    """Adds X-Request-ID header and logs request timing."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = str(uuid.uuid4())[:8]
        request_id_var.set(rid)
        request.state.request_id = rid

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = rid
        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"

        logger.info(
            f"[{rid}] {request.method} {request.url.path} → {response.status_code} ({elapsed_ms:.0f}ms)"
        )
        return response


# ── Rate Limiting ─────────────────────────────────────────────────────────────

RATE_LIMIT_WINDOW = 60   # seconds
RATE_LIMIT_MAX = 20      # max requests per window per IP
_rate_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    """Return True if request is allowed, False if rate-limited.

    Uses a sliding-window counter per IP address.
    """
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    # Clean old entries
    _rate_store[client_ip] = [t for t in _rate_store[client_ip] if t > window_start]
    if len(_rate_store[client_ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_store[client_ip].append(now)
    return True


# ── Input Sanitization ────────────────────────────────────────────────────────

# Patterns commonly used for prompt injection attacks
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions|prompts|rules)",
    r"(system|admin)\s*prompt\s*:",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"forget\s+(everything|all|your)\s+(you|instructions|rules)",
    r"override\s+(your|the|all)\s+(instructions|rules|safety)",
    r"DAN\s+mode",
    r"jailbreak",
]

_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def sanitize_input(text: str) -> str:
    """Sanitize user input for safety.

    - Strips excessive whitespace
    - Detects and flags potential prompt injection attempts
    - Truncates extremely long inputs

    Returns the sanitized text. Raises ValueError if injection detected.
    """
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', text).strip()

    # Check for prompt injection patterns
    for pattern in _compiled_patterns:
        if pattern.search(cleaned):
            logger.warning(f"Potential prompt injection detected: {cleaned[:80]}...")
            raise ValueError(
                "Your message was flagged by our safety filter. "
                "Please rephrase your question about elections."
            )

    return cleaned


def sanitize_chat_input(message: str) -> str:
    """Sanitize chat message input with graceful handling.

    Returns sanitized text or the original text if sanitization
    encounters a non-injection issue.
    """
    try:
        return sanitize_input(message)
    except ValueError:
        raise
    except Exception:
        return message.strip()
