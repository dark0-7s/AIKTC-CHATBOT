# backend/engine/dynamic_resolver.py
"""
AIKTC AI Chatbot — Dynamic Information & Official Source Resolver
=================================================================
Implements Step 3 of Algorithm 1:
  - is_dynamic(intent, entities, message)
  - get_official_source(intent, entities, message)

Comprehensive mapping of all official AIKTC website URLs, departmental
homepages, lab directories, syllabi, fee circulars, and government portals.
"""

from typing import Any

# ==============================================================================
# VERIFIED OFFICIAL AIKTC & GOVERNMENT URL REGISTRY
# ==============================================================================
OFFICIAL_SOURCES = {
    # ── Government & Examination Authorities ──────────────────────────────────
    "cet_cell": {
        "title": "Maharashtra CET Cell Official Portal",
        "url": "https://cetcell.mahacet.org/",
        "icon": "ti-world"
    },
    "dte_maharashtra": {
        "title": "Directorate of Technical Education (DTE Maharashtra)",
        "url": "https://www.dtemaharashtra.gov.in/",
        "icon": "ti-building"
    },
    "mahadbt": {
        "title": "MahaDBT Official Scholarship Portal",
        "url": "https://mahadbt.maharashtra.gov.in/",
        "icon": "ti-award"
    },
    "nri_cet_cell": {
        "title": "CET Cell Foreign / NRI Admissions Portal",
        "url": "https://fn.mahacet.org/",
        "icon": "ti-globe"
    },

    # ── Central AIKTC Institutional Portals ────────────────────────────────────
    "aiktc_main": {
        "title": "AIKTC Official Website",
        "url": "https://aiktc.ac.in/",
        "icon": "ti-home"
    },
    "aiktc_admissions": {
        "title": "AIKTC Central Admissions Portal",
        "url": "https://aiktc.ac.in/admissions/",
        "icon": "ti-school"
    },
    "aiktc_fees": {
        "title": "AIKTC Official Fee Structure Circular",
        "url": "https://aiktc.ac.in/aiktc-fees-structure/",
        "icon": "ti-receipt"
    },
    "aiktc_library": {
        "title": "KRRC Central Library Online Portal",
        "url": "http://www.aiktlibrary.org/",
        "icon": "ti-book"
    },
    "aiktc_placements": {
        "title": "AIKTC Training & Placement Cell (TPO)",
        "url": "https://aiktc.ac.in/training-and-placement/",
        "icon": "ti-briefcase"
    },
    "aiktc_virtual_tour": {
        "title": "AIKTC Campus Virtual Tour (YouTube)",
        "url": "https://www.youtube.com/watch?v=UP75aVsNqOU&t=1s",
        "icon": "ti-video"
    },
    "aiktc_activities": {
        "title": "AIKTC Social & Student Council Activities",
        "url": "https://aiktc.ac.in/social-activities/",
        "icon": "ti-users"
    },
    "aiktc_sports": {
        "title": "AIKTC Sports & Fitness Centre",
        "url": "https://soet.aiktc.ac.in/aiktc-centres/sports-fitness-centre/",
        "icon": "ti-activity"
    },

    # ── Engineering Departmental Portals (soet.aiktc.ac.in) ───────────────────
    "cse_homepage": {
        "title": "Computer Engineering Official Department Page",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-engineering/",
        "icon": "ti-device-desktop"
    },
    "cse_labs": {
        "title": "Computer Engineering Laboratories Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-engineering/computer-engineering-labs/",
        "icon": "ti-cpu"
    },
    "cse_syllabus": {
        "title": "Computer Engineering Curriculum & Syllabus",
        "url": "https://soet.aiktc.ac.in/co-syllabus/",
        "icon": "ti-file-text"
    },
    "cs_aiml_homepage": {
        "title": "CSE (AI & Machine Learning) Department Page",
        "url": "https://soet.aiktc.ac.in/computer-science-and-engineering-aiml/",
        "icon": "ti-robot"
    },
    "cs_ds_homepage": {
        "title": "CSE (Data Science) Official Department Page",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-science-and-engineering-data-science/",
        "icon": "ti-chart-dots"
    },
    "ecs_homepage": {
        "title": "Electronics & Computer Science Department Page",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/electronics-and-computer-science/",
        "icon": "ti-circuit-switch"
    },
    "ecs_labs": {
        "title": "Electronics & Computer Science Laboratories Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/electronics-and-computer-science/electronics-and-computer-science-labs/",
        "icon": "ti-cpu"
    },
    "civil_homepage": {
        "title": "Civil Engineering Official Department Page",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/civil-engineering/",
        "icon": "ti-tool"
    },
    "mech_homepage": {
        "title": "Mechanical Engineering Official Department Page",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/mechanical-engineering/",
        "icon": "ti-settings"
    },
    "ece_homepage": {
        "title": "Electrical & Computer Engineering Department Page",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/electrical-and-computer-engineering/",
        "icon": "ti-bolt"
    },
    "bscit_homepage": {
        "title": "B.Sc. Information Technology Department Page",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/bachelor-of-science-i-t/",
        "icon": "ti-code"
    },

    # ── Pharmacy & Architecture School Portals ────────────────────────────────
    "pharmacy_homepage": {
        "title": "School of Pharmacy Official Portal",
        "url": "https://aiktc.ac.in/bachelor-of-pharmacy/",
        "icon": "ti-pill"
    },
    "pharmacy_labs": {
        "title": "Pharmacy Research & Analytical Labs",
        "url": "https://aiktc.ac.in/bachelor-of-pharmacy/bachelor-of-pharmacy-labs/",
        "icon": "ti-flask"
    },
    "architecture_homepage": {
        "title": "School of Architecture Official Portal",
        "url": "https://aiktc.ac.in/bachelor-of-architecture/",
        "icon": "ti-building-arch"
    },
    "architecture_admissions": {
        "title": "B.Arch Architecture Admissions Page",
        "url": "https://aiktc.ac.in/bachelor-of-architecture-admissions/",
        "icon": "ti-compass"
    },

    # ── Leadership & Governance (aiktc.ac.in & soet.aiktc.ac.in) ─────────────
    "aiktc_director": {
        "title": "Campus Director Dr. Ramjan Khatik Official Profile",
        "url": "https://aiktc.ac.in/director/",
        "icon": "ti-user-check"
    },
    "aiktc_director_message": {
        "title": "Director's Desk & Official Message",
        "url": "https://aiktc.ac.in/directors-message/",
        "icon": "ti-message-report"
    },
    "aiktc_principal": {
        "title": "Principal's Desk - Dr. Mohd. Mukhtar Official Profile",
        "url": "https://soet.aiktc.ac.in/about-principal/",
        "icon": "ti-user"
    },
    "aiktc_board_directors": {
        "title": "AIKTC Board of Directors",
        "url": "https://aiktc.ac.in/about-aiktc/board-of-directors/",
        "icon": "ti-users"
    },
    "aiktc_board_governors": {
        "title": "AIKTC Board of Governors",
        "url": "https://soet.aiktc.ac.in/board-of-governors/",
        "icon": "ti-building"
    },
    "aiktc_org_structure": {
        "title": "AIKTC Organizational Governance Structure",
        "url": "https://soet.aiktc.ac.in/about-us/aiktc-organizational-structure/",
        "icon": "ti-sitemap"
    },

    # ── Official Faculty Directories & Staff Portals ──────────────────────────
    "faculty_directory_soet": {
        "title": "School of Engineering (SOET) Faculty Directory",
        "url": "https://soet.aiktc.ac.in/faculty-directory/",
        "icon": "ti-users"
    },
    "faculty_directory_sop": {
        "title": "School of Pharmacy (SOP) Faculty Directory",
        "url": "https://aiktc.ac.in/faculty-directory-sop/",
        "icon": "ti-users"
    },
    "faculty_directory_soa": {
        "title": "School of Architecture (SOA) Faculty Directory",
        "url": "https://aiktc.ac.in/faculty-directory-architecture/",
        "icon": "ti-users"
    },
    "cse_faculty": {
        "title": "Computer Engineering Faculty & Staff Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-engineering/computer-engineering-staff/",
        "icon": "ti-id-badge"
    },
    "cs_aiml_faculty": {
        "title": "CSE (AI & Machine Learning) Faculty Directory",
        "url": "https://soet.aiktc.ac.in/computer-science-and-engineering-aiml/artificial-intelligence-machine-learning-faculty/",
        "icon": "ti-id-badge"
    },
    "cs_ds_faculty": {
        "title": "CSE (Data Science) Faculty Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-science-and-engineering-data-science/data-science-faculty/",
        "icon": "ti-id-badge"
    },
    "ecs_faculty": {
        "title": "Electronics & Computer Science Faculty Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/electronics-and-computer-science/electronics-and-computer-science-staff/",
        "icon": "ti-id-badge"
    },
    "mech_faculty": {
        "title": "Mechanical Engineering Faculty Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/mechanical-engineering/mechanical-engineering-staff/",
        "icon": "ti-id-badge"
    },
    "civil_faculty": {
        "title": "Civil Engineering Faculty Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/civil-engineering/civil-engineering-staff/",
        "icon": "ti-id-badge"
    },
    "ece_faculty": {
        "title": "Electrical & Computer Engineering Faculty Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/electrical-and-computer-engineering/electrical-engineering-staff/",
        "icon": "ti-id-badge"
    },
    "bscit_faculty": {
        "title": "B.Sc. IT Faculty Directory",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/bachelor-of-science-i-t/bscit-faculty/",
        "icon": "ti-id-badge"
    }
}

DYNAMIC_KEYWORDS = [
    "cutoff", "cut-off", "cut off", "closing rank", "percentile",
    "cap round", "cap schedule", "cet cell", "dates", "deadline",
    "admission date", "schedule", "allotment", "merit list",
    "milega", "chances", "chance hai", "admission chance",
    "website", "portal", "link", "circular", "official link"
]


def is_dynamic(intent: str, entities: dict | None = None, message: str = "") -> bool:
    """
    Algorithm 1, Step 3: Check whether a query requires dynamic/time-sensitive information.
    
    Cutoff marks, CAP schedules, admission deadlines, or explicit portal requests
    must be routed with official navigational links.
    """
    if intent in ("admission_cutoff", "cap"):
        return True

    msg_lower = message.lower()
    return any(kw in msg_lower for kw in DYNAMIC_KEYWORDS)


def get_official_source(
    intent: str,
    entities: dict | None = None,
    message: str = ""
) -> dict[str, Any]:
    """
    Algorithm 1, Step 3: Resolve the appropriate official source links.
    Returns arguments formatted for the frontend show_links / LinkCard renderer.
    """
    depts = set(entities.get("departments", [])) if entities else set()
    msg_lower = message.lower()

    # 0. College Leadership / Administration (Director, Principal, Campus)
    if "director" in msg_lower or "principal" in msg_lower or "leadership" in msg_lower:
        return {
            "title": "Official Director, Principal & Leadership Portals",
            "links": [
                OFFICIAL_SOURCES["aiktc_director"],
                OFFICIAL_SOURCES["aiktc_director_message"],
                OFFICIAL_SOURCES["aiktc_principal"],
                OFFICIAL_SOURCES["faculty_directory_soet"],
                OFFICIAL_SOURCES["aiktc_board_directors"]
            ]
        }

    # 1. Faculty / Staff Directory Queries
    if intent == "faculty" or any(kw in msg_lower for kw in ("faculty", "teacher", "professor", "professors", "staff", "hod", "lecturer")):
        if "ECS" in depts or "ecs" in msg_lower or "electronics and computer" in msg_lower:
            return {
                "title": "Official Electronics & Computer Science Faculty Directory",
                "links": [
                    OFFICIAL_SOURCES["ecs_faculty"],
                    OFFICIAL_SOURCES["faculty_directory_soet"],
                    OFFICIAL_SOURCES["ecs_homepage"],
                    OFFICIAL_SOURCES["ecs_labs"]
                ]
            }
        elif "COMP" in depts or "CSE" in depts or "computer" in msg_lower:
            return {
                "title": "Official Computer Engineering Faculty Directory",
                "links": [
                    OFFICIAL_SOURCES["cse_faculty"],
                    OFFICIAL_SOURCES["faculty_directory_soet"],
                    OFFICIAL_SOURCES["cse_homepage"],
                    OFFICIAL_SOURCES["cse_labs"]
                ]
            }
        elif "AIML" in depts or "aiml" in msg_lower or "artificial intelligence" in msg_lower:
            return {
                "title": "Official CSE (AIML) Faculty Directory",
                "links": [
                    OFFICIAL_SOURCES["cs_aiml_faculty"],
                    OFFICIAL_SOURCES["faculty_directory_soet"],
                    OFFICIAL_SOURCES["cs_aiml_homepage"]
                ]
            }
        elif "DS" in depts or "data science" in msg_lower:
            return {
                "title": "Official CSE (Data Science) Faculty Directory",
                "links": [
                    OFFICIAL_SOURCES["cs_ds_faculty"],
                    OFFICIAL_SOURCES["faculty_directory_soet"],
                    OFFICIAL_SOURCES["cs_ds_homepage"]
                ]
            }
        elif "MECH" in depts or "mechanical" in msg_lower:
            return {
                "title": "Official Mechanical Engineering Faculty Directory",
                "links": [
                    OFFICIAL_SOURCES["mech_faculty"],
                    OFFICIAL_SOURCES["faculty_directory_soet"],
                    OFFICIAL_SOURCES["mech_homepage"]
                ]
            }
        elif "CIVIL" in depts or "civil" in msg_lower:
            return {
                "title": "Official Civil Engineering Faculty Directory",
                "links": [
                    OFFICIAL_SOURCES["civil_faculty"],
                    OFFICIAL_SOURCES["faculty_directory_soet"],
                    OFFICIAL_SOURCES["civil_homepage"]
                ]
            }
        elif "BPHARM" in depts or "pharmacy" in msg_lower:
            return {
                "title": "Official School of Pharmacy Faculty Directory",
                "links": [
                    OFFICIAL_SOURCES["faculty_directory_sop"],
                    OFFICIAL_SOURCES["pharmacy_homepage"],
                    OFFICIAL_SOURCES["pharmacy_labs"]
                ]
            }
        elif "BARCH" in depts or "architecture" in msg_lower:
            return {
                "title": "Official School of Architecture Faculty Directory",
                "links": [
                    OFFICIAL_SOURCES["faculty_directory_soa"],
                    OFFICIAL_SOURCES["architecture_homepage"]
                ]
            }
        else:
            return {
                "title": "Official AIKTC Faculty Directories",
                "links": [
                    OFFICIAL_SOURCES["faculty_directory_soet"],
                    OFFICIAL_SOURCES["faculty_directory_sop"],
                    OFFICIAL_SOURCES["faculty_directory_soa"],
                    OFFICIAL_SOURCES["aiktc_director"]
                ]
            }

    # 2. CAP rounds, CET cell & Admission Application Process
    if intent in ("cap", "admission_process") or "apply" in msg_lower or "admission" in msg_lower:
        links = [
            OFFICIAL_SOURCES["aiktc_admissions"],
            OFFICIAL_SOURCES["cet_cell"],
            OFFICIAL_SOURCES["dte_maharashtra"]
        ]
        if "nri" in msg_lower or "foreign" in msg_lower:
            links.append(OFFICIAL_SOURCES["nri_cet_cell"])
        else:
            links.append(OFFICIAL_SOURCES["aiktc_main"])
        return {
            "title": "Official AIKTC Admissions & CAP Application Portals",
            "links": links
        }

    # 2. Fee structure & circulars
    elif intent == "fee":
        return {
            "title": "Official AIKTC Fee Structure & Circulars",
            "links": [
                OFFICIAL_SOURCES["aiktc_fees"],
                OFFICIAL_SOURCES["aiktc_admissions"],
                OFFICIAL_SOURCES["aiktc_main"]
            ]
        }

    # 3. Scholarships & financial aid
    elif intent == "scholarship":
        return {
            "title": "Official Scholarship & Fee Waiver Portals",
            "links": [
                OFFICIAL_SOURCES["mahadbt"],
                OFFICIAL_SOURCES["aiktc_admissions"]
            ]
        }

    # 4. Placements & TPO
    elif intent == "placement":
        return {
            "title": "AIKTC Training & Placement Cell Official Portals",
            "links": [
                OFFICIAL_SOURCES["aiktc_placements"],
                OFFICIAL_SOURCES["aiktc_main"]
            ]
        }

    # 5. Department Laboratories & Facilities
    elif intent in ("facilities", "labs") or any(kw in msg_lower for kw in ("lab", "labs", "laboratory", "laboratories", "workshop", "studios")):
        if "ECS" in depts or "ecs" in msg_lower or "electronics and computer" in msg_lower:
            return {
                "title": "Official Electronics & Computer Science Laboratories",
                "links": [
                    OFFICIAL_SOURCES["ecs_labs"],
                    OFFICIAL_SOURCES["ecs_faculty"],
                    OFFICIAL_SOURCES["ecs_homepage"],
                    OFFICIAL_SOURCES["aiktc_main"]
                ]
            }
        elif "COMP" in depts or "CSE" in depts or "computer" in msg_lower:
            return {
                "title": "Official Computer Engineering Laboratories Directory",
                "links": [
                    OFFICIAL_SOURCES["cse_labs"],
                    OFFICIAL_SOURCES["cse_homepage"],
                    OFFICIAL_SOURCES["cse_faculty"],
                    OFFICIAL_SOURCES["cse_syllabus"]
                ]
            }
        elif "BPHARM" in depts or "pharmacy" in msg_lower:
            return {
                "title": "Official Pharmacy Laboratories & Research Portals",
                "links": [
                    OFFICIAL_SOURCES["pharmacy_labs"],
                    OFFICIAL_SOURCES["pharmacy_homepage"],
                    OFFICIAL_SOURCES["faculty_directory_sop"]
                ]
            }
        elif "BARCH" in depts or "architecture" in msg_lower:
            return {
                "title": "Official School of Architecture Studios & Labs",
                "links": [
                    OFFICIAL_SOURCES["architecture_homepage"],
                    OFFICIAL_SOURCES["faculty_directory_soa"]
                ]
            }
        else:
            return {
                "title": "Official AIKTC Campus & Department Laboratories",
                "links": [
                    OFFICIAL_SOURCES["cse_labs"],
                    OFFICIAL_SOURCES["ecs_labs"],
                    OFFICIAL_SOURCES["pharmacy_labs"],
                    OFFICIAL_SOURCES["aiktc_main"]
                ]
            }

    # 6. Departmental queries (CSE, IT, ECS, Pharmacy, Architecture, etc.)
    elif "COMP" in depts or "CSE" in depts or "computer" in msg_lower:
        return {
            "title": "Official Computer Engineering Portals & Faculty Directory",
            "links": [
                OFFICIAL_SOURCES["cse_labs"],
                OFFICIAL_SOURCES["cse_faculty"],
                OFFICIAL_SOURCES["cse_homepage"],
                OFFICIAL_SOURCES["cse_syllabus"]
            ]
        }
    elif "BPHARM" in depts or "pharmacy" in msg_lower:
        return {
            "title": "Official School of Pharmacy Portals",
            "links": [
                OFFICIAL_SOURCES["pharmacy_homepage"],
                OFFICIAL_SOURCES["pharmacy_labs"],
                OFFICIAL_SOURCES["aiktc_admissions"]
            ]
        }
    elif "BARCH" in depts or "architecture" in msg_lower:
        return {
            "title": "Official School of Architecture Portals",
            "links": [
                OFFICIAL_SOURCES["architecture_homepage"],
                OFFICIAL_SOURCES["architecture_admissions"],
                OFFICIAL_SOURCES["aiktc_admissions"]
            ]
        }
    elif "CIVIL" in depts or "civil" in msg_lower:
        return {
            "title": "Official Civil Engineering Department Portals",
            "links": [
                OFFICIAL_SOURCES["civil_homepage"],
                OFFICIAL_SOURCES["aiktc_admissions"]
            ]
        }
    elif "MECH" in depts or "mechanical" in msg_lower:
        return {
            "title": "Official Mechanical Engineering Department Portals",
            "links": [
                OFFICIAL_SOURCES["mech_homepage"],
                OFFICIAL_SOURCES["aiktc_admissions"]
            ]
        }
    elif "ECS" in depts or "ecs" in msg_lower:
        return {
            "title": "Official Electronics & Computer Science Portals & Labs",
            "links": [
                OFFICIAL_SOURCES["ecs_labs"],
                OFFICIAL_SOURCES["ecs_faculty"],
                OFFICIAL_SOURCES["ecs_homepage"],
                OFFICIAL_SOURCES["aiktc_admissions"]
            ]
        }

    # 6. Library / Campus facilities
    elif "library" in msg_lower or "krrc" in msg_lower:
        return {
            "title": "AIKTC KRRC Central Library Online Portal",
            "links": [
                OFFICIAL_SOURCES["aiktc_library"],
                OFFICIAL_SOURCES["aiktc_main"]
            ]
        }

    # 6b. Sports, Cultural, Student Clubs & Campus Activities
    elif any(k in msg_lower for k in ("sport", "sports", "cultural", "activity", "activities", "club", "clubs", "fest", "fests", "bonhomie", "fuerza", "nss")):
        return {
            "title": "Official AIKTC Campus Life, Sports & Activities Portals",
            "links": [
                OFFICIAL_SOURCES["aiktc_sports"],
                OFFICIAL_SOURCES["aiktc_activities"],
                OFFICIAL_SOURCES["aiktc_main"]
            ]
        }

    # 7. Default (Cutoffs, Admissions & General Dynamic Navigation)
    else:
        return {
            "title": "Official Cutoff & Admission Authorities",
            "links": [
                OFFICIAL_SOURCES["cet_cell"],
                OFFICIAL_SOURCES["aiktc_admissions"],
                OFFICIAL_SOURCES["dte_maharashtra"],
                OFFICIAL_SOURCES["aiktc_main"]
            ]
        }
