"""Optional bearer/token auth gate (#27)."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.AUTH_DISABLED or not settings.UI_AUTH_TOKEN:
            return await call_next(request)
        path = request.url.path
        if path.endswith("/health") or path.rstrip("/").endswith("/api/health"):
            return await call_next(request)
        if path in {"/api/health", "/health"}:
            return await call_next(request)
        auth = request.headers.get("authorization") or ""
        token = request.headers.get("x-api-token") or ""
        expected = settings.UI_AUTH_TOKEN
        ok = (auth.lower().startswith("bearer ") and auth.split(" ", 1)[1] == expected) or (token == expected)
        if not ok:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)
