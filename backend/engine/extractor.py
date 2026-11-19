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
PERSON_INTENTS = {
    "hod": [
        "hod",
        "h.o.d",
        "head of department",
        "head",
        "department head",
        "head department",
    ],
    "faculty": [
        "faculty",
        "teacher",
        "professor",
        "lecturer",
        "staff",
        "staff member",
    ],

    "director": [
        "director",
    ],

    "principal": [
        "principal",
    ],

    "dean": [
        "dean",
    ]
}

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


PRONOUN_IT_PATTERN = re.compile(
    r'\b(?:'
    r'(?:compare|with|about|for|to|of|tell|show|explain)\s+it\b|'
    r'\bit\s+(?:with|to|and\s+also|is|has|does|offers?)\b|'
    r'\b(?:what|how)\s+about\s+it\b|'
    r'\bhow\s+is\s+it\b'
    r')',
    re.IGNORECASE
)

IT_ACADEMIC_CONTEXT = re.compile(
    r'\b(?:'
    r'(?:between|vs\.?|versus)\s+it\s+and\b|'
    r'\bit\s+and\s+(?:cs|comp|mech|civil|extc|ecs|pharma|arch)\b|'
    r'\b(?:cs|comp|mech|civil|extc|ecs|pharma|arch)\s+and\s+it\b|'
    r'\bit\s+(?:dept|department|branch|course|engineering|program|placements?|syllabus|curriculum|faculty)\b|'
    r'\bbsc\s*it\b'
    r')',
    re.IGNORECASE
)


def extract_departments(text: str) -> list[str]:
    """
    Extract canonical department codes from text with strict word boundary enforcement.
    Uses longest-match greedy resolution so composite phrases like 'CSE AIML' or
    'CSE Data Science' match their specific department without falsely matching 'CSE'.
    Prevents false substring matches (e.g., 'it' in 'eligibility', 'co' in 'college').
    """
    text_lower = normalize_text(text).lower()
    
    # Flatten and sort all (code, alias) pairs by length descending for greedy matching
    all_aliases = []
    for code, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            all_aliases.append((code, alias))
    all_aliases.sort(key=lambda x: len(x[1]), reverse=True)

    found = []
    claimed_spans = []

    for code, alias in all_aliases:
        if len(alias) <= 4:
            pattern = r'\b' + re.escape(alias) + r'\b'
        else:
            pattern = r'\b' + re.escape(alias)
            
        for match in re.finditer(pattern, text_lower):
            start, end = match.span()
            # If this character span was already claimed by a longer alias, skip it
            if any(s <= start < e or s < end <= e for s, e in claimed_spans):
                continue
                
            # Disambiguate pronoun 'it' from Information Technology department
            if code == "IT" and alias == "it":
                is_pronoun = bool(PRONOUN_IT_PATTERN.search(text_lower))
                is_academic = bool(IT_ACADEMIC_CONTEXT.search(text_lower))
                if is_pronoun and not is_academic:
                    continue  # Do not count pronoun 'it' as IT department
                    
            claimed_spans.append((start, end))
            if code not in found:
                found.append(code)
                
    return found

def extract_person_intent(text: str):
    text = normalize_text(text).lower()

    for intent, aliases in PERSON_INTENTS.items():
        if any(re.search(r'\b' + re.escape(a) + r'\b', text) for a in aliases):
            return intent

    return None


def extract_category(text: str) -> str | None:
    """
    Extract canonical category from text using word boundary matching.
    Returns canonical key ("Open", "OBC", etc.) or None.
    """
    text_lower = normalize_text(text).lower()
    for category, aliases in CATEGORY_ALIASES.items():
        for alias in aliases:
            if len(alias) <= 3:
                if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                    return category
            else:
                if alias in text_lower:
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


def get_recent_department_from_history(history: list[dict]) -> list[str]:
    """Search backward through history turns to find the most recent active department."""
    # First search user turns (most accurate signal of student interest)
    for turn in reversed(history):
        if turn.get("role") == "user":
            depts = extract_departments(str(turn.get("content", "")))
            if depts:
                return depts[:2]
    # Fallback to assistant turns if user turn had no explicit department
    for turn in reversed(history):
        content = str(turn.get("content", ""))
        m = re.findall(r'\b(COMP|CSE|CSAIML|CSDS|ECS|ECE|MECH|CIVIL|BSIT|BPHARM|DPHARM|MPHARM|BARCH|DARCH)\b', content)
        if m:
            return [m[0]]
        depts = extract_departments(content)
        if depts:
            return depts[:1]
    return []


def extract_entities(current_message: str, history: list[dict]) -> dict:
    """
    Main extraction function. Called by context_builder on every request.
    
    Args:
        current_message: The student's current message (string)
        history: Full session history (mixed roles)
    
    Returns:
        {
            "departments": list[str],      # current message + context window inheritance
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
    
    # 3. Extract departments from current message
    departments = extract_departments(current_message)

    # Context window inheritance for complex multi-turn and comparison queries
    current_norm_dept = normalize_text(current_message).lower()
    is_comparison = bool(re.search(r'\b(?:difference|differ|diff|compare|comparison|versus|vs\.?|distinguish|better|between|prefer)\b', current_norm_dept))
    has_pronoun_reference = bool(re.search(r'\b(?:it|this|that|the department|this branch|that branch|the course|this program)\b', current_norm_dept))
    is_dept_aspect_followup = bool(re.search(r'\b(?:faculty|hod|dean|prof|teacher|labs?|laborator(?:y|ies)|placements?|package|fees?|eligibility|syllabus|subjects?|scope|career)\b', current_norm_dept))

    if not departments and (has_pronoun_reference or is_dept_aspect_followup or is_comparison):
        hist_depts = get_recent_department_from_history(history)
        if hist_depts:
            departments = list(hist_depts)
    elif departments and (is_comparison or has_pronoun_reference):
        hist_depts = get_recent_department_from_history(history)
        for hd in hist_depts:
            if hd not in departments:
                departments.insert(0, hd)

    # 4. Extract person intent — CURRENT MESSAGE ONLY (no history carryover)
    person_intent = extract_person_intent(current_message)

    # --------------------------------------------------
    # Extract category from current message
    # --------------------------------------------------
    category = extract_category(current_message)

    # Only recover category from history if the query is an admission / cutoff follow-up
    current_norm = normalize_text(current_message).lower()
    is_admission_msg = any(s in current_norm for s in ADMISSION_SIGNALS) or bool(RE_PERCENTILE.search(current_norm))
    if category is None and is_admission_msg:
        for turn in reversed(relevant_turns):
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
        "person_intent": person_intent,
        "number": number,
        "number_type": number_type,
        "category": category,
        "number_source": number_source or "none",
    }