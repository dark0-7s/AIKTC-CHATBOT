from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
from datetime import datetime

router = APIRouter(prefix="/feedback", tags=["Feedback"])

# Path to feedback.json
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "feedback.json"


class FeedbackRequest(BaseModel):
    session_id: str | None = None
    chat_id: str | None = None
    message_id: str | None = None

    question: str = ""
    answer: str = ""

    rating: str | int = "positive"
    reason: str = ""
    comment: str = ""


def load_feedback():
    if not DATA_FILE.exists():
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
def save_feedback(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("SAVE ERROR:", e)
        raise


@router.post("/")
def submit_feedback(payload: FeedbackRequest):

    feedback = load_feedback()

    feedback.append({
        "id": len(feedback) + 1,
        "session_id": payload.session_id,
        "chat_id": payload.chat_id,
        "message_id": payload.message_id,

        "question": payload.question,
        "answer": payload.answer,

        "rating": payload.rating,
        "reason": payload.reason,
        "comment": payload.comment,

        "created_at": datetime.now().isoformat()
    })

    save_feedback(feedback)

    # Synchronize to SQLite feedback table
    try:
        from session.manager import get_connection
        conn = get_connection()
        int_rating = 1 if payload.rating in ("helpful", "positive", 1, "1") else -1
        full_comment = f"[{payload.reason}] {payload.comment}" if payload.reason else payload.comment
        conn.execute(
            """
            INSERT INTO feedback (session_id, rating, comment, conversation_snippet)
            VALUES (?, ?, ?, ?)
            """,
            (payload.session_id or "", int_rating, full_comment, payload.question or payload.answer or "")
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("SQLite Feedback sync error:", e)

    return {
        "success": True,
        "message": "Feedback saved successfully."
    }


@router.get("/")
def get_feedback():
    return load_feedback()