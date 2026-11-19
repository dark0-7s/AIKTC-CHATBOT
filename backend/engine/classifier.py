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


# ==============================================================================
# PREPROCESSING (Algorithm 1 — Step 1)
# ==============================================================================
DEVANAGARI_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

def preprocess(text: str) -> str:
    """
    Algorithm 1, Step 1: Preprocess user query.
    Normalizes whitespace, converts Devanagari digits to ASCII, and strips whitespace.
    """
    if not text:
        return ""
    for dev, ascii_ in DEVANAGARI_DIGITS.items():
        text = text.replace(dev, ascii_)
    # Normalize multiple whitespace characters
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ==============================================================================
# INTENT CLASSIFICATION (Algorithm 1 — Step 2)
# ==============================================================================
INTENT_PATTERNS = {
    "out_of_scope": [
        r'\b(?:weather|temperature|forecast|cricket|football|movie|song|jokes?|riddles?|recipe|pm of india|president of india)\b',
        r'\b(?:write (?:a |me )?(?:code|python|java|program|essay|poem)|solve (?:this )?math|who won the match)\b',
        r'\b(?:vjti|spit|coep|ict|iit bombay|bits pilani|mit pune)\b',
        r'\b(?:elon musk|bill gates|mark zuckerberg|narendra modi|donald trump|messi|ronaldo|virat kohli)\b',
        r'\b(?:capital of \w+|stock market|bitcoin|crypto|how to cook|bake a cake)\b'
    ],
    "admission_process": [
        r'\b(?:admission process|how to apply|apply for admission|admission procedure|steps to apply|step by step process)\b',
        r'\b(?:admission kaise|kaise apply|admission lena|form kaise|apply kaise|dakhila|pravesh prakriya)\b',
        r'\bdocuments?\b.*?\b(?:required|needed|checklist|list)\b',
        r'\b(?:eligibility criteria|eligibility for|eligibility)\b',
        r'\b(?:minority|domicile|income certificate|confirm seat|verification)\b',
        r'\b(?:institutional quota|against cap seats|after getting cap allotment)\b'
    ],
    "admission_cutoff": [
        r'\b(?:cutoff|cut off|cut-off|closing rank|closing score|percentile|कटऑफ|परसेंटाइल)\b',
        r'\b(?:chances?|milega|mil sakta|qualify)\b'
    ],
    "hostel": [
        r'\b(?:hostel|hostels|mess|accommodation|rooms|room rent|stay|pg|rental flats)\b'
    ],
    "fee": [
        r'\b(?:refund|cancellation|deducted|deduction)\b',
        r'\b(?:fee|fees|fee structure|tuition|cost|annual fee|total fee|payment|dd|demand draft|installment)\b',
        r'\b(?:kitni fee|paisa|charges)\b'
    ],
    "scholarship": [
        r'\b(?:scholarship|scholarships|mahadbt|ebc|freeship|financial aid|fee waiver|zakat)\b',
        r'\b(?:tfws|concession)\b'
    ],
    "cap": [
        r'\b(?:cap round|cap rounds|cet cell|mahacet|option form|allotment|e-scrutiny|physical scrutiny|merit list)\b',
        r'\b(?:centralised admission process|centralized admission process|dte code|choice code|institute code)\b',
        r'\bcap\b'
    ],
    "faculty": [
        r'\b(?:who is the training and placement officer|who is tpo|who is the tpo)\b',
        r'\b(?:faculty|teacher|teachers|professor|professors|lecturer|staff|hod|dean|director|principal)\b',
        r'\b(?:head of|who is the hod|who is the director|who is the principal|who teaches|teach|instructor|kaun hai)\b'
    ],
    "placement": [
        r'\b(?:placement|placements|package|highest package|average package|recruiter|recruiters|companies|company|internship|internships|placed|aptitude|tpo cell)\b'
    ],
    "facilities": [
        r'\b(?:facility|facilities|lab|labs|laboratory|laboratories|library|canteen|sports|gym|ground|bus|transport|infrastructure)\b',
        r'\b(?:krrc|incubation|workshop|equipment|auditorium|club|clubs|chapter|chapters|ieee|csi)\b'
    ],
    "contact": [
        r'\b(?:contact|phone|email|address|location|helpline|how to reach|call|talk to|office|where is)\b'
    ]
}

def classify_intent(text: str, context: list[dict] | None = None) -> str:
    """
    Algorithm 1, Step 2: Intent classification.
    Determines query intent using deterministic keyword and pattern matching.
    Returns canonical intent string.
    """
    text_lower = text.lower()

    # 1. Out of scope
    for pattern in INTENT_PATTERNS["out_of_scope"]:
        if re.search(pattern, text_lower):
            return "out_of_scope"

    # 2. Specific refund / cancellation query has highest fee precedence
    if re.search(r'\b(?:refund|cancellation|deducted|deduction)\b', text_lower):
        return "fee"

    # 3. Hostel (e.g., "hostel accommodation", "hostel fee", "apply for hostel")
    for pattern in INTENT_PATTERNS["hostel"]:
        if re.search(pattern, text_lower):
            return "hostel"

    # 4. Explicit "how to apply" or application steps
    if re.search(r'\b(?:how to apply|apply for admission|admission process|steps to apply|step by step process)\b', text_lower):
        return "admission_process"

    # 4. Explicit fee queries (e.g., "concession in fees", "TFWS category fees")
    if re.search(r'\b(?:concession in fees?|category fees?|fee(?:s)? for \w+ category)\b', text_lower):
        return "fee"

    # 5. Cutoff & chances (takes precedence over TFWS/scholarship mentions)
    for pattern in INTENT_PATTERNS["admission_cutoff"]:
        if re.search(pattern, text_lower):
            return "admission_cutoff"

    # 4. Hostel (e.g., "hostel accommodation", "hostel fee")
    for pattern in INTENT_PATTERNS["hostel"]:
        if re.search(pattern, text_lower):
            return "hostel"

    # 5. CAP rounds & state admission authorities (e.g. e-scrutiny, CAP verification)
    for pattern in INTENT_PATTERNS["cap"]:
        if re.search(pattern, text_lower):
            return "cap"

    # 6. Scholarship (e.g. MahaDBT, EBC, TFWS waiver, minority scholarship)
    for pattern in INTENT_PATTERNS["scholarship"]:
        if re.search(pattern, text_lower):
            return "scholarship"

    # 7. Admission Process & documentation & basic eligibility
    for pattern in INTENT_PATTERNS["admission_process"]:
        if re.search(pattern, text_lower):
            return "admission_process"

    # 8. Faculty / Personnel (checked before placement so "Who is TPO" maps to faculty)
    for pattern in INTENT_PATTERNS["faculty"]:
        if re.search(pattern, text_lower):
            return "faculty"

    # 9. Placements & recruiters
    for pattern in INTENT_PATTERNS["placement"]:
        if re.search(pattern, text_lower):
            return "placement"

    # 10. Fees & payment
    for pattern in INTENT_PATTERNS["fee"]:
        if re.search(pattern, text_lower):
            return "fee"

    # 11. Facilities, labs, infrastructure
    for pattern in INTENT_PATTERNS["facilities"]:
        if re.search(pattern, text_lower):
            return "facilities"

    # 12. Contact, phone, address, directions
    for pattern in INTENT_PATTERNS["contact"]:
        if re.search(pattern, text_lower):
            return "contact"

    # 13. Check follow-up context if present
    if context:
        for turn in reversed(context):
            if turn.get("role") == "user":
                prev_intent = classify_intent(turn.get("content", ""))
                if prev_intent in ("faculty", "fee", "admission_cutoff", "hostel", "scholarship"):
                    return prev_intent
                break

    return "general"

