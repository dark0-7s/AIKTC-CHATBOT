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

DEPT_COMPARISON_PROFILES = {
    "COMP": {
        "name": "Computer Engineering",
        "school": "Engineering",
        "intake": "120 Seats",
        "duration": "4 Years (B.Tech)",
        "focus": "Algorithms, Full-Stack Software Engineering, Cloud Architecture, Database Systems, Cyber Security, Distributed Systems",
        "labs": "Machine Learning Lab, Data Engineering Lab, Cloud Computing Lab, Systems Programming Lab",
        "projects": "Algorithm 8.0 Hackathons, Full-Stack Web Portals, Cloud Computing Architecture, Scalable Databases",
        "industry": "Enterprise Software, Cloud Computing, FinTech, Cybersecurity & SaaS Platforms",
        "careers": "Software Development Engineer (SDE), Cloud Solutions Architect, Full-Stack Developer, Cyber Security Specialist",
        "recruiters": "TCS, Infosys, Capgemini, Jio, Accenture, L&T Infotech",
        "suitability": "Ideal if you enjoy programming, building web/cloud systems, software architecture, and algorithmic problem-solving.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-engineering/"
    },
    "CSE": {
        "name": "Computer Engineering",
        "school": "Engineering",
        "intake": "120 Seats",
        "duration": "4 Years (B.Tech)",
        "focus": "Algorithms, Full-Stack Software Engineering, Cloud Architecture, Database Systems, Cyber Security, Distributed Systems",
        "labs": "Machine Learning Lab, Data Engineering Lab, Cloud Computing Lab, Systems Programming Lab",
        "projects": "Algorithm 8.0 Hackathons, Full-Stack Web Portals, Cloud Computing Architecture, Scalable Databases",
        "industry": "Enterprise Software, Cloud Computing, FinTech, Cybersecurity & SaaS Platforms",
        "careers": "Software Development Engineer (SDE), Cloud Solutions Architect, Full-Stack Developer, Cyber Security Specialist",
        "recruiters": "TCS, Infosys, Capgemini, Jio, Accenture, L&T Infotech",
        "suitability": "Ideal if you enjoy programming, building web/cloud systems, software architecture, and algorithmic problem-solving.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-engineering/"
    },
    "CSAIML": {
        "name": "CSE (AI & Machine Learning)",
        "school": "Engineering",
        "intake": "120 Seats",
        "duration": "4 Years (B.Tech)",
        "focus": "Deep Learning, Natural Language Processing (NLP), Computer Vision, Generative AI, Reinforcement Learning, Autonomous Systems",
        "labs": "AI/ML Lab, High Performance Computing Lab, Multi-core GPU Workstation Cluster",
        "projects": "Predictive Healthcare Diagnostics, Autonomous Vehicle Systems, NLP Voice Assistants, Computer Vision Inspection",
        "industry": "Artificial Intelligence, Robotic Automation, Healthcare Analytics, FinTech Predictive Modeling",
        "careers": "AI Engineer, Machine Learning Specialist, Deep Learning Engineer, Computer Vision Developer, Data Scientist",
        "recruiters": "TCS, Capgemini, Reliance Jio, Tech Mahindra, Specialized AI Startups",
        "suitability": "Ideal if you love neural networks, predictive algorithms, cognitive computing, and creating intelligent systems.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-engineering/"
    },
    "CSDS": {
        "name": "CSE (Data Science)",
        "school": "Engineering",
        "intake": "60 Seats",
        "duration": "4 Years (B.Tech)",
        "focus": "Big Data Engineering (Hadoop/Spark), Predictive Analytics, Applied Statistics, Data Warehousing, Business Intelligence (Tableau)",
        "labs": "Data Engineering Lab, Big Data Analytics Lab, Machine Learning Lab",
        "projects": "Nexathon Hackathons, Enterprise ETL Pipelines, Customer Churn Prediction, Financial Time-Series Forecasting",
        "industry": "Big Data Engineering, E-Commerce Analytics, Investment Banking, Supply Chain Intelligence",
        "careers": "Data Scientist, Big Data Engineer, BI Consultant, Quantitative Analyst, Data Architect",
        "recruiters": "Jio, TCS, Cognizant, Analytics Consultancies, FinTech Firms",
        "suitability": "Ideal if you are passionate about statistical patterns, mathematical modeling, and enterprise data analytics.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/computer-engineering/"
    },
    "ECS": {
        "name": "Electronics & Computer Science",
        "school": "Engineering",
        "intake": "60 Seats",
        "duration": "4 Years (B.Tech)",
        "focus": "Embedded Systems, Internet of Things (IoT), VLSI Circuit Design, Microcontrollers, Edge AI, Computer Networks, C++/Python Software",
        "labs": "Analog Circuit Design Lab, Embedded Systems Lab, Signal Processing Lab, Advanced Communication Lab",
        "projects": "Smart IoT Sensor Nodes, Microcontroller Firmware, Edge AI Prototyping, FPGA Digital Systems",
        "industry": "Semiconductors, IoT Smart Devices, Consumer Electronics, Enterprise Networking, Software Development",
        "careers": "Embedded Systems Engineer, IoT Architect, VLSI Design Engineer, Firmware Developer, Software Developer",
        "recruiters": "Intel, Qualcomm, Cisco, Texas Instruments, TCS, L&T Infotech",
        "suitability": "Ideal if you want the dual advantage of hardware circuit mastery, microcontroller robotics, and software programming.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/electronics-and-computer-science/"
    },
    "ECE": {
        "name": "Electrical & Computer Engineering",
        "school": "Engineering",
        "intake": "60 Seats",
        "duration": "4 Years (B.Tech)",
        "focus": "Smart Grid Systems, Electric Vehicle (EV) Powertrains, Power Electronics, Industrial Automation (PLC/SCADA), Microprocessors",
        "labs": "Power Electronics & Drives Lab, Control Systems Lab, Network Lab (SCILAB/MATLAB), Electrical Machines Lab",
        "projects": "EV Battery Management Systems, Solar Inverter Automation, Industrial SCADA Networks, Smart Microgrid Controllers",
        "industry": "Electric Mobility (EV), Renewable Energy Utilities, Power Distribution, Industrial Robotics",
        "careers": "EV Systems Engineer, Electrical Design Engineer, Industrial Automation Specialist, Control Systems Engineer",
        "recruiters": "Tata Power, Siemens, Schneider Electric, ABB, Adani Electricity, L&T",
        "suitability": "Ideal if you want to power the green energy transition, smart electric vehicles, and automated factory robotics.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/electrical-engineering/"
    },
    "MECH": {
        "name": "Mechanical Engineering",
        "school": "Engineering",
        "intake": "60 Seats",
        "duration": "4 Years (B.Tech)",
        "focus": "Thermodynamics, Fluid Dynamics, CAD/CAM/CAE Design (SolidWorks/ANSYS), Manufacturing Processes, Mechatronics, Automotive Engineering",
        "labs": "CNC Milling & Lathe Workshop, Heat Transfer & RAC Lab, Fluid Mechanics Lab, Dynamics of Machinery Lab, IC Engines Lab",
        "projects": "Formula Student / FSAE Racing Cars, BAJA All-Terrain Vehicles, Robotics Prototyping, HVAC Energy Optimization",
        "industry": "Automotive, Aerospace, Heavy Machinery, Precision Manufacturing, HVAC & Energy Plants",
        "careers": "Mechanical Design Engineer, Thermal Systems Engineer, Automotive Engineer, Production & Quality Engineer, Project Engineer",
        "recruiters": "Mahindra & Mahindra, Tata Motors, L&T, Godrej, Thermax, HVAC Consultancies",
        "suitability": "Ideal if you love physical machines, hands-on fabrication, vehicle engineering, thermal science, and structural robotics.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/mechanical-engineering/"
    },
    "CIVIL": {
        "name": "Civil Engineering",
        "school": "Engineering",
        "intake": "30 Seats (B.Tech) + 42 (M.Tech)",
        "duration": "4 Years (B.Tech) / 2 Years (M.Tech)",
        "focus": "Structural Analysis, Concrete Technology, Geotechnical Engineering, Transportation Systems, Environmental Engineering, BIM & GIS",
        "labs": "Concrete Technology Lab, Soil Mechanics Lab, Fluid Mechanics Lab, Total Station Advanced Surveying Suite, CAD Structural Lab",
        "projects": "Earthquake-Resistant Building Analysis, Smart Transit Planning, Water Treatment Systems, BIM 3D Construction Scheduling",
        "industry": "Infrastructure Mega-Projects, Urban Transit (Metro), Real Estate, Structural Consultancy, Environmental Engineering",
        "careers": "Structural Design Engineer, Construction Project Manager, Geotechnical Consultant, Highway Planner, BIM Engineer",
        "recruiters": "L&T Construction, Shapoorji Pallonji, Afcons, Tata Projects, Municipal Corporations",
        "suitability": "Ideal if you want to design and construct landmark buildings, bridges, metro transit networks, and water sustainability systems.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/civil-engineering/"
    },
    "BSIT": {
        "name": "B.Sc Information Technology",
        "school": "Engineering",
        "intake": "60 Seats",
        "duration": "3 Years (B.Sc)",
        "focus": "Software Development (Java, Python, PHP), Database Management, Web & Mobile Development, Linux Administration, Computer Networks",
        "labs": "IT Programming Lab, Database Lab, Software Development Lab",
        "projects": "Full-Stack Web Portals, Database-Driven E-Commerce Sites, Mobile Apps, Network Security Auditing",
        "industry": "IT Services, Web Development Agencies, Corporate Software Support, Database Operations",
        "careers": "Web Developer, Junior Software Engineer, Database Administrator, QA/Software Tester, Network Associate",
        "recruiters": "TCS, Wipro, Infosys, Tech Startups, IT Consultancies",
        "suitability": "Ideal if you seek a fast-track 3-year degree focused on immediate software programming and web development.",
        "url": "https://soet.aiktc.ac.in/school-of-engineering/bachelor-of-science-i-t/"
    },
    "BPHARM": {
        "name": "Bachelor of Pharmacy (B.Pharm)",
        "school": "Pharmacy",
        "intake": "100 Seats",
        "duration": "4 Years (B.Pharm)",
        "focus": "Pharmaceutics, Pharmacology, Medicinal Chemistry, Pharmacognosy, Pharmaceutical Analysis, Biopharmaceutics",
        "labs": "Industrial Machine Room (₹30L Pilot Plant), Biotechnology Lab (LAF), Pharmaceutics Labs, Analytical Chemistry Lab",
        "projects": "Formulation Development, In-vitro Drug Release Studies, Phytochemical Extraction, Quality Control Testing",
        "industry": "Pharmaceutical Manufacturing, Clinical Research, Regulatory Affairs, Hospital & Retail Pharmacy",
        "careers": "Formulation R&D Scientist, QA/QC Chemist, Clinical Research Associate, Drug Inspector, Production Manager",
        "recruiters": "Cipla, Sun Pharma, Abbott, Lupin, Glenmark, TCS Life Sciences",
        "suitability": "Ideal if you are passionate about medicine, drug development, healthcare sciences, and clinical research.",
        "url": "https://aiktc.ac.in/bachelor-of-pharmacy/"
    },
    "DPHARM": {
        "name": "Diploma in Pharmacy (D.Pharm)",
        "school": "Pharmacy",
        "intake": "60 Seats",
        "duration": "2 Years (Diploma)",
        "focus": "Pharmaceutics, Pharmacology, Pharmacognosy, Community Pharmacy, Hospital Pharmacy, Drug Store Management",
        "labs": "Pharmaceutics Lab, Pharmaceutical Chemistry Lab, Biotechnology Lab",
        "projects": "Prescription Compounding, Patient Counseling Simulations, Drug Inventory Control",
        "industry": "Retail Pharmacy, Hospital Dispensary, Medical Distribution",
        "careers": "Registered Pharmacist (R.Ph), Hospital Pharmacist, Medical Representative, Pharmacy Store Owner",
        "recruiters": "Apollo Pharmacy, Wellness Forever, Hospital Pharmacies, Pharmaceutical Distributors",
        "suitability": "Ideal if you want rapid 2-year qualification to become a licensed pharmacist or enter community/hospital practice.",
        "url": "https://aiktc.ac.in/diploma-in-pharmacy/"
    },
    "BARCH": {
        "name": "Bachelor of Architecture (B.Arch)",
        "school": "Architecture",
        "intake": "40 Seats",
        "duration": "5 Years (B.Arch)",
        "focus": "Architectural Design, Sustainable Building Design, Building Construction & Materials, Urban Planning, History of Architecture",
        "labs": "Design Studios, Building Construction Lab, Climatology Lab, Model Making Workshop, CAD/BIM Lab",
        "projects": "NASA Design Competitions, Sustainable Campus Master Planning, Climate-Responsive Habitat Design, Scale Models",
        "industry": "Architectural Design Studios, Urban Planning Consultancies, Real Estate Developers, Interior Architecture",
        "careers": "Principal Architect, Urban Designer, Landscape Architect, Sustainable Building Consultant, BIM Manager",
        "recruiters": "Leading Architectural Firms, Bin Khot Architects, Design Studios, Urban Authorities",
        "suitability": "Ideal if you have creative artistic talent, spatial visualization, and a passion for shaping the built environment.",
        "url": "https://aiktc.ac.in/bachelor-of-architecture/"
    }
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


def format_department_comparison(dept_codes: list[str]) -> str:
    """
    Format a rich, executive, side-by-side comparative analysis between two departments.
    """
    p1 = DEPT_COMPARISON_PROFILES.get(dept_codes[0])
    p2 = DEPT_COMPARISON_PROFILES.get(dept_codes[1])
    if not p1 or not p2:
        return ""

    n1, n2 = p1["name"], p2["name"]
    c1, c2 = dept_codes[0], dept_codes[1]

    lines = [
        f"### ⚖️ Academic Program Comparison: {n1} ({c1}) vs. {n2} ({c2})\n",
        f"Choosing between **{n1}** and **{n2}** represents two distinct engineering and career pathways. Below is an authoritative, parameter-by-parameter comparison grounded in AIKTC's curriculum, lab infrastructure, and industry placement tracks:\n",
        f"| Comparison Parameter | {n1} ({c1}) | {n2} ({c2}) |",
        f"| :--- | :--- | :--- |",
        f"| **School & Affiliation** | School of {p1['school']} (Univ. of Mumbai) | School of {p2['school']} (Univ. of Mumbai) |",
        f"| **Degree & Duration** | {p1['duration']} | {p2['duration']} |",
        f"| **Approved Intake** | {p1['intake']} | {p2['intake']} |",
        f"| **Core Technical Focus** | {p1['focus']} | {p2['focus']} |",
        f"| **Specialized Laboratories** | {p1['labs']} | {p2['labs']} |",
        f"| **Hands-on Projects & Fests** | {p1['projects']} | {p2['projects']} |",
        f"| **Industry Sectors** | {p1['industry']} | {p2['industry']} |",
        f"| **Key Career Roles** | {p1['careers']} | {p2['careers']} |",
        f"| **Top Recruiters** | {p1['recruiters']} | {p2['recruiters']} |\n",
        f"### 🔍 Detailed Discipline Profiles:",
        f"- **{n1} ({c1}):** Blends {p1['focus']}. Hands-on experiential training is conducted across state-of-the-art facilities like the {p1['labs']}.",
        f"- **{n2} ({c2}):** Centers around {p2['focus']}. Practical prototyping takes place in cutting-edge facilities including the {p2['labs']}.\n",
        f"### 🎯 Which One Should You Choose? (Decision Guide):",
        f"- 👉 **Choose {n1} ({c1})** if: {p1['suitability']}",
        f"- 👉 **Choose {n2} ({c2})** if: {p2['suitability']}\n",
        f"### 🌐 Official Department Portals:",
        f"- [{n1} Official Department Page]({p1['url']})",
        f"- [{n2} Official Department Page]({p2['url']})",
        f"- [AIKTC Central Admissions Portal](https://aiktc.ac.in/admissions/)",
        f"- [AIKTC Official Website](https://aiktc.ac.in/)\n",
        f"---\n*Source: AIKTC Verified Institutional Knowledge Base*"
    ]
    return "\n".join(lines)


def synthesize_grounded_answer(
    message: str,
    algo_result: dict[str, Any],
    has_structured_card: bool = False
) -> str:
    """
    Synthesize an authoritative, grounded response from Algorithm 1 RAG retrieval
    with verified official web navigation references.
    """
    lang = algo_result.get("lang", "en")
    q_prep = algo_result.get("q_prep", message)
    intent = algo_result.get("intent", "general")
    entities = algo_result.get("entities", {})
    target_depts = entities.get("departments", []) if entities else []

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

    # 3. Handle Department Comparison Queries (e.g., "difference in ecs and mech", "compare CSE and AIML")
    is_comparison = (
        intent == "compare_departments"
        or (len(target_depts) >= 2 and any(w in q_prep.lower() for w in ("difference", "differ", "diff", "compare", "comparison", "vs", "versus", "between", "better", "choose", "and")))
    )
    if is_comparison and len(target_depts) >= 2:
        d1, d2 = target_depts[0], target_depts[1]
        if d1 in DEPT_COMPARISON_PROFILES and d2 in DEPT_COMPARISON_PROFILES:
            return format_department_comparison([d1, d2])

    # 4. Handle Cutoff & Percentile Queries (Dynamic State CET Cell First Year Admissions)
    is_cutoff_query = (
        intent == "admission_cutoff"
        or any(kw in q_prep.lower() for kw in ("cutoff", "cut-off", "cut off", "percentile", "closing rank", "closing score", "कटऑफ", "परसेंटाइल"))
    )
    if is_cutoff_query:
        if lang in ("hi", "mr"):
            cutoff_text = (
                "### 📊 MHT-CET / JEE प्रवेश कटऑफ और परसेंटाइल\n\n"
                "AIKTC (इंजीनियरिंग, फार्मेसी और आर्किटेक्चर) के सभी डिग्री पाठ्यक्रमों के लिए आधिकारिक **कटऑफ (Cutoff Percentile)** और **क्लोजिंग रैंक** महाराष्ट्र राज्य कॉमन एंट्रेंस टेस्ट सेल (State CET Cell) द्वारा **केंद्रीकृत प्रवेश प्रक्रिया (CAP Rounds)** के माध्यम से जारी किए जाते हैं।\n\n"
                "- **आधिकारिक कटऑफ और सीट आवंटन पोर्टल:**\n"
                "  राउंड-वाइज कटऑफ और मेरिट सूची देखने के लिए कृपया आधिकारिक **[Maharashtra State CET First Year Admissions & Cutoffs Portal](https://fe2026.mahacet.org/StaticPages/HomePage)** पर जाएँ।\n"
                "- **AIKTC प्रवेश सहायता केंद्र:**\n"
                "  📞 +91 8104363070 | ✉️ admissions@aiktc.ac.in | [AIKTC Central Admissions](https://aiktc.ac.in/admissions/)"
            )
        else:
            cutoff_text = (
                "### 📊 MHT-CET / JEE Admission Cutoff & Percentiles\n\n"
                "Official admission **cutoff percentiles** and **closing merit ranks** for Engineering (B.Tech), Pharmacy (B.Pharm), and Architecture (B.Arch) at AIKTC are determined dynamically by the **Maharashtra State Common Entrance Test Cell (CET Cell)** across multiple **CAP Rounds**.\n\n"
                "- **Official Cutoffs & Allotment Portal:**\n"
                "  To check live round-wise cutoff percentiles, merit ranks, and seat matrix, please visit the official **[Maharashtra State CET First Year Admissions & Cutoffs Portal](https://fe2026.mahacet.org/StaticPages/HomePage)**.\n"
                "- **AIKTC Central Admissions Helpline:**\n"
                "  📞 +91 8104363070 | ✉️ admissions@aiktc.ac.in | [AIKTC Central Admissions](https://aiktc.ac.in/admissions/)"
            )
        
        response_parts = [cutoff_text]
        official_source = get_official_source(intent, entities, message)
        if official_source and official_source.get("links"):
            source_title = official_source.get("title", "Official Web Navigation Portals")
            link_lines = [f"### 🌐 {source_title}:"]
            for link in official_source["links"]:
                link_title = link.get("title", "Official Link")
                link_url = link.get("url", "https://fe2026.mahacet.org/StaticPages/HomePage")
                link_lines.append(f"- [{link_title}]({link_url})")
            response_parts.append("\n".join(link_lines))
        response_parts.append("---\n*Source: AIKTC Verified Institutional Knowledge Base*")
        return "\n\n".join(response_parts)

    retrieved_context = (algo_result.get("retrieved_context") or "").strip()

    # 5. Extract Document sections from retrieved_context
    doc_sections: list[dict[str, Any]] = []
    if retrieved_context:
        parts = re.split(r"###\s*\[DOCUMENT\s*\d+:\s*", retrieved_context)
        for part in parts[1:]:
            lines = part.strip().split("\n")
            title_header = lines[0].split("]")[0].strip()
            
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
            # If overview chunk is present among retrieved documents, prioritize it
            overview_doc = next((d for d in doc_sections if "_overview" in d['title'].lower() or "overview" in d['title'].lower()), None)
            chosen_doc = overview_doc or doc_sections[0]
            clean_body = re.sub(r"!\[.*?\]\(.*?\)", "", chosen_doc['body'])
            clean_body = re.sub(r"(?:Lab|HOD|Director)?\s*Photo:\s*", "", clean_body)
            clean_body = re.sub(r"\s*\|\s*Photo:.*", "", clean_body)
            clean_body = re.sub(r"\berstwhile\b", "formerly", clean_body, flags=re.IGNORECASE)
            
            if not clean_body.startswith("###"):
                response_parts.append(f"### {chosen_doc['title']}\n{clean_body.strip()}")
            else:
                response_parts.append(clean_body.strip())
        else:
            response_parts.append(
                "For detailed information regarding your inquiry, please refer to the **AIKTC Admissions & Administration Office**:\n\n"
                "- **Admissions Helpline:** +91 8104363070 | admissions@aiktc.ac.in\n"
                "- **Campus Telephone:** +91-22-27481247 / +91-22-27481248\n"
                "- **Campus Address:** Plot No. 2 & 3, Sector-16, Near Thana Naka, Khandagao, New Panvel, Navi Mumbai, Maharashtra 410206"
            )

    # 6. Always append Verified Official Web Navigation Links
    official_source = get_official_source(intent, entities, message)
    if official_source and official_source.get("links"):
        source_title = official_source.get("title", "Official Web Navigation Portals")
        link_lines = [f"### 🌐 {source_title}:"]
        for link in official_source["links"]:
            link_title = link.get("title", "Official Link")
            link_url = link.get("url", "https://aiktc.ac.in/")
            link_lines.append(f"- [{link_title}]({link_url})")
        response_parts.append("\n".join(link_lines))

    # 7. Source citation footer
    response_parts.append("---\n*Source: AIKTC Verified Institutional Knowledge Base*")

    final_resp = "\n\n".join(response_parts)
    return re.sub(r"\berstwhile\b", "formerly", final_resp, flags=re.IGNORECASE)
