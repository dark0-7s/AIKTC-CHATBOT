# backend/routes/health.py
"""
AIKTC AI Chatbot — Health Check Route
=======================================
Provides a /health endpoint for monitoring server status,
KB availability, and runtime statistics.
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, Request

logger = logging.getLogger("aiktc.health")

router = APIRouter(tags=["Health"])

# Track server start time for uptime calculation
_START_TIME = time.time()


@router.get(
    "/health",
    summary     = "Health check",
    description = "Returns server status, KB availability, and runtime statistics.",
)
async def health(request: Request):
    """
    Health check endpoint.
    Returns detailed server status for monitoring.
    """
    uptime_seconds = int(time.time() - _START_TIME)
    kb_loaded      = bool(getattr(request.app.state, "kb_markdown", ""))
    kb_size        = len(getattr(request.app.state, "kb_markdown", ""))

    try:
        from session.manager import get_active_session_count
        active_sessions = get_active_session_count()
    except Exception:
        active_sessions = -1

    return {
        "status"         : "healthy",
        "version"        : "1.0.0",
        "timestamp"      : datetime.utcnow().isoformat() + "Z",
        "uptime_seconds" : uptime_seconds,
        "kb_loaded"      : kb_loaded,
        "kb_size_chars"  : kb_size,
        "active_sessions": active_sessions,
    }