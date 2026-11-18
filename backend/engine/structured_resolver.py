# backend/engine/structured_resolver.py
"""
AIKTC AI Chatbot — Structured Response Resolver
=================================================
Implements Algorithm 1 Step 6 (DECIDE_RESPONSE_TYPE) and System Design Rule 12:
- Single person queries (Director, Principal, HOD, Dean) -> show_media_card
- Department faculty roster queries -> show_faculty_grid
- Department laboratory & facility queries -> show_list

Extracts profile images, credentials, and locations directly from the Knowledge Base.
"""

import re
from typing import Any


def _get_initials(name: str) -> str:
    """Generate 2-character uppercase initials from a person's name."""
    cleaned = re.sub(r"^(Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|Ar\.)\s*", "", name, flags=re.IGNORECASE).strip()
    parts = cleaned.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    return "AI"


def find_department(dept_code_or_name: str, kb_dict: dict[str, Any]) -> dict[str, Any] | None:
    """Look up a department dictionary across Engineering, Pharmacy, and Architecture."""
    target = (dept_code_or_name or "").strip().upper()
    
    # 1. Check Engineering
    eng_depts = kb_dict.get("engineering", {}).get("departments", [])
    for d in eng_depts:
        code = d.get("code", "").upper()
        name = d.get("name", "").upper()
        if target == code or target in code or code in target or target in name:
            return d
            
    # 2. Check Pharmacy
    pharm_depts = kb_dict.get("pharmacy", {}).get("departments", [])
    for d in pharm_depts:
        code = d.get("code", "").upper()
        name = d.get("name", "").upper()
        if target == code or target in code or code in target or target in name:
            return d

    # 3. Check Architecture
    arch_depts = kb_dict.get("architecture", {}).get("departments", [])
    for d in arch_depts:
        code = d.get("code", "").upper()
        name = d.get("name", "").upper()
        if target == code or target in code or code in target or target in name:
            return d

    return None


def resolve_structured_response(
    message: str,
    intent: str,
    entities: dict[str, Any],
    kb_dict: dict[str, Any]
) -> tuple[str, dict[str, Any]] | None:
    """
    Check if the query matches a structured component requirement.
    Returns (function_name, args_dict) or None.
    """
    msg_lower = message.lower()
    person_intent = entities.get("person_intent")
    depts = entities.get("departments", [])
    
    # Resolve canonical target department code
    target_dept_code = None
    if "ecs" in msg_lower or "electronics and computer" in msg_lower:
        target_dept_code = "ECS"
    elif "aiml" in msg_lower or "artificial intelligence" in msg_lower:
        target_dept_code = "CSAIML"
    elif "data science" in msg_lower or "csds" in msg_lower or " ds" in msg_lower:
        target_dept_code = "CSDS"
    elif "arch" in msg_lower or "barch" in msg_lower:
        target_dept_code = "BARCH"
    elif "pharm" in msg_lower or "bpharm" in msg_lower:
        target_dept_code = "BPHARM"
    elif "civil" in msg_lower:
        target_dept_code = "CIVIL"
    elif "mech" in msg_lower:
        target_dept_code = "MECH"
    elif "electrical" in msg_lower or "ece" in msg_lower:
        target_dept_code = "ECE"
    elif "computer" in msg_lower or "cse" in msg_lower or " co " in msg_lower:
        target_dept_code = "COMP"
    elif "bsc" in msg_lower or re.search(r"\b(it|information technology)\b", msg_lower):
        target_dept_code = "BSIT"
    elif depts:
        target_dept_code = depts[0]
        if target_dept_code == "CSE":
            target_dept_code = "COMP"

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Department Laboratories & Facilities (show_list)
    # Check first so lab queries never trigger person or faculty cards
    # ─────────────────────────────────────────────────────────────────────────
    is_lab_query = (
        intent in ("facilities", "labs") or
        any(k in msg_lower for k in ["lab", "labs", "laboratory", "laboratories", "workshop", "studios"])
    )
    if is_lab_query and target_dept_code:
        dept = find_department(target_dept_code, kb_dict)
        if dept:
            labs_list = dept.get("labs", [])
            items = []
            for lab in labs_list:
                if isinstance(lab, dict):
                    lname = lab.get("name", "")
                    items.append({
                        "name": lname,
                        "description": lab.get("description", ""),
                        "location": lab.get("location", ""),
                        "image_url": lab.get("image_url"),
                        "badge": lab.get("location", "").split(",")[0] if lab.get("location") else "Laboratory",
                        "initials": "".join([w[0] for w in lname.split() if w][:2]).upper()
                    })
            if items:
                return (
                    "show_list",
                    {
                        "title": f"{dept.get('name', target_dept_code)} Laboratories & Facilities",
                        "items": items
                    }
                )

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Single Person: Campus Director
    # ─────────────────────────────────────────────────────────────────────────
    if (person_intent == "director" or "director" in msg_lower) and not is_lab_query:
        director = kb_dict.get("common", {}).get("director", {})
        name = director.get("name", "Dr. Ramjan Khatik")
        img_url = director.get("image_url") or "/images/people/Dr-Ramzan-Khatik-Director.jpg"
        return (
            "show_media_card",
            {
                "name": name,
                "designation": "Campus Director",
                "initials": director.get("initials") or _get_initials(name),
                "image_url": img_url,
                "details": [
                    {"icon": "award", "label": "Qual.", "value": director.get("qualification", "PhD · M.E.")},
                    {"icon": "briefcase", "label": "Exp.", "value": director.get("experience", "25 years")},
                    {"icon": "mail", "label": "Email", "value": director.get("email", "director@aiktc.ac.in")},
                    {"icon": "phone", "label": "Phone", "value": director.get("phone", "022-2745-0001")},
                ]
            }
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Single Person: Principal
    # ─────────────────────────────────────────────────────────────────────────
    if (person_intent == "principal" or "principal" in msg_lower) and not is_lab_query:
        principal = kb_dict.get("common", {}).get("principal", {})
        name = principal.get("name", "Dr. Mohd. Mukhtar")
        return (
            "show_media_card",
            {
                "name": name,
                "designation": "Engineering Principal",
                "initials": principal.get("initials") or _get_initials(name),
                "image_url": principal.get("image_url"),
                "details": [
                    {"icon": "award", "label": "Qual.", "value": principal.get("qualification", "PhD · M.E.")},
                    {"icon": "briefcase", "label": "Exp.", "value": principal.get("experience", "18 years")},
                    {"icon": "mail", "label": "Email", "value": principal.get("email", "principal@aiktc.ac.in")},
                    {"icon": "phone", "label": "Phone", "value": principal.get("phone", "022-2745-0002")},
                ]
            }
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Single Person: Dean
    # ─────────────────────────────────────────────────────────────────────────
    if "dean" in msg_lower:
        if "arch" in msg_lower:
            dean = kb_dict.get("architecture", {}).get("dean", {})
            name = dean.get("name", "Prof. Raj Mhatre")
            return (
                "show_media_card",
                {
                    "name": name,
                    "designation": "Dean, School of Architecture",
                    "initials": _get_initials(name),
                    "image_url": dean.get("image_url") or "/images/architecture/barch/raj_mhatre.jpg",
                    "details": [
                        {"icon": "award", "label": "Qual.", "value": dean.get("qualification", "B.Arch, M.Arch")},
                    ]
                }
            )
        elif "pharm" in msg_lower:
            dean = kb_dict.get("pharmacy", {}).get("dean", {})
            name = dean.get("name", "Dr. Shariq Syed")
            return (
                "show_media_card",
                {
                    "name": name,
                    "designation": "Dean, School of Pharmacy",
                    "initials": _get_initials(name),
                    "image_url": dean.get("image_url") or "/images/pharmacy/bpharm/shariq_syed.jpg",
                    "details": [
                        {"icon": "award", "label": "Qual.", "value": dean.get("qualification", "M.Pharm, Ph.D. (USA)")},
                        {"icon": "briefcase", "label": "Exp.", "value": dean.get("experience", "17 years")},
                    ]
                }
            )
        else:
            dean = kb_dict.get("engineering", {}).get("dean", {})
            name = dean.get("name", "Dr. Rajendra Magar")
            return (
                "show_media_card",
                {
                    "name": name,
                    "designation": "Dean, School of Engineering & Technology",
                    "initials": _get_initials(name),
                    "image_url": dean.get("image_url") or "/images/people/rajendra_magar.jpg",
                    "details": [
                        {"icon": "award", "label": "Qual.", "value": dean.get("qualification", "Ph.D, M.E, B.E")},
                    ]
                }
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Single Person: Department HOD / Coordinator
    # ─────────────────────────────────────────────────────────────────────────
    if person_intent == "hod" or "hod" in msg_lower or "head of department" in msg_lower or "head" in msg_lower:
        if target_dept_code:
            dept = find_department(target_dept_code, kb_dict)
            if dept:
                hod = dept.get("hod") or dept.get("programme_coordinator") or dept.get("dean")
                if isinstance(hod, dict):
                    name = hod.get("name", "")
                    desig = hod.get("designation") or f"HOD ({dept.get('name', target_dept_code)})"
                    img_url = hod.get("image_url")
                    return (
                        "show_media_card",
                        {
                            "name": name,
                            "designation": desig,
                            "initials": _get_initials(name),
                            "image_url": img_url,
                            "details": [
                                {"icon": "award", "label": "Qual.", "value": hod.get("qualification", "")},
                                {"icon": "briefcase", "label": "Exp.", "value": hod.get("experience", "")},
                            ]
                        }
                    )

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Department Faculty Grid
    # ─────────────────────────────────────────────────────────────────────────
    is_faculty_query = (
        intent == "faculty" or
        any(k in msg_lower for k in ["faculty", "staff", "staffs", "teachers", "professors", "lecturer"])
    )
    if is_faculty_query and target_dept_code:
        dept = find_department(target_dept_code, kb_dict)
        if dept:
            faculty_list = dept.get("faculty", [])
            members = []
            for f in faculty_list:
                if isinstance(f, dict):
                    fname = f.get("name", "")
                    members.append({
                        "name": fname,
                        "designation": f.get("designation", "Faculty"),
                        "initials": _get_initials(fname),
                        "specialization": f.get("qualification") or f.get("specialization") or "",
                        "experience": f.get("experience", ""),
                        "image_url": f.get("image_url")
                    })
            if members:
                return (
                    "show_faculty_grid",
                    {
                        "department": dept.get("name", target_dept_code),
                        "members": members[:8]  # Clean compact roster
                    }
                )

    return None
