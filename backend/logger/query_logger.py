# backend/logger/query_logger.py
"""
AIKTC AI Chatbot — Query Logger
=================================
Database helpers for logging queries and retrieving QA data.

Provides:
  - log_query()            : Persist query + LLM response to DB
  - get_unresolved_queries(): Fetch unresolved/fallback queries
  - get_negative_feedback() : Fetch thumbs-down feedback entries
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Optional

from session.manager import get_connection

# ==============================================================================
# LOGGING
# ==============================================================================
logger = logging.getLogger("aiktc.query_logger")

# ==============================================================================
# CONSTANTS
# ==============================================================================
# Truncate raw LLM outputs to prevent DB bloat
MAX_RAW_LLM_OUTPUT = 50_000
DEFAULT_LIMIT       = 100
MAX_LIMIT           = 500


# ==============================================================================
# PRIVATE HELPERS
# ==============================================================================
def _truncate(value: Optional[str], max_len: int) -> Optional[str]:
    """Truncate a string to max_len characters if needed."""
    if value is None:
        return None
    if len(value) <= max_len:
        return value
    logger.debug(
        f"Truncating value from {len(value)} to {max_len} chars"
    )
    return value[:max_len]


def _sanitize_limit(limit: int) -> int:
    """Ensure limit is a valid positive integer within bounds."""
    if not isinstance(limit, int) or limit <= 0:
        return DEFAULT_LIMIT
    return min(limit, MAX_LIMIT)


def _fetch_rows(sql: str, params: tuple, limit: int) -> list[dict[str, Any]]:
    """
    Execute a SELECT query and return results as a list of dicts.

    Args:
        sql   : SQL query string with LIMIT ? placeholder at end
        params: Query parameters (excluding limit)
        limit : Maximum rows to return

    Returns:
        list[dict]: Query results

    Raises:
        sqlite3.DatabaseError: On database failure
    """
    safe_limit = _sanitize_limit(limit)
    try:
        conn = get_connection()
        cur  = conn.execute(sql, params + (safe_limit,))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except sqlite3.DatabaseError:
        logger.exception(f"DB error while fetching rows: {sql[:80]}")
        raise


# ==============================================================================
# PUBLIC API
# ==============================================================================
def log_query(
    session_id            : str,
    message               : str,
    response_type         : str,
    raw_llm_output        : Optional[str] = None,
    deterministic_context : Optional[str] = None,
    topic                 : str = "other",
    departments           : str = "[]",
) -> None:
    """
    Persist a user query and LLM response metadata to the queries table.

    Args:
        session_id            : Session identifier
        message               : User's message
        response_type         : Type of response generated (text, table, contact, etc.)
        raw_llm_output        : Full LLM response text (truncated if too long)
        deterministic_context : Context note passed to LLM
        topic                 : Classified topic for analytics
        departments           : JSON array of department codes

    Raises:
        ValueError          : If session_id or message is empty
        sqlite3.DatabaseError: On database failure
    """
    if not session_id or not session_id.strip():
        raise ValueError("session_id is required and cannot be empty")
    if not message or not message.strip():
        raise ValueError("message is required and cannot be empty")
    if not response_type:
        response_type = "unknown"

    # Truncate large outputs before storing
    raw_llm_output = _truncate(raw_llm_output, MAX_RAW_LLM_OUTPUT)

    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO queries
                (session_id, message, response_type, raw_llm_output, deterministic_context, topic, departments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, message.strip(), response_type, raw_llm_output, deterministic_context, topic, departments),
        )
        conn.commit()
        conn.close()
        logger.debug(
            f"Query logged | session={session_id[:8]} | type={response_type} | topic={topic}"
        )
    except sqlite3.DatabaseError:
        logger.exception(f"Failed to log query for session={session_id[:8]}")
        raise


def get_unresolved_queries(limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """
    Return recent queries that produced a plain text (unresolved) response.
    These are queries where the LLM couldn't match a structured function call.

    Args:
        limit: Maximum number of rows to return (max 500)

    Returns:
        list[dict]: Rows with keys: timestamp, message, response_type
    """
    sql = """
        SELECT timestamp, session_id, message, response_type
        FROM queries
        WHERE response_type = 'text'
        ORDER BY timestamp DESC
        LIMIT ?
    """
    return _fetch_rows(sql, (), limit)


def get_negative_feedback(limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """
    Return recent negative feedback entries (thumbs down, rating = -1).

    Args:
        limit: Maximum number of rows to return (max 500)

    Returns:
        list[dict]: Rows with keys: timestamp, session_id, rating, comment
    """
    sql = """
        SELECT timestamp, session_id, rating, comment
        FROM feedback
        WHERE rating = -1
        ORDER BY timestamp DESC
        LIMIT ?
    """
    return _fetch_rows(sql, (), limit)


def get_all_queries(limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """
    Return recent queries of all types.

    Args:
        limit: Maximum number of rows to return (max 500)

    Returns:
        list[dict]: Query rows
    """
    sql = """
        SELECT timestamp, session_id, message, response_type
        FROM queries
        ORDER BY timestamp DESC
        LIMIT ?
    """
    return _fetch_rows(sql, (), limit)