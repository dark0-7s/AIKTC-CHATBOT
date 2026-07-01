# backend/session/manager.py
"""
AIKTC AI Chatbot — Session Manager
====================================
Manages conversation sessions, history trimming,
anchor logic, query logging, and feedback storage
using SQLite as the persistent backend.

Tables:
  sessions  — Stores conversation history and anchor per session
  queries   — Logs every query for analytics
  feedback  — Stores user thumbs up/down feedback

Anchor Logic:
  An "anchor" is the most recent admission-signal message from the user.
  It is prepended to trimmed history so the LLM always has context
  about what branch/percentile/category the student is asking about.
  The anchor is released when:
    - A verdict (high/medium/low chance) has been presented
    - No admission signals found in last 6 user turns
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from config import settings

# ==============================================================================
# LOGGING
# ==============================================================================
logger = logging.getLogger("aiktc.session")

# ==============================================================================
# DATABASE PATH — Created on module load
# ==============================================================================
DB_PATH = settings.resolved_database_path
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# CONSTANTS
# ==============================================================================
MAX_HISTORY_TURNS  = 8    # Max turns kept in trimmed history
ANCHOR_RELEASE_TURNS = 6  # No-signal turns before anchor is released
# Words in bot response that indicate a verdict was given (high, medium, low)
VERDICT_SIGNALS = {"high", "medium", "low"}
# CONNECTION
# ==============================================================================
def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite connection with Row factory enabled.
    Row factory allows accessing columns by name (row["column_name"]).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # Better concurrent write performance
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ==============================================================================
# INITIALIZATION
# ==============================================================================
def init_db() -> None:
    """
    Initialize the SQLite database.
    Creates all tables and indexes if they do not already exist.
    Safe to call multiple times (idempotent).
    """
    conn = get_connection()
    try:
        conn.executescript("""
            -- Sessions table: stores conversation history and anchor
            CREATE TABLE IF NOT EXISTS sessions (
                session_id  TEXT    PRIMARY KEY,
                history     TEXT    NOT NULL DEFAULT '[]',
                anchor      TEXT    DEFAULT NULL,
                created_at  INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at  INTEGER DEFAULT (strftime('%s', 'now'))
            );

            -- Queries table: logs every query for analytics
            CREATE TABLE IF NOT EXISTS queries (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp             TEXT    DEFAULT (datetime('now')),
                session_id            TEXT,
                message               TEXT,
                response_type         TEXT,
                raw_llm_output        TEXT,
                deterministic_context TEXT,
                topic                 TEXT,
                departments           TEXT
            );

            -- Feedback table: stores user thumbs up/down
            CREATE TABLE IF NOT EXISTS feedback (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp            TEXT    DEFAULT (datetime('now')),
                session_id           TEXT,
                rating               INTEGER CHECK(rating IN (1, -1)),
                comment              TEXT,
                conversation_snippet TEXT
            );

            -- Indexes for fast lookups
            CREATE INDEX IF NOT EXISTS idx_queries_response_type
                ON queries(response_type);
            CREATE INDEX IF NOT EXISTS idx_queries_session
                ON queries(session_id);
            CREATE INDEX IF NOT EXISTS idx_queries_timestamp
                ON queries(timestamp);
            CREATE INDEX IF NOT EXISTS idx_queries_topic
                ON queries(topic);
            CREATE INDEX IF NOT EXISTS idx_feedback_rating
                ON feedback(rating);
            CREATE INDEX IF NOT EXISTS idx_feedback_session
                ON feedback(session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_updated
                ON sessions(updated_at);
        """)
        conn.commit()
        logger.info(f"Database initialized: {DB_PATH}")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()


# ==============================================================================
# SESSION CRUD
# ==============================================================================
def load_session(session_id: str) -> dict:
    """
    Load session data for a given session ID.
    Returns default empty state if session does not exist.

    Args:
        session_id: Unique session identifier

    Returns:
        dict: {history: list, anchor: dict | None}
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT history, anchor FROM sessions WHERE session_id = ?",
            (session_id,)
        ).fetchone()

    if row is None:
        return {"history": [], "anchor": None}

    try:
        history = json.loads(row["history"])
    except json.JSONDecodeError:
        logger.warning("Malformed stored history for session %s; resetting", session_id)
        history = []

    anchor_json = row["anchor"]
    anchor = None
    if anchor_json:
        try:
            anchor = json.loads(anchor_json)
        except json.JSONDecodeError:
            logger.warning("Malformed stored anchor for session %s; dropping", session_id)
            anchor = None

    return {"history": history, "anchor": anchor}


def save_session(
    session_id: str,
    history   : list,
    anchor    : Optional[dict],
    is_type_a : bool = False
) -> None:
    """
    Save session data after trimming history and updating anchor.

    Steps:
      1. Trim history to MAX_HISTORY_TURNS
      2. Ensure anchor message is present in trimmed history
      3. Update anchor based on latest signals
      4. Persist to SQLite

    Args:
        session_id: Unique session identifier
        history   : Full conversation history list
        anchor    : Current anchor dict or None
        is_type_a : True if the current engine execution was Type A
    """
    trimmed_history = trim_history(history, anchor)
    new_anchor = update_anchor(trimmed_history, anchor, is_type_a)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, history, anchor, updated_at)
            VALUES (?, ?, ?, strftime('%s', 'now'))
            ON CONFLICT(session_id) DO UPDATE SET
                history    = excluded.history,
                anchor     = excluded.anchor,
                updated_at = excluded.updated_at
            """,
            (
                session_id,
                json.dumps(trimmed_history),
                json.dumps(new_anchor) if new_anchor else None,
            ),
        )
        conn.commit()

    logger.debug("Session saved | id=%s | turns=%d", session_id[:8], len(trimmed_history))


def delete_session(session_id: str) -> bool:
    """
    Delete a session permanently from the database.
    Used when user clicks 'New Chat'.

    Args:
        session_id: Session to delete

    Returns:
        bool: True if deleted, False if not found
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        deleted = cursor.rowcount > 0

    if deleted:
        logger.info("Session deleted: %s", session_id[:8])
    return deleted


# ==============================================================================
# QUERY LOGGING
# ==============================================================================
def log_query(
    session_id            : str,
    message               : str,
    response_type         : str,
    raw_llm_output        : str,
    deterministic_context : str = "",
    topic                 : str = "other",
    departments           : str = "[]"
) -> None:
    """
    Log a query to the queries table for analytics.

    Args:
        session_id            : Session identifier
        message               : User's message
        response_type         : Type of response generated
        raw_llm_output        : Full LLM response text
        deterministic_context : Context passed to LLM (optional)
        topic                 : Classified topic for analytics
        departments           : JSON array of department codes
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO queries
                (session_id, message, response_type, raw_llm_output, deterministic_context, topic, departments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, message, response_type, raw_llm_output, deterministic_context, topic, departments),
        )
        conn.commit()


# ==============================================================================
# FEEDBACK
# ==============================================================================
def save_feedback(
    session_id           : str,
    rating               : int,
    comment              : str = "",
    conversation_snippet : str = ""
) -> None:
    """
    Save user feedback (thumbs up = 1, thumbs down = -1).

    Args:
        session_id           : Session identifier
        rating               : 1 (positive) or -1 (negative)
        comment              : Optional text comment
        conversation_snippet : Last few messages for context
    """
    if rating not in (1, -1):
        logger.warning(f"Invalid rating value: {rating}. Must be 1 or -1.")
        return

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO feedback
                (session_id, rating, comment, conversation_snippet)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, rating, comment, conversation_snippet),
        )
        conn.commit()
        logger.debug(f"Feedback saved | session={session_id[:8]} | rating={rating}")
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
    finally:
        conn.close()


# ==============================================================================
# ADMIN QUERIES
# ==============================================================================
def get_query_stats() -> dict:
    """
    Return aggregated query statistics for the admin dashboard.

    Returns:
        dict: {total, by_type, recent}
    """
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]

        by_type = conn.execute(
            "SELECT response_type, COUNT(*) as count "
            "FROM queries GROUP BY response_type ORDER BY count DESC"
        ).fetchall()

        recent = conn.execute(
            "SELECT timestamp, session_id, message, response_type "
            "FROM queries ORDER BY id DESC LIMIT 20"
        ).fetchall()

    return {
        "total"  : total,
        "by_type": [dict(r) for r in by_type],
        "recent" : [dict(r) for r in recent],
    }


def get_feedback_stats() -> dict:
    """
    Return feedback statistics for the admin dashboard.

    Returns:
        dict: {total, positive, negative, recent}
    """
    with get_connection() as conn:
        total    = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        positive = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating = 1").fetchone()[0]
        negative = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating = -1").fetchone()[0]

        recent = conn.execute(
            "SELECT timestamp, session_id, rating, comment "
            "FROM feedback ORDER BY id DESC LIMIT 20"
        ).fetchall()

    return {
        "total"   : total,
        "positive": positive,
        "negative": negative,
        "recent"  : [dict(r) for r in recent],
    }


def get_active_session_count() -> int:
    """Return count of sessions active in the last 30 minutes."""
    with get_connection() as conn:
        threshold = "strftime('%s','now') - 1800"
        count = conn.execute(
            f"SELECT COUNT(*) FROM sessions WHERE updated_at >= ({threshold})"
        ).fetchone()[0]
    return count


# ==============================================================================
# PRIVATE — History Trimming
# ==============================================================================
def trim_history(history: list, anchor: Optional[dict]) -> list:
    """
    Trim history to MAX_HISTORY_TURNS.
    If anchor exists and is not in trimmed history, prepend it
    so the LLM always has the original admission context.

    Args:
        history: Full conversation history
        anchor : Current anchor dict or None

    Returns:
        list: Trimmed history with anchor prepended if needed
    """
    trimmed = history[-MAX_HISTORY_TURNS:]

    if anchor is None:
        return trimmed

    anchor_content = anchor.get("content", "")
    anchor_present = any(
        t.get("role") == "user" and t.get("content") == anchor_content
        for t in trimmed
    )

    if not anchor_present:
        trimmed = [{"role": "user", "content": anchor_content}] + trimmed

    return trimmed


# ==============================================================================
# PRIVATE — Anchor Management
# ==============================================================================
def update_anchor(
    history        : list,
    current_anchor : Optional[dict],
    is_type_a      : bool = False
) -> Optional[dict]:
    """
    Update the session anchor based on conversation state.

    Release anchor if:
      - Bot has presented a verdict in last 4 turns and context was Type-A
      - No admission signals found in last ANCHOR_RELEASE_TURNS user turns

    Set new anchor if:
      - Found a user turn with admission signals

    Args:
        history        : Trimmed conversation history
        current_anchor : Current anchor or None
        is_type_a      : True if the current engine execution was Type A
    """
    from engine.aliases import ADMISSION_SIGNALS

    user_turns = [t for t in history if t.get("role") == "user"]
    bot_turns  = [t for t in history[-4:] if t.get("role") == "assistant"]

    # -- Release if verdict was presented --
    if current_anchor and is_type_a:
        for bot in bot_turns:
            content = bot.get("content", "").lower()
            if any(signal in content for signal in VERDICT_SIGNALS):
                logger.debug("Anchor released — verdict presented")
                return None

    # -- Find newest admission signal in user turns --
    new_anchor = None
    for turn in reversed(user_turns):
        if any(signal in turn["content"].lower() for signal in ADMISSION_SIGNALS):
            new_anchor = {"content": turn["content"]}
            break

    # -- Release after too many no-signal turns --
    if current_anchor and new_anchor is None:
        recent_turns = user_turns[-ANCHOR_RELEASE_TURNS:]
        has_signal   = any(
            any(signal in t["content"].lower() for signal in ADMISSION_SIGNALS)
            for t in recent_turns
        )
        if not has_signal:
            logger.debug("Anchor released — no admission signals in recent turns")
            return None

    return new_anchor