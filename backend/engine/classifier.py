# backend/engine/classifier.py
import re

# Matches explicit percentile: "92 percentile", "78.67%", "85 percent", "percentile is 83"
RE_PERCENTILE = re.compile(
    r'(\d{1,3}(?:\.\d+)?)\s*(?:percentile\b|percent\b|%|pratishat\b|pct\b)'
    r'|\b(?:percentile|percent|pratishat|pct)\s*(?:is|of)?\s*(\d{1,3}(?:\.\d+)?)\b',
    re.IGNORECASE
)

# Matches explicit rank: "rank 25000", "AIR 5000", "CRL 1,50,000"
RE_RANK = re.compile(
    r'(?:rank|AIR|CRL|all\s*india\s*rank|state\s*rank)\s*[:#]?\s*(\d{1,7}[\d,]*)'
    r'|(\d{1,7}[\d,]*)\s*(?:rank|AIR|CRL)',
    re.IGNORECASE
)

# Matches explicit marks/score: "NATA 145", "score 145", "145 marks"
RE_MARKS = re.compile(
    r'(\d{1,3}(?:\.\d+)?)\s*(?:marks|score|nata|out\s*of)'
    r'|(?:nata|score|marks)\s*[:#]?\s*(\d{1,3}(?:\.\d+)?)',
    re.IGNORECASE
)

# Matches lakh notation: "1.5 lakh", "2 lac", "150 thousand"
RE_LAKH = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|thousand|k)\b',
    re.IGNORECASE
)

# Matches comma-separated numbers: "1,50,000" or "125,000"
RE_COMMA_NUM = re.compile(r'(?<!\.)\b(\d{1,3}(?:,\d{2,3})+)\b(?!\.)')

# Matches large plain integers > 200 (likely ranks)
RE_LARGE_INT = re.compile(r'(?<!\.)\b([2-9]\d{2,6})\b(?!\.)')

# Matches small numbers ≤ 100 (possibly percentile, possibly ambiguous)
RE_SMALL_NUM = re.compile(r'(?<!\.)\b(\d{1,3}(?:\.\d+)?)\b(?!\.)')


def classify_number(raw: str, context_text: str) -> tuple[float, str]:
    """
    Given a raw number string and its surrounding text, return
    (numeric_value, number_type) where number_type is one of:
    "percentile", "rank", "marks", "ambiguous"
    
    Classification rules (applied in order):
    1. Explicit percentile keyword near the number → "percentile"
    2. Explicit rank keyword near the number → "rank"
    3. Explicit marks/score/NATA keyword near the number → "marks"
    4. Lakh/thousand notation → "rank"
    5. Comma-separated thousands → "rank"
    6. Number > 200 (integer, no decimal) → "rank"
    7. Number <= 100 or has decimal → "ambiguous"
    """
    try:
        value = float(raw.replace(',', ''))
    except ValueError:
        return 0.0, "ambiguous"

    ctx = context_text.lower()

    if RE_PERCENTILE.search(ctx):
        return value, "percentile"
    if RE_RANK.search(ctx):
        return value, "rank"
    if RE_MARKS.search(ctx):
        return value, "marks"
    
    m_lakh = RE_LAKH.search(ctx)
    if m_lakh:
        matched_str = m_lakh.group(0).lower()
        multiplier = 100000 if any(x in matched_str for x in ('lakh', 'lac')) else 1000
        try:
            val = float(m_lakh.group(1))
            return val * multiplier, "rank"
        except ValueError:
            pass
            
    if RE_COMMA_NUM.search(ctx):
        return value, "rank"
        
    if value > 200 and '.' not in raw:
        return value, "rank"
        
    return value, "ambiguous"
