# backend/engine/extractor.py
import re
from .aliases import (
    DEPARTMENT_ALIASES, CATEGORY_ALIASES,
    ADMISSION_SIGNALS, LOOKUP_WORDS
)
from .classifier import (
    classify_number, RE_PERCENTILE, RE_RANK,
    RE_MARKS, RE_LAKH, RE_COMMA_NUM,
    RE_LARGE_INT, RE_SMALL_NUM
)

# Devanagari digit equivalents (normalize before extraction)
DEVANAGARI_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

RE_PERCENTILE_KEYWORD = re.compile(r'\b(?:percentile|percent|pratishat|pct|%)\b', re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Replace Devanagari digits with ASCII digits."""
    for dev, ascii_ in DEVANAGARI_DIGITS.items():
        text = text.replace(dev, ascii_)
    return text


def extract_departments(text: str) -> list[str]:
    """
    Extract canonical department codes from text.
    Only searches within the given text — never called on history.
    Returns list of unique canonical codes (e.g., ["CSE", "IT"]).
    """
    text_lower = normalize_text(text).lower()
    found = []
    for code, aliases in DEPARTMENT_ALIASES.items():
        if any(alias in text_lower for alias in aliases):
            if code not in found:
                found.append(code)
    return found


def extract_category(text: str) -> str | None:
    """
    Extract canonical category from text.
    Returns canonical key ("Open", "OBC", etc.) or None.
    """
    text_lower = normalize_text(text).lower()
    for category, aliases in CATEGORY_ALIASES.items():
        if any(alias in text_lower for alias in aliases):
            return category
    return None


def filter_relevant_history(user_turns: list[dict]) -> list[dict]:
    """
    From the list of user turns (role="user" only), keep only those
    that contain at least one ADMISSION_SIGNAL word.
    
    IMPORTANT: "cutoff" is not in ADMISSION_SIGNALS — cutoff queries
    do not cause turns to be retained (prevents contamination).
    
    Args:
        user_turns: List of {"role": "user", "content": str}
    Returns:
        Filtered list of user turns
    """
    relevant = []
    for turn in user_turns:
        text_lower = normalize_text(turn["content"]).lower()
        has_category = any(
            any(alias in text_lower for alias in aliases)
            for aliases in CATEGORY_ALIASES.values()
        )
        if has_category or any(signal in text_lower for signal in ADMISSION_SIGNALS):
            relevant.append(turn)
    return relevant


def is_false_positive(raw_val: str, match_start: int, match_end: int, text: str) -> bool:
    """
    Identify if a match is a false positive year (e.g., 2024 in 'Placements 2024')
    or an ordinal (e.g., 12 in '12th class') rather than an admissions score.
    """
    suffix = text[match_end:match_end+15].lower()
    
    # Year or class suffixes
    year_suffixes = ["year", "saal", "class", "std", "grade", "साल", "कक्षा", "वीं", "वी"]
    for s in year_suffixes:
        if s in suffix:
            # If "percentile", "percent" or "%" is also present, it's likely a real score.
            if "percentile" in suffix or "percent" in suffix or "%" in suffix:
                return False
            return True
            
    # Ordinal suffix e.g. 12th, 10th
    if re.match(r'^(?:th|rd|nd|st)\b', suffix):
        if not ("percentile" in suffix or "percent" in suffix or "%" in suffix):
            return True

    # Check for four digit years in range 1990-2030 (like 2024)
    try:
        val = float(raw_val.replace(',', ''))
        if 1990 <= val <= 2030:
            text_lower = text.lower()
            keywords = ["rank", "air", "crl", "percentile", "percent", "%", "score", "marks", "nata", "cet", "chances", "eligible", "milega"]
            if "placement" in text_lower or "passout" in text_lower or not any(k in text_lower for k in keywords):
                return True
    except ValueError:
        pass

    return False


def extract_entities(current_message: str, history: list[dict]) -> dict:
    """
    Main extraction function. Called by context_builder on every request.
    
    Args:
        current_message: The student's current message (string)
        history: Full session history (mixed roles)
    
    Returns:
        {
            "departments": list[str],      # from current message ONLY
            "number": float | None,
            "number_type": str | None,     # percentile/rank/marks/ambiguous
            "category": str | None,        # canonical key or None
            "number_source": str,          # "current" or "history"
        }
    """
    # 1. Get only user turns from history, exclude current message
    user_turns = [t for t in history if t.get("role") == "user"]
    
    # 2. Filter to admission-relevant turns only
    relevant_turns = filter_relevant_history(user_turns)
    
    # 3. Extract departments — CURRENT MESSAGE ONLY
    departments = extract_departments(current_message)
    
    # 4. Extract category from current + relevant history
    category = extract_category(current_message)
    if category is None:
        for turn in relevant_turns:
            category = extract_category(turn["content"])
            if category:
                break
    
    # 5. Extract number — current message first, then history
    number, number_type, number_source = None, None, None
    
    current_norm = normalize_text(current_message)
    
    # Try explicit keywords first in current message
    for pattern, ntype in [
        (RE_PERCENTILE, "percentile"),
        (RE_RANK, "rank"),
        (RE_MARKS, "marks"),
    ]:
        m = pattern.search(current_norm)
        if m:
            raw = next((g for g in m.groups() if g is not None), None)
            if raw:
                if is_false_positive(raw, m.start(), m.end(), current_norm):
                    continue
                number = float(raw.replace(',', ''))
                number_type = ntype
                number_source = "current"
                break
    
    # Try large/lakh/comma patterns in current message
    if number is None:
        for pattern in [RE_LAKH, RE_COMMA_NUM, RE_LARGE_INT]:
            m = pattern.search(current_norm)
            if m:
                raw = next((g for g in m.groups() if g is not None), None)
                if raw:
                    if is_false_positive(raw, m.start(), m.end(), current_norm):
                        continue
                    number, number_type = classify_number(raw, current_norm)
                    number_source = "current"
                    break
    
    # Try small numbers in current message
    if number is None:
        m = RE_SMALL_NUM.search(current_norm)
        if m:
            raw = m.group(1)
            if not is_false_positive(raw, m.start(), m.end(), current_norm):
                val = float(raw)
                if val <= 100:
                    number, number_type = val, "ambiguous"
                    number_source = "current"
    
    # If no number in current message, search relevant history
    if number is None:
        # Prevent carrying over scores if the current message is a general lookup query
        current_lower = current_norm.lower()
        has_lookup = any(w in current_lower for w in ["cutoff", "cut-off", "cut off", "fees", "fee", "hostel", "placement"])
        if not has_lookup:
            for turn in reversed(relevant_turns):  # Most recent first
                turn_norm = normalize_text(turn["content"])
                for pattern, ntype in [
                    (RE_PERCENTILE, "percentile"),
                    (RE_MARKS, "marks"),
                ]:
                    m = pattern.search(turn_norm)
                    if m:
                        raw = next((g for g in m.groups() if g is not None), None)
                        if raw is not None:
                            if is_false_positive(raw, m.start(), m.end(), turn_norm):
                                continue
                            number = float(raw.replace(',', ''))
                            number_type = ntype
                            number_source = "history"
                            break
                if number:
                    break
    
    # Differentiate JEE percentile from MHT-CET percentile
    is_jee = False
    if number_type == "percentile":
        if number_source == "current" and "jee" in current_message.lower():
            is_jee = True
        elif number_source == "history":
            for turn in reversed(relevant_turns):
                turn_norm = normalize_text(turn["content"])
                if RE_PERCENTILE_KEYWORD.search(turn_norm) and "jee" in turn_norm.lower():
                    is_jee = True
                    break
    if is_jee:
        number_type = "jee_percentile"

    return {
        "departments": departments,
        "number": number,
        "number_type": number_type,
        "category": category,
        "number_source": number_source or "none",
    }