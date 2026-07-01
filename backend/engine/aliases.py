# backend/engine/aliases.py

import unicodedata

DEPARTMENT_ALIASES = {
    "CSE": [
        "cse", "computer", "cs", "comps", "comp", "computer science",
        "computer engineering", "cs engineering",
        "कंप्यूटर", "कंप्यूटर इंजीनियरिंग", "कंप्यूटर साइंस",
        "computer hai", "cse chahiye", "cs milega"
    ],
    "IT": [
        "it", "information technology", "info tech", "i.t.",
        "सूचना प्रौद्योगिकी", "आईटी", "it chahiye", "it milega"
    ],
    "ECS": [
        "ecs", "electronics", "e&cs", "extc", "e&tc", "e and tc",
        "electronics and computer", "electronics computer",
        "इलेक्ट्रॉनिक्स", "इलेक्ट्रॉनिक्स एंड कंप्यूटर",
        "ecs chahiye", "extc chahiye"
    ],
    "MECH": [
        "mech", "mechanical", "mechnical", "mechanic",
        "मैकेनिकल", "यांत्रिक", "यांत्रिक अभियांत्रिकी",
        "mech chahiye", "mechanical milega"
    ],
    "CIVIL": [
        "civil", "civil engineering", "civl",
        "सिविल", "सिविल इंजीनियरिंग",
        "civil chahiye"
    ],
    "CHEM": [
        "chem", "chemical", "chemical engineering",
        "रासायनिक", "रासायनिक अभियांत्रिकी"
    ],
    "BPHARM": [
        "bpharm", "b pharm", "b.pharm", "bachelor of pharmacy",
        "pharmacy", "pharma", "b pharmacy",
        "फार्मेसी", "बी फार्म", "बी फार्मेसी",
        "bpharm chahiye", "pharmacy milega"
    ],
    "MPHARM": [
        "mpharm", "m pharm", "m.pharm", "master of pharmacy",
        "m pharmacy", "एम फार्म", "एम फार्मेसी"
    ],
    "BARCH": [
        "barch", "b arch", "b.arch", "bachelor of architecture",
        "architecture", "arch",
        "आर्किटेक्चर", "वास्तुकला", "बी आर्क",
        "arch chahiye", "architecture milega"
    ]
}

CATEGORY_ALIASES = {
    "Open": [
        "open", "general", "unreserved", "ur", "open category",
        "general category", "no reservation", "gen",
        "सामान्य", "खुला", "अनारक्षित", "जनरल", "सामान्य वर्ग",
        "samanaya", "khula", "general hai", "open hai",
        "open category hai", "no caste", "merit"
    ],
    "OBC": [
        "obc", "other backward class", "other backward caste",
        "backward class", "obc-ncl", "ncl", "obc ncl",
        "पिछड़ा", "अन्य पिछड़ा वर्ग", "ओबीसी",
        "obc hai", "obc category", "pichwada", "obc certificate"
    ],
    "SC": [
        "sc", "scheduled caste", "dalit", "sc category",
        "अनुसूचित जाति", "एससी", "sc hai", "sc certificate"
    ],
    "ST": [
        "st", "scheduled tribe", "tribal", "adivasi",
        "अनुसूचित जनजाति", "एसटी", "आदिवासी",
        "st hai", "st category", "st certificate"
    ],
    "EWS": [
        "ews", "economically weaker section", "economically weaker",
        "ews certificate", "income below 8 lakh",
        "आर्थिक रूप से कमजोर", "ईडब्ल्यूएस",
        "ews hai", "ews category", "8 lakh income"
    ],
    "TFWS": [
        "tfws", "tuition fee waiver", "fee waiver", "tfw",
        "tuition waiver", "tfws seat", "fee waiver scheme",
        "शुल्क माफी", "टीएफडब्ल्यूएस",
        "tfws hai", "fee waiver seat", "tuition free"
    ]
}

# Words that signal a turn is admission-relevant (for history filtering)
# IMPORTANT: "cutoff" is deliberately excluded — it is a data lookup word,
# not an eligibility word. Including it would contaminate the engine.
ADMISSION_SIGNALS = {
    # English
    "percentile", "rank", "chance", "chances", "eligible", "eligibility",
    "get into", "get in", "qualify", "enough", "sufficient",
    "will i get", "can i get", "should i apply", "admission",
    "milega", "mil sakta", "score",
    # Hindi
    "प्रतिशत", "रैंक", "अवसर", "योग्य", "प्रवेश",
    # All department names (any mention of dept in a turn is admission-relevant)
    *[alias for aliases in DEPARTMENT_ALIASES.values() for alias in aliases],
}

ELIGIBILITY_SIGNALS = {
    # Used in prompt to decide when to present Type A verdict
    # English
    "chance", "chances", "eligible", "eligibility", "get into", "get in",
    "qualify", "enough", "sufficient", "will i get", "can i get",
    "should i apply",
    # Hindi
    "milega", "mil sakta", "chance hai", "eligible hoon", "ho sakta hai",
    "मिलेगा", "मिल सकता", "योग्य", "प्रवेश मिलेगा", "क्या मुझे"
}

# Lookup words — do NOT cause history turn retention
LOOKUP_WORDS = {
    "cutoff", "table", "list", "show", "fees", "hostel", "lab",
    "faculty", "who is", "kaun", "kya hai"
}

def normalize(text: str) -> str:
    """Normalize unicode text — converts to NFC form and strips extra whitespace."""
    return unicodedata.normalize("NFC", text).strip()