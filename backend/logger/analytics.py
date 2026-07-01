# backend/logger/analytics.py
"""
AIKTC AI Chatbot — Analytics Classification
=============================================
Provides topic classification and department extraction
for the admin dashboard analytics.

Functions:
  - classify_topic()             : Classify a query into one of 10 topic categories
  - extract_query_departments()  : Extract department codes and return as JSON string
"""

import json
import logging
from typing import Optional

logger = logging.getLogger("aiktc.analytics")


def classify_topic(message: str, response_type: str) -> str:
    """
    Classify a user query into one of the predefined topic categories.

    Priority: response_type is the strongest signal; keyword scan
    is used as fallback for 'text' responses or when response_type is absent.

    Args:
        message       : The user's message text
        response_type : The response type from the LLM (e.g., 'text', 'table', 'prediction')

    Returns:
        str: One of: admission, cutoff, fee, lab, faculty, placement,
             hostel, process, contact, other
    """
    msg = message.lower()
    rt = (response_type or "").lower()

    # Response-type based classification (strongest signal)
    if rt in ("prediction", "multi_pred"):
        return "admission"

    if rt == "table":
        if "cutoff" in msg:
            return "cutoff"
        if "fee" in msg:
            return "fee"
        return "other"

    if rt == "faculty_grid":
        return "faculty"

    if rt == "list":
        if "lab" in msg:
            return "lab"
        return "other"

    if rt == "steps":
        return "process"

    if rt == "contact":
        return "contact"

    if rt == "comparison":
        if "fee" in msg:
            return "fee"
        return "other"

    # Keyword fallback for text responses or unknown types
    keywords = {
        "admission": ["chance", "milega", "eligible", "admission", "admit"],
        "cutoff":    ["cutoff", "cut off", "cut-off"],
        "fee":       ["fees", "₹", "fee", "cost", "fee structure"],
        "lab":       ["lab", "laboratory"],
        "faculty":   ["faculty", "hod", "teacher", "professor"],
        "placement": ["placement", "package", "recruiter", "placed"],
        "hostel":    ["hostel"],
        "process":   ["process", "procedure", "steps"],
        "contact":   ["contact", "phone", "email", "call"],
    }

    for topic, kws in keywords.items():
        if any(kw in msg for kw in kws):
            return topic

    return "other"


def extract_query_departments(
    message: str,
    response_type: str = "",
    llm_args: Optional[dict] = None,
) -> str:
    """
    Extract department codes from the user message and LLM function args.
    Returns a JSON array string suitable for database storage.

    Uses the existing engine extractor to ensure consistent alias mapping.

    Args:
        message       : The user's message text
        response_type : The response type from the LLM
        llm_args      : The function call arguments from the LLM (if any)

    Returns:
        str: JSON array string, e.g. '["CSE", "IT"]'
    """
    try:
        from engine.extractor import extract_departments
    except ImportError:
        logger.warning("Could not import extract_departments; returning empty list")
        return "[]"

    # Extract from message
    dept_set = set(extract_departments(message))

    # Extract from LLM function args if present
    if llm_args and isinstance(llm_args, dict):
        rt = (response_type or "").lower()

        # Single prediction: { "dept": "CSE", ... }
        if rt in ("prediction", "multi_pred"):
            dept_val = llm_args.get("dept")
            if dept_val and isinstance(dept_val, str):
                dept_set.add(dept_val.upper())

            # Multi prediction: { "predictions": [{"dept": "CSE"}, ...] }
            predictions = llm_args.get("predictions")
            if predictions and isinstance(predictions, list):
                for pred in predictions:
                    if isinstance(pred, dict):
                        d = pred.get("dept")
                        if d and isinstance(d, str):
                            dept_set.add(d.upper())

    return json.dumps(sorted(dept_set))
