# backend/engine/rag_synthesizer.py
"""
AIKTC AI Chatbot — RAG Grounded Synthesizer
============================================
Synthesizes accurate, grounded natural responses directly from the
retrieved knowledge base chunks and integrates official institutional
web navigation links to ensure 100% zero-hallucination institutional
factual accuracy and seamless portal navigation.
"""

import re
from typing import Any

from engine.dynamic_resolver import get_official_source

GREETING_WORDS = {
    "hi", "hello", "hey", "hola", "namaste", "assalam", "assalamoalaikum",
    "salaam", "good morning", "good afternoon", "good evening", "howdy",
    "sup", "who are you", "what can you do", "help"
}

def is_greeting(query: str) -> bool:
    q = query.strip().lower()
    q_clean = re.sub(r"[^\w\s]", "", q).strip()
    if q_clean in GREETING_WORDS:
        return True
    for g in GREETING_WORDS:
        if q_clean.startswith(g + " ") or q_clean == g:
            return True
    return False

def format_greeting(lang: str = "en") -> str:
    if lang in ("hi", "mr"):
        return (
            "नमस्ते! अंजुमन-ए-इस्लाम के कालसेकर टेक्निकल कैंपस (AIKTC) एआई सहायक में आपका स्वागत है।\n\n"
            "मैं आपको निम्नलिखित विषयों पर सहायता प्रदान कर सकता हूँ:\n"
            "- **प्रवेश और कटऑफ:** कैब राउंड, एमएचटी-सीईटी कटऑफ और आवश्यक दस्तावेज\n"
            "- **पाठ्यक्रम:** इंजीनियरिंग (बी.ई., डिप्लोमा) और फार्मेसी (डी.फार्म, बी.फार्म, एम.फार्म)\n"
            "- **शुल्क और छात्रवृत्ति:** अनुमोदित शुल्क संरचना और छात्रवृत्ति योजनाएं\n"
            "- **संकाय और परिसर:** संकाय विवरण, प्रयोगशालाएं और सुविधाएं\n"
            "- **वेबसाइट नेविगेशन:** आधिकारिक AIKTC पोर्टल लिंक्स\n\n"
            "### 🌐 आधिकारिक लिंक्स:\n"
            "- [AIKTC Central Admissions Portal](https://aiktc.ac.in/admissions/)\n"
            "- [AIKTC Official Website](https://aiktc.ac.in/)\n\n"
            "---\n*Source: AIKTC Verified Institutional Knowledge Base*"
        )
    return (
        "Hello! Welcome to the **Anjuman-I-Islam's Kalsekar Technical Campus (AIKTC) AI Assistant**.\n\n"
        "I can help you with:\n"
        "- **Admissions & Eligibility:** CAP rounds, cutoff percentiles, and required documents\n"
        "- **Academic Programs:** Engineering (Degree & Diploma) and Pharmacy (D.Pharm, B.Pharm, M.Pharm)\n"
        "- **Fees & Scholarships:** FRA-approved fee structures, government & institutional scholarships\n"
        "- **Faculty & Campus:** Department leadership, research laboratories, and campus facilities\n"
        "- **Official Web Navigation:** Direct links to official AIKTC admission and department portals\n\n"
        "### 🌐 Official Institutional Portals:\n"
        "- [AIKTC Central Admissions Portal](https://aiktc.ac.in/admissions/)\n"
        "- [AIKTC Official Website](https://aiktc.ac.in/)\n\n"
        "---\n*Source: AIKTC Verified Institutional Knowledge Base*"
    )

def synthesize_grounded_answer(
    message: str,
    algo_result: dict[str, Any],
    has_structured_card: bool = False
) -> str:
    """
    Synthesize an authoritative, grounded response from Algorithm 1 RAG retrieval
    with verified official web navigation references.

    If has_structured_card is True, concise non-duplicated supplementary context is
    provided alongside official links, preventing duplicate text rosters and images.
    """
    lang = algo_result.get("lang", "en")
    q_prep = algo_result.get("q_prep", message)
    intent = algo_result.get("intent", "general")
    entities = algo_result.get("entities", {})
    
    # 1. Handle Greetings
    if is_greeting(q_prep):
        return format_greeting(lang)

    # 2. Handle Out-of-Scope Queries
    if intent == "out_of_scope":
        if lang in ("hi", "mr"):
            return (
                "मैं केवल **अंजुमन-ए-इस्लाम के कालसेकर टेक्निकल कैंपस (AIKTC)** से संबंधित कॉलेज, प्रवेश, पाठ्यक्रम, शुल्क, संकाय और परिसर सुविधाओं के प्रश्नों में सहायता कर सकता हूँ।\n\n"
                "कृपया AIKTC प्रवेश, छात्रवृत्ति, प्रयोगशालाओं या विभागों के बारे में पूछें।\n\n"
                "### 🌐 आधिकारिक AIKTC पोर्टल:\n"
                "- [AIKTC Central Admissions Portal](https://aiktc.ac.in/admissions/)\n"
                "- [AIKTC Official Website](https://aiktc.ac.in/)\n\n"
                "---\n*Source: AIKTC Verified Institutional Knowledge Base*"
            )
        return (
            "I am the **AIKTC Institutional AI Assistant**, dedicated exclusively to providing verified information regarding **Anjuman-I-Islam's Kalsekar Technical Campus (AIKTC)**.\n\n"
            "Your question appears to be outside my institutional scope. You can ask me about:\n"
            "- **Admissions & Eligibility:** B.Tech, Pharmacy, B.Arch, and CAP round schedules\n"
            "- **Academic Fees & Scholarships:** FRA-approved fee structures and MahaDBT / EBC schemes\n"
            "- **Departments & Faculty:** Faculty profiles, department leadership, and research laboratories\n"
            "- **Campus Facilities:** Hostels, Central Library, Incubation Centre, and Placement Cell\n\n"
            "### 🌐 Official Institutional Portals:\n"
            "- [AIKTC Central Admissions Portal](https://aiktc.ac.in/admissions/)\n"
            "- [AIKTC Official Website](https://aiktc.ac.in/)\n\n"
            "---\n*Source: AIKTC Verified Institutional Knowledge Base*"
        )

    retrieved_context = (algo_result.get("retrieved_context") or "").strip()

    # 2. Extract Document sections from retrieved_context
    doc_sections: list[dict[str, Any]] = []
    if retrieved_context:
        parts = re.split(r"###\s*\[DOCUMENT\s*\d+:\s*", retrieved_context)
        for part in parts[1:]:
            lines = part.strip().split("\n")
            title_header = lines[0].split("]")[0].strip()
            
            # Extract domain if present
            domain = ""
            for l in lines[1:4]:
                if l.startswith("Domain:"):
                    domain = l.split("Domain:")[1].split("|")[0].strip()
                    break

            body_lines = [
                l for l in lines[1:]
                if not l.startswith("Domain:") and not l.strip() == "----------------------------------------"
            ]
            body = "\n".join(body_lines).strip()
            if body:
                doc_sections.append({
                    "title": title_header,
                    "domain": domain,
                    "body": body
                })

    response_parts: list[str] = []

    if has_structured_card:
        # When a structured card (MediaCard, FacultyGrid, ListCards) is rendered,
        # provide a concise supplementary overview without duplicating the card data or repeating images.
        if doc_sections:
            primary_doc = doc_sections[0]
            clean_body = re.sub(r"!\[.*?\]\(.*?\)", "", primary_doc['body'])
            clean_body = re.sub(r"(?:Lab|HOD|Director)?\s*Photo:\s*", "", clean_body)
            clean_body = re.sub(r"\s*\|\s*Photo:.*", "", clean_body)
            
            body_lines = [line.strip() for line in clean_body.split("\n") if line.strip()]
            summary_lines = []
            for line in body_lines:
                if line.startswith("- **") and len(summary_lines) >= 1:
                    break
                if line.startswith("- Prof.") or line.startswith("- Dr.") or line.startswith("Faculty Members:"):
                    break
                summary_lines.append(line)
                if len(summary_lines) >= 4:
                    break
            
            if summary_lines:
                response_parts.append("\n".join(summary_lines))
    else:
        if doc_sections:
            primary_doc = doc_sections[0]
            clean_body = re.sub(r"!\[.*?\]\(.*?\)", "", primary_doc['body'])
            clean_body = re.sub(r"(?:Lab|HOD|Director)?\s*Photo:\s*", "", clean_body)
            clean_body = re.sub(r"\s*\|\s*Photo:.*", "", clean_body)
            response_parts.append(f"### {primary_doc['title']}\n{clean_body.strip()}")
        else:
            response_parts.append(
                "For detailed information regarding your inquiry, please refer to the **AIKTC Admissions & Administration Office**:\n\n"
                "- **Admissions Helpline:** +91 8104363070 | admissions@aiktc.ac.in\n"
                "- **Campus Telephone:** +91-22-27481247 / +91-22-27481248\n"
                "- **Campus Address:** Plot No. 2 & 3, Sector-16, Near Thana Naka, Khandagao, New Panvel, Navi Mumbai, Maharashtra 410206"
            )

    # 3. Always append Verified Official Web Navigation Links
    official_source = get_official_source(intent, entities, message)
    if official_source and official_source.get("links"):
        source_title = official_source.get("title", "Official Web Navigation Portals")
        link_lines = [f"### 🌐 {source_title}:"]
        for link in official_source["links"]:
            link_title = link.get("title", "Official Link")
            link_url = link.get("url", "https://aiktc.ac.in/")
            link_lines.append(f"- [{link_title}]({link_url})")
        response_parts.append("\n".join(link_lines))

    # 4. Source citation footer
    response_parts.append("---\n*Source: AIKTC Verified Institutional Knowledge Base*")

    return "\n\n".join(response_parts)
