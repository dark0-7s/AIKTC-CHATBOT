# backend/main.py
"""
AIKTC AI Chatbot — FastAPI Application Entry Point
===================================================
Initializes the FastAPI app, middleware, routes,
knowledge base, and database on startup.
"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import settings
from kb.loader import load_and_merge_kb
from kb.markdown import kb_to_markdown
from routes import admin, chat, health
from session.manager import init_db

# ==============================================================================
# LOGGING
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("aiktc.main")


# ==============================================================================
# RATE LIMITER
# ==============================================================================
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


# ==============================================================================
# LIFESPAN — Startup & Shutdown
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.

    Startup:
      - Initialize SQLite database (creates tables if not exist)
      - Load and merge all knowledge base JSON files
      - Convert merged KB to markdown for LLM context window
      - Store KB markdown in app state for reuse across requests

    Shutdown:
      - Log shutdown message
    """
    logger.info("=" * 60)
    logger.info("  AIKTC AI Chatbot — Starting Up")
    logger.info("=" * 60)

    # Validate Gemini API key
    if not settings.gemini_api_key:
        logger.error(
            "GEMINI_API_KEY is not set! "
            "Add it to your .env file and restart."
        )

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Rate limit configuration for routes
    app.state.rate_limit = settings.rate_limit_per_minute

    # Load knowledge base
    try:
        kb_path = settings.resolved_kb_path
        merged = load_and_merge_kb(kb_path)
        app.state.kb_markdown = kb_to_markdown(merged)
        logger.info(
            f"Knowledge base loaded | "
            f"size={len(app.state.kb_markdown)} chars | "
            f"path={kb_path}"
        )
    except Exception as e:
        logger.error(f"Knowledge base loading failed: {e}")
        app.state.kb_markdown = ""

    logger.info("Server ready — http://localhost:8000")
    logger.info("API docs — http://localhost:8000/docs")
    logger.info("=" * 60)

    yield  # Application runs here

    logger.info("AIKTC AI Chatbot — Shutting down")


# ==============================================================================
# FASTAPI APP
# ==============================================================================
app = FastAPI(
    title="AIKTC AI Admission Chatbot",
    description=(
        "Intelligent AI chatbot for AIKTC college website.\n\n"
        "Handles student queries about:\n"
        "- Admission process, cutoffs, fees, eligibility\n"
        "- Departments, faculty, labs, placements\n"
        "- College facilities and general information\n\n"
        "Supports English and Hinglish."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ==============================================================================
# RATE LIMITING
# ==============================================================================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==============================================================================
# CORS MIDDLEWARE
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


# ==============================================================================
# REQUEST LOGGING MIDDLEWARE
# ==============================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request with method, path, and response status."""
    import time
    start = time.time()
    response = await call_next(request)
    ms = int((time.time() - start) * 1000)
    logger.info(
        f"{request.method:6} {request.url.path} | "
        f"status={response.status_code} | {ms}ms"
    )
    return response


# ==============================================================================
# GLOBAL EXCEPTION HANDLER
# ==============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return a clean error response."""
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "path": str(request.url.path),
        },
    )


# ==============================================================================
# ROUTES
# ==============================================================================
app.include_router(chat.router)
app.include_router(chat.router, prefix="/api")
app.include_router(admin.router)
app.include_router(admin.router, prefix="/api")
app.include_router(health.router)
app.include_router(health.router, prefix="/api")


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )