"""Rate Limiting Middleware & Decorators for sensitive endpoints."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class EndpointRateLimiter(BaseHTTPMiddleware):
    """In-memory rate limiter per IP / User for sensitive authentication and AI endpoints."""

    def __init__(self, app, requests_per_minute: int = 60, sensitive_requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.sensitive_requests_per_minute = sensitive_requests_per_minute
        self._general_buckets = defaultdict(list)
        self._sensitive_buckets = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        path = request.url.path

        # Sensitive paths (login, password reset, OCR processing, AI queries)
        is_sensitive = any(
            p in path for p in ["/auth/login", "/auth/forgot-password", "/ask-red-bear/query", "/ocr/jobs"]
        )

        bucket = self._sensitive_buckets[client_ip] if is_sensitive else self._general_buckets[client_ip]
        limit = self.sensitive_requests_per_minute if is_sensitive else self.requests_per_minute

        # Prune old window (60s)
        window_start = now - 60
        valid_requests = [t for t in bucket if t > window_start]
        bucket.clear()
        bucket.extend(valid_requests)

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before retrying.",
            )

        bucket.append(now)
        return await call_next(request)
