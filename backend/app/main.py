"""CRBCL Platform — FastAPI Main Application Entrypoint with CSRF Defense and Security Headers."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_v1_router
from app.auth.security import verify_csrf_token
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crbcl.api")

CSRF_EXEMPT_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/refresh",
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s in %s mode...", settings.app_name, settings.app_env)
    yield
    logger.info("Shutting down %s...", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Chief Red Bear Children's Lodge (CRBCL) Family Wellness Case Management Platform API",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS Middleware ──────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── CSRF & Security Headers Middleware ───────────────────
    @app.middleware("http")
    async def security_and_csrf_middleware(request: Request, call_next):
        # 1. State-changing CSRF defense for cookie-authenticated browser requests
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            path = request.url.path
            if path not in CSRF_EXEMPT_PATHS:
                auth_header = request.headers.get("Authorization", "")
                has_bearer = auth_header.startswith("Bearer ")

                # If request relies on cookie auth (no Bearer header) and has crbcl_access_token
                if not has_bearer and "crbcl_access_token" in request.cookies:
                    header_csrf = request.headers.get("X-CSRF-Token")
                    cookie_csrf = request.cookies.get("crbcl_csrf_token")
                    if not verify_csrf_token(header_csrf, cookie_csrf):
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={
                                "error": {
                                    "code": "CSRF_VERIFICATION_FAILED",
                                    "message": "Invalid or missing CSRF token in state-changing request",
                                    "details": {},
                                }
                            },
                        )

        response: Response = await call_next(request)

        # 2. Strict Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # ── Structured Error Handlers ────────────────────────────
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = {}
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
            errors[field or "request"] = err["msg"]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": errors,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact support.",
                    "details": {},
                }
            },
        )

    # ── Mount Routers ────────────────────────────────────────
    app.include_router(api_v1_router)

    return app


app = create_app()
