"""TeaSpoon FastAPI application entrypoint.

Wires routers, CORS (allow-listed origins only), security headers, and DB init.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .routers import contributions, dashboard, products, scan, settings as settings_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Seed an empty DB so a fresh checkout has data to scan against.
    from .seed import seed_if_empty

    seed_if_empty()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Know it in teaspoons, not grams. Daily nutrition tracking API.",
    lifespan=lifespan,
)

# CORS - when origins contains "*", credentials must be disabled (Starlette rule).
_is_wildcard = settings.cors_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=not _is_wildcard,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-User-Id"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Generic message to the client; full detail stays in server logs / Sentry.
    return JSONResponse(status_code=500, content={"detail": "Something went wrong."})


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "version": settings.version}


app.include_router(scan.router)
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(settings_router.router)
app.include_router(contributions.router)
