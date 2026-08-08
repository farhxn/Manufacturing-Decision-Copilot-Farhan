"""
Manufacturing Decision Copilot - FastAPI Application Entry Point
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.exceptions import AppHTTPException
from app.core.logging import configure_logging, get_logger
from app.database.chroma import get_chroma_client

# Configure structured logging before anything else
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown tasks."""
    # ── Startup ──────────────────────────────────────────
    logger.info(
        "Starting Manufacturing Decision Copilot",
        environment=settings.environment,
        version=settings.app_version,
    )

    # Ensure upload directory exists
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        logger.info("Storage directories ready", upload_dir=settings.upload_dir)
    except Exception as e:
        logger.warning("Storage directory creation skipped", error=str(e))

    # Initialize ChromaDB client (creates collection if needed)
    try:
        get_chroma_client()
        logger.info("ChromaDB initialized")
    except Exception as e:
        logger.warning("ChromaDB initialization deferred", error=str(e))

    yield

    # ── Shutdown ─────────────────────────────────────────
    logger.info("Manufacturing Decision Copilot shutting down")


# ── Application ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Manufacturing Decision Copilot",
    description=(
        "Evidence-backed manufacturing decision intelligence platform. "
        "Transforms fragmented supplier documents into transparent, "
        "explainable, and evidence-backed sourcing decisions."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(api_router)


@app.exception_handler(AppHTTPException)
async def app_http_exception_handler(request: Request, exc: AppHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = [f"{'.'.join(str(part) for part in error.get('loc', []))}: {error.get('msg')}" for error in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": details,
            },
        },
    )


# ── Global Error Handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler that returns a standard error envelope.
    Never exposes internal stack traces to the client.
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "details": [],
            },
        },
    )


# ── Root Redirect ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Manufacturing Decision Copilot API", "docs": "/docs"}
