# backend/routes/admin.py
"""
AIKTC AI Chatbot — Admin Routes
=================================
Provides secured admin endpoints for:
  - Uploading knowledge base JSON files
  - Uploading cutoff CSV data
  - Reloading KB without server restart
  - Reviewing unresolved queries and negative feedback

Authentication:
  - Bearer token  : for upload and reload endpoints
  - HTTP Basic    : for review/dashboard endpoints
"""

from __future__ import annotations

import csv
import html
import io
import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)

from config import settings
from engine.verdict import reload_cutoffs
from kb.loader import load_and_merge_kb
from kb.markdown import kb_to_markdown
from logger.query_logger import get_negative_feedback, get_unresolved_queries
from admin import kb_editor

# ==============================================================================
# LOGGING
# ==============================================================================
logger = logging.getLogger("aiktc.admin")

# ==============================================================================
# ROUTER
# ==============================================================================
router = APIRouter(prefix="/admin", tags=["Admin"])

# ==============================================================================
# CONSTANTS
# ==============================================================================
SUPPORTED_SCHOOLS: frozenset[str] = frozenset({
    "common", "engineering", "pharmacy", "architecture"
})

REQUIRED_CUTOFF_COLUMNS: frozenset[str] = frozenset({
    "school", "branch", "category", "year", "cutoff", "cutoff_unit"
})

# ==============================================================================
# AUTHENTICATION
# ==============================================================================
bearer_scheme = HTTPBearer(auto_error=False)
basic_scheme  = HTTPBasic(auto_error=False)


def verify_bearer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> bool:
    """
    Verify Bearer token for upload and reload endpoints.
    Token must match settings.kb_reload_token.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Bearer token required",
            headers     = {"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != settings.kb_reload_token:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Invalid token",
            headers     = {"WWW-Authenticate": "Bearer"},
        )
    return True


def verify_basic_auth(
    credentials: Optional[HTTPBasicCredentials] = Depends(basic_scheme),
) -> bool:
    """
    Verify HTTP Basic Auth for review/dashboard endpoints.
    Credentials must match settings.admin_user and settings.admin_pass.
    """
    if not credentials:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Basic authentication required",
            headers     = {"WWW-Authenticate": "Basic"},
        )
    if (
        credentials.username != settings.admin_user
        or credentials.password != settings.admin_pass
    ):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Invalid credentials",
            headers     = {"WWW-Authenticate": "Basic"},
        )
    return True


# ==============================================================================
# HELPERS
# ==============================================================================
def _resolve_kb_path() -> Path:
    """Return the KB directory path, creating it if needed."""
    kb_path = settings.resolved_kb_path
    kb_path.mkdir(parents=True, exist_ok=True)
    return kb_path


def _reload_kb_markdown(request: Request) -> None:
    """Reload KB from disk and update app state."""
    merged = load_and_merge_kb(str(_resolve_kb_path()))
    request.app.state.kb_markdown = kb_to_markdown(merged)
    logger.info("KB markdown reloaded in app state")


def _get_db():
    """Return a SQLite connection for dashboard queries."""
    from session.manager import get_connection
    return get_connection()


def _render_review_page(title: str, rows: list[dict]) -> str:
    """
    Render a simple HTML page for reviewing queries/feedback.
    All content is HTML-escaped to prevent XSS.
    """
    if not rows:
        body = "<p>No records found.</p>"
    else:
        items = "".join(
            "<li>"
            f"<strong>{html.escape(str(row.get('timestamp', 'N/A')))}</strong> — "
            f"{html.escape(str(row.get('message', row.get('comment', 'N/A'))))} "
            f"→ <em>{html.escape(str(row.get('response_type', row.get('rating', 'N/A'))))}</em>"
            "</li>"
            for row in rows
        )
        body = f"<ul>{items}</ul>"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{html.escape(title)}</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
            h1   {{ color: #0a1f5c; border-bottom: 2px solid #2563c7; padding-bottom: 10px; }}
            li   {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
            strong {{ color: #555; }}
            em   {{ color: #2563c7; }}
        </style>
    </head>
    <body>
        <h1>{html.escape(title)}</h1>
        <p>Total records: {len(rows)}</p>
        {body}
    </body>
    </html>
    """


# ==============================================================================
# ROUTES
# ==============================================================================
@router.post(
    "/upload/kb",
    summary     = "Upload a knowledge base JSON file",
    description = "Upload a JSON file for a specific school (common/engineering/pharmacy/architecture). Requires Bearer token.",
)
async def upload_kb(
    request: Request,
    school : str,
    file   : UploadFile = File(...),
    _      : bool = Depends(verify_bearer),
):
    """
    Upload and replace a KB JSON file for a specific school.
    Automatically reloads the KB markdown in app state.
    """
    school = school.strip().lower()

    # Validate school name
    if school not in SUPPORTED_SCHOOLS:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = f"Invalid school '{school}'. Must be one of: {sorted(SUPPORTED_SCHOOLS)}",
        )

    # Validate file type
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "File must be a .json file",
        )

    # Read and parse JSON
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = f"Invalid JSON: {exc}",
        ) from exc

    # Validate structure for engineering
    if school == "engineering" and not isinstance(data, dict):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "Engineering KB must be a JSON object (dict), not a list.",
        )

    # Save to disk
    file_path = _resolve_kb_path() / f"{school}.json"
    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    logger.info(f"KB file uploaded: {school}.json | size={len(content)} bytes")

    # Reload app state
    _reload_kb_markdown(request)

    return {
        "status" : "ok",
        "message": f"{school}.json updated and reloaded successfully",
        "school" : school,
        "size"   : len(content),
    }


@router.post(
    "/upload/cutoffs",
    summary     = "Upload cutoff CSV data",
    description = "Upload a CSV file with cutoff data. Requires Bearer token.",
)
async def upload_cutoffs(
    file: UploadFile = File(...),
    _   : bool = Depends(verify_bearer),
):
    """
    Upload and replace the cutoffs CSV file.
    Validates required columns before saving.
    """
    # Validate file type
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "File must be a .csv file",
        )

    content = await file.read()

    # Validate CSV structure
    try:
        decoded = content.decode("utf-8")
        reader  = csv.DictReader(io.StringIO(decoded))
        columns = frozenset(c.strip() for c in (reader.fieldnames or []))
        missing = REQUIRED_CUTOFF_COLUMNS - columns
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "File must be UTF-8 encoded",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = f"Invalid CSV: {exc}",
        )

    # Save to disk
    file_path = _resolve_kb_path() / "cutoffs.csv"
    file_path.write_text(decoded, encoding="utf-8")
    logger.info(f"Cutoffs CSV uploaded | size={len(content)} bytes")

    # Reload cutoff cache
    reload_cutoffs(file_path)

    return {
        "status" : "ok",
        "message": "cutoffs.csv updated and cache reloaded successfully",
        "size"   : len(content),
    }


@router.post(
    "/reload-kb",
    summary     = "Reload knowledge base from disk",
    description = "Force reload KB markdown without restarting the server. Requires Bearer token.",
)
async def reload_kb(
    request: Request,
    _      : bool = Depends(verify_bearer),
):
    """Reload the KB markdown and cutoff cache from disk."""
    _reload_kb_markdown(request)
    reload_cutoffs(_resolve_kb_path() / "cutoffs.csv")
    logger.info("Admin triggered full KB reload")
    return {"status": "ok", "message": "Knowledge base and cutoffs reloaded"}


# ==============================================================================
# KB EDITOR ROUTES
# ==============================================================================
class KBFileWriteRequest(BaseModel):
    path: str
    content: str


@router.get(
    "/kb/tree",
    summary     = "Get KB directory tree",
    description = "Returns a nested JSON tree of the KB directory. Requires Basic Auth.",
)
async def get_kb_tree(_: bool = Depends(verify_basic_auth)):
    return {"tree": kb_editor.build_tree()}


@router.get(
    "/kb/file",
    summary     = "Read KB file content",
    description = "Returns the content and metadata of a KB file. Requires Basic Auth.",
)
async def get_kb_file(path: str, _: bool = Depends(verify_basic_auth)):
    try:
        return kb_editor.read_file(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error reading file {path}: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/kb/file",
    summary     = "Write KB file content",
    description = "Writes content to a KB file and triggers reload. Requires Basic Auth.",
)
async def write_kb_file(req: KBFileWriteRequest, request: Request, _: bool = Depends(verify_basic_auth)):
    try:
        if req.path.endswith(".json"):
            # Syntax validation
            json.loads(req.content)
            
        elif req.path.endswith("cutoffs.csv"):
            # Syntax validation for cutoffs
            reader = csv.DictReader(io.StringIO(req.content))
            columns = frozenset(c.strip() for c in (reader.fieldnames or []))
            missing = REQUIRED_CUTOFF_COLUMNS - columns
            if missing:
                raise ValueError(f"Missing required columns: {sorted(missing)}")
                
        kb_editor.write_file(req.path, req.content)
        
        # Trigger reload if successful
        _reload_kb_markdown(request)
        if req.path.endswith("cutoffs.csv"):
            reload_cutoffs(_resolve_kb_path() / "cutoffs.csv")
            
        return {"status": "ok", "message": f"{req.path} saved successfully."}
        
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error writing file {req.path}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


class KBFolderCreateRequest(BaseModel):
    parent: str
    name: str

class KBDeleteRequest(BaseModel):
    path: str

@router.post(
    "/kb/delete",
    summary     = "Delete KB file or empty folder",
    description = "Deletes a file or an empty folder and triggers reload. Requires Basic Auth.",
)
async def delete_kb_file(req: KBDeleteRequest, request: Request, _: bool = Depends(verify_basic_auth)):
    try:
        kb_editor.safe_delete(req.path)
        # Trigger reload if successful
        _reload_kb_markdown(request)
        if req.path.endswith("cutoffs.csv"):
            reload_cutoffs(_resolve_kb_path() / "cutoffs.csv")
            
        return {"status": "ok", "message": f"{req.path} deleted successfully."}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error deleting path {req.path}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/kb/create_folder",
    summary     = "Create new KB folder",
    description = "Creates a new folder inside a parent directory. Requires Basic Auth.",
)
async def create_kb_folder(req: KBFolderCreateRequest, _: bool = Depends(verify_basic_auth)):
    try:
        kb_editor.safe_create_folder(req.parent, req.name)
        return {"status": "ok", "message": f"Folder {req.name} created successfully."}
    except FileExistsError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error creating folder {req.name}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/kb/upload",
    summary     = "Upload KB file",
    description = "Accepts a raw file upload to a specific folder and triggers reload. Requires Basic Auth.",
)
async def upload_kb_file(
    request: Request,
    folder: str = Form(""),
    file: UploadFile = File(...),
    _: bool = Depends(verify_basic_auth)
):
    try:
        if not file.filename:
            raise ValueError("No filename provided")
            
        target_path = f"{folder.strip('/')}/{file.filename}" if folder.strip('/') else file.filename
        
        # Read content
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8")
        
        # Validation
        if target_path.endswith(".json"):
            json.loads(content)
        elif target_path.endswith("cutoffs.csv"):
            reader = csv.DictReader(io.StringIO(content))
            columns = frozenset(c.strip() for c in (reader.fieldnames or []))
            missing = REQUIRED_CUTOFF_COLUMNS - columns
            if missing:
                raise ValueError(f"Missing required columns: {sorted(missing)}")
                
        # Write file
        kb_editor.write_file(target_path, content)
        
        # Trigger reload
        _reload_kb_markdown(request)
        if target_path.endswith("cutoffs.csv"):
            reload_cutoffs(_resolve_kb_path() / "cutoffs.csv")
            
        return {"status": "ok", "message": f"{target_path} uploaded successfully."}
        
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error uploading file {getattr(file, 'filename', 'unknown')}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/review/unresolved",
    response_class = HTMLResponse,
    summary        = "View unresolved / fallback queries",
    description    = "HTML page showing queries that triggered fallback responses. Requires Basic Auth.",
)
async def review_unresolved(
    _: bool = Depends(verify_basic_auth),
) -> HTMLResponse:
    """Show unresolved queries in a simple HTML page."""
    queries = get_unresolved_queries()
    return HTMLResponse(
        content = _render_review_page("Unresolved / Fallback Queries", queries)
    )


@router.get(
    "/review/feedback",
    response_class = HTMLResponse,
    summary        = "View negative feedback",
    description    = "HTML page showing thumbs-down feedback entries. Requires Basic Auth.",
)
async def review_feedback(
    _: bool = Depends(verify_basic_auth),
) -> HTMLResponse:
    """Show negative feedback in a simple HTML page."""
    feedbacks = get_negative_feedback()
    return HTMLResponse(
        content = _render_review_page("Negative Feedback", feedbacks)
    )


@router.get(
    "/stats",
    summary     = "Get query and feedback statistics",
    description = "Returns aggregated stats for admin dashboard. Requires Bearer token.",
)
async def get_stats(_: bool = Depends(verify_bearer)):
    """Return aggregated query and feedback statistics."""
    from session.manager import get_query_stats, get_feedback_stats, get_active_session_count
    return {
        "queries" : get_query_stats(),
        "feedback": get_feedback_stats(),
        "active_sessions": get_active_session_count(),
    }


# ==============================================================================
# DASHBOARD — Serve HTML
# ==============================================================================
@router.get(
    "/dashboard",
    response_class = HTMLResponse,
    summary        = "Admin Dashboard",
    description    = "Serves the admin dashboard single-page application. Requires Basic Auth.",
)
async def dashboard_page(
    _: bool = Depends(verify_basic_auth),
):
    """Serve the admin dashboard HTML page with injected config."""
    dashboard_path = Path(__file__).parent.parent / "admin_dashboard" / "index.html"
    if not dashboard_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard HTML file not found",
        )
    html = dashboard_path.read_text(encoding="utf-8")
    # Inject bearer token for KB upload/reload endpoints
    meta_tag = f'<meta name="kb-token" content="{settings.kb_reload_token}">'
    html = html.replace("</head>", f"  {meta_tag}\n</head>", 1)
    return HTMLResponse(content=html)


# ==============================================================================
# DASHBOARD API — Stats
# ==============================================================================
@router.get(
    "/dashboard/stats",
    summary     = "Dashboard overview statistics",
    description = "Returns card data: today count, 7-day count, active sessions, negative feedback, top response types.",
)
async def dashboard_stats(
    _: bool = Depends(verify_basic_auth),
):
    """Return overview card numbers for the admin dashboard."""
    conn = _get_db()
    try:
        total_today = conn.execute(
            "SELECT COUNT(*) FROM queries WHERE timestamp >= date('now')"
        ).fetchone()[0]

        total_7_days = conn.execute(
            "SELECT COUNT(*) FROM queries WHERE timestamp >= date('now', '-7 days')"
        ).fetchone()[0]

        top_types_rows = conn.execute(
            "SELECT response_type, COUNT(*) AS count FROM queries "
            "WHERE timestamp >= date('now', '-30 days') "
            "GROUP BY response_type ORDER BY count DESC LIMIT 5"
        ).fetchall()
        top_response_types = [
            {"type": row[0] or "unknown", "count": row[1]} for row in top_types_rows
        ]

        negative_feedback_count = conn.execute(
            "SELECT COUNT(*) FROM feedback WHERE rating = -1 AND timestamp >= date('now')"
        ).fetchone()[0]

        active_sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM queries "
            "WHERE timestamp >= datetime('now', '-1 hour')"
        ).fetchone()[0]
    finally:
        conn.close()

    return {
        "total_today": total_today,
        "total_last_7_days": total_7_days,
        "top_response_types": top_response_types,
        "negative_feedback_count": negative_feedback_count,
        "active_sessions_last_hour": active_sessions,
    }


# ==============================================================================
# DASHBOARD API — Topics
# ==============================================================================
ALL_TOPICS = [
    "admission", "cutoff", "fee", "lab", "faculty",
    "placement", "hostel", "process", "contact", "other"
]


@router.get(
    "/dashboard/topics",
    summary     = "Topic distribution, hot departments, and daily trends",
    description = "Returns analytics data for charts. Accepts ?days=30 parameter.",
)
async def dashboard_topics(
    days: int = 30,
    _: bool = Depends(verify_basic_auth),
):
    """Return topic breakdown, hot departments, and daily trend data for charts."""
    if days < 1:
        days = 30
    if days > 365:
        days = 365

    conn = _get_db()
    try:
        # --- Topic distribution ---
        topic_rows = conn.execute(
            "SELECT topic, COUNT(*) AS count FROM queries "
            "WHERE timestamp >= date('now', ? || ' days') GROUP BY topic",
            (f"-{days}",),
        ).fetchall()
        topics = {t: 0 for t in ALL_TOPICS}
        for row in topic_rows:
            key = row[0] or "other"
            if key in topics:
                topics[key] += row[1]
            else:
                topics["other"] += row[1]

        # --- Hot departments ---
        dept_rows = conn.execute(
            "SELECT departments FROM queries "
            "WHERE timestamp >= date('now', ? || ' days') AND departments IS NOT NULL AND departments != '[]'",
            (f"-{days}",),
        ).fetchall()
        dept_counts: dict[str, int] = {}
        for row in dept_rows:
            try:
                codes = json.loads(row[0])
                if isinstance(codes, list):
                    for code in codes:
                        dept_counts[code] = dept_counts.get(code, 0) + 1
            except (json.JSONDecodeError, TypeError):
                continue
        hot_departments = sorted(
            [{"dept": k, "count": v} for k, v in dept_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:5]

        # --- Daily trends ---
        trend_rows = conn.execute(
            "SELECT date(timestamp) AS day, topic, COUNT(*) AS count FROM queries "
            "WHERE timestamp >= date('now', ? || ' days') "
            "GROUP BY day, topic ORDER BY day ASC",
            (f"-{days}",),
        ).fetchall()
        daily_map: dict[str, dict[str, int]] = {}
        for row in trend_rows:
            day = row[0]
            topic_key = row[1] or "other"
            if day not in daily_map:
                daily_map[day] = {t: 0 for t in ALL_TOPICS}
            if topic_key in daily_map[day]:
                daily_map[day][topic_key] += row[2]
            else:
                daily_map[day]["other"] += row[2]
        daily_trends = [
            {"date": day, **counts} for day, counts in sorted(daily_map.items())
        ]
    finally:
        conn.close()

    return {
        "topics": topics,
        "hot_departments": hot_departments,
        "daily_trends": daily_trends,
    }


# ==============================================================================
# DASHBOARD API — Query Log
# ==============================================================================
@router.get(
    "/dashboard/queries",
    summary     = "Paginated query log with filtering",
    description = "Returns filtered, paginated query log entries.",
)
async def dashboard_queries(
    page: int = 1,
    per_page: int = 50,
    response_type: Optional[str] = None,
    topic: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    _: bool = Depends(verify_basic_auth),
):
    """Return paginated query log with optional filters."""
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 50
    if per_page > 200:
        per_page = 200

    conditions = []
    params: list = []

    if response_type:
        conditions.append("response_type = ?")
        params.append(response_type)
    if topic:
        conditions.append("topic = ?")
        params.append(topic)
    if date_from:
        conditions.append("timestamp >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("timestamp <= ? || ' 23:59:59'")
        params.append(date_to)
    if search:
        conditions.append("message LIKE ?")
        params.append(f"%{search}%")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    conn = _get_db()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM queries {where_clause}", params
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT id, timestamp, session_id, message, response_type, topic, departments, "
            f"deterministic_context, raw_llm_output "
            f"FROM queries {where_clause} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()
    finally:
        conn.close()

    data = []
    for row in rows:
        data.append({
            "id": row[0],
            "timestamp": row[1],
            "session_id": row[2],
            "message": row[3],
            "response_type": row[4],
            "topic": row[5],
            "departments": row[6],
            "deterministic_context": row[7],
            "raw_llm_output": row[8],
        })

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "data": data,
    }


# ==============================================================================
# DASHBOARD API — Feedback
# ==============================================================================
@router.get(
    "/dashboard/feedback",
    summary     = "Negative feedback entries",
    description = "Returns recent negative feedback with conversation snippets.",
)
async def dashboard_feedback(
    _: bool = Depends(verify_basic_auth),
):
    """Return last 100 negative feedback entries."""
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT f.id, f.timestamp, f.session_id, f.rating, f.comment, "
            "f.conversation_snippet "
            "FROM feedback f "
            "WHERE f.rating = -1 "
            "ORDER BY f.id DESC LIMIT 100"
        ).fetchall()
    finally:
        conn.close()

    data = []
    for row in rows:
        data.append({
            "id": row[0],
            "timestamp": row[1],
            "session_id": row[2],
            "rating": row[3],
            "comment": row[4],
            "conversation_snippet": row[5],
        })

    return {"data": data}