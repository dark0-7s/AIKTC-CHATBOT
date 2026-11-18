# backend/kb/chunker.py
"""
AIKTC Knowledge Base Semantic Chunker for RAG
=============================================
Deconstructs institutional JSON and markdown knowledge into highly cohesive,
semantically grounded document chunks with rich metadata.
"""

import json
from pathlib import Path
from typing import Any


class TextChunk:
    def __init__(
        self,
        chunk_id: str,
        title: str,
        category: str,
        content: str,
        metadata: dict[str, Any] | None = None
    ):
        self.chunk_id = chunk_id
        self.title = title
        self.category = category  # e.g., 'fee', 'faculty', 'facilities', 'scholarship', 'hostel', 'placement', 'admission_process', 'contact'
        self.content = content.strip()
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        return f"<Chunk {self.chunk_id}: '{self.title}' ({self.category})>"


def _load_json_safe(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def create_chunks_from_kb(kb_dir: str | Path) -> list[TextChunk]:
    """
    Parses the knowledge base directory and creates structured semantic chunks.
    """
    kb_path = Path(kb_dir)
    chunks: list[TextChunk] = []

    # 1. Common / Institutional Overview & Leadership
    common = _load_json_safe(kb_path / "common.json")
    if isinstance(common, dict):
        # Overview
        overview_text = (
            f"Institution: {common.get('name', 'Anjuman-I-Islam Kalsekar Technical Campus (AIKTC)')}\n"
            f"Address: {common.get('address', 'Plot No. 2&3, Sector 16, Near Thana Naka, Khandagao, New Panvel, Navi Mumbai 410206')}\n"
            f"Website: {common.get('website', 'https://aiktc.ac.in')}\n"
            f"Affiliation: Affiliated to University of Mumbai, Approved by AICTE New Delhi, Recognized by DTE Maharashtra.\n"
            f"DTE Institute Code: 3217.\n"
            f"Established: {common.get('established', '2011')} by Anjuman-I-Islam trust."
        )
        chunks.append(TextChunk(
            chunk_id="inst_overview",
            title="AIKTC College Overview, Accreditation & DTE Code",
            category="contact",
            content=overview_text,
            metadata={"source": "common.json"}
        ))

        # Leadership
        director = common.get("director", {})
        principal = common.get("principal", {})
        dir_name = director.get("name", "Dr. Ramjan Khatik")
        dir_qual = director.get("qualification", "PhD · M.E.")
        dir_exp = director.get("experience", "25 years")
        dir_img = director.get("image_url", "/images/people/Dr-Ramzan-Khatik-Director.jpg")
        
        prin_name = principal.get("name", "Dr. Mohd. Mukhtar")
        prin_qual = principal.get("qualification", "PhD · M.E.")
        prin_exp = principal.get("experience", "18 years")

        leadership_text = (
            f"Campus Director: {dir_name} ({dir_qual}).\n"
            f"Director Experience: {dir_exp}.\n"
            f"Director Photo: ![{dir_name}]({dir_img})\n"
            f"Engineering Principal: {prin_name} ({prin_qual}).\n"
            f"Principal Experience: {prin_exp}.\n"
            f"Management: Governed by Anjuman-I-Islam trust, Mumbai."
        )
        chunks.append(TextChunk(
            chunk_id="inst_leadership",
            title="College Leadership - Director and Principal Profiles",
            category="faculty",
            content=leadership_text,
            metadata={"source": "common.json", "image_url": dir_img}
        ))

        # Hostel
        hostel = common.get("hostel", {})
        if hostel:
            fac_str = ", ".join(hostel.get("facilities", []))
            hostel_text = (
                f"Hostel Accommodation:\n"
                f"- Boys Hostel Capacity: {hostel.get('boys_capacity', 120)} beds.\n"
                f"- Girls Hostel Capacity: {hostel.get('girls_capacity', 80)} beds.\n"
                f"- Annual Hostel Rent/Fee: ₹{hostel.get('fees_per_year', 45000):,} per academic year.\n"
                f"- Monthly Mess Charges: ₹{hostel.get('mess_per_month', 3500):,} per month.\n"
                f"- Amenities: {fac_str or 'Wi-Fi, 24x7 security, water purifier, recreation room, study tables'}.\n"
                f"- Allotment: First-come-first-served basis upon admission confirmation."
            )
            chunks.append(TextChunk(
                chunk_id="inst_hostel",
                title="Hostel Accommodation, Fees, Capacity & Mess Facilities",
                category="hostel",
                content=hostel_text,
                metadata={"source": "common.json"}
            ))

        # Contact & Directions
        contacts = common.get("contacts", {})
        contact_text = (
            f"AIKTC Campus Contact & Location:\n"
            f"Address: Plot #2 & 3, Sector 16, Near Thana Naka, Khanda Gaon, New Panvel, Navi Mumbai, Maharashtra 410206.\n"
            f"Phone: +91-22-27481247 / +91-22-27481248\n"
            f"Admission Helpline Email: admissions@aiktc.ac.in | info@aiktc.ac.in\n"
            f"How to Reach: 10 minutes walking or auto-rickshaw from Khandeshwar / Panvel Railway Station on Harbor Line."
        )
        chunks.append(TextChunk(
            chunk_id="inst_contact",
            title="College Contact Numbers, Email & How to Reach Location",
            category="contact",
            content=contact_text,
            metadata={"source": "common.json"}
        ))

    # 2. Scholarships & Financial Aid
    scholarships_dir = kb_path / "scholarships"
    if scholarships_dir.is_dir():
        for sf in scholarships_dir.glob("*.json"):
            sdata = _load_json_safe(sf)
            if not sdata or not isinstance(sdata, dict):
                continue
            title = sdata.get("name") or sdata.get("title") or sf.stem.replace("_", " ").title()
            text_lines = [f"Scholarship Scheme: {title}"]
            for k, v in sdata.items():
                if k not in ("name", "title") and isinstance(v, (str, int, float, list)):
                    if isinstance(v, list):
                        v = ", ".join(str(item) for item in v)
                    text_lines.append(f"- {k.replace('_', ' ').capitalize()}: {v}")
            chunks.append(TextChunk(
                chunk_id=f"scholarship_{sf.stem}",
                title=f"Scholarship Details - {title}",
                category="scholarship",
                content="\n".join(text_lines),
                metadata={"source": str(sf.name)}
            ))

    # 3. Fees and Refund Policies across Schools
    for school in ["engineering", "pharmacy", "architecture"]:
        school_dir = kb_path / school
        if not school_dir.is_dir():
            continue

        # School Overview & Admission Eligibility
        overview_data = _load_json_safe(school_dir / "overview.json")
        if isinstance(overview_data, dict):
            # Dean & Leadership
            dean = overview_data.get("dean", {})
            if dean:
                d_name = dean.get("name", "")
                d_qual = dean.get("qualification", "")
                d_desig = dean.get("designation", "Dean")
                d_img = dean.get("image_url", "")
                d_content = (
                    f"Dean, School of {school.capitalize()}: {d_name} ({d_qual}), Designation: {d_desig}.\n"
                    f"School Accreditation: {overview_data.get('accreditation', 'NAAC Accredited')}."
                )
                if d_img:
                    d_content += f"\nDean Photo: ![{d_name}]({d_img})"
                chunks.append(TextChunk(
                    chunk_id=f"{school}_dean",
                    title=f"School of {school.capitalize()} - Dean Profile & Leadership",
                    category="faculty",
                    content=d_content,
                    metadata={"school": school, "image_url": d_img}
                ))

            # Admission Eligibility Criteria
            adm = overview_data.get("admission_process", {})
            if adm and isinstance(adm, dict):
                adm_lines = [f"Eligibility Criteria & Admission Process for {school.capitalize()}:"]
                for k, v in adm.items():
                    adm_lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
                chunks.append(TextChunk(
                    chunk_id=f"{school}_admission_eligibility",
                    title=f"{school.capitalize()} Admission Eligibility Criteria & Requirements",
                    category="admission_process",
                    content="\n".join(adm_lines),
                    metadata={"school": school}
                ))

            # Library & KRRC
            lib = overview_data.get("library", {})
            if lib and isinstance(lib, dict):
                chunks.append(TextChunk(
                    chunk_id=f"{school}_library",
                    title=f"Central Library & Knowledge Resources Relay Centre (KRRC)",
                    category="facilities",
                    content=(
                        f"AIKTC Central Library (KRRC):\n"
                        f"- Name: {lib.get('name', 'Knowledge Resources & Relay Centre')}\n"
                        f"- Volumes: {lib.get('volumes', 25627):,} | Titles: {lib.get('titles', 8192):,}\n"
                        f"- Digital Access: National Digital Library of India (NDLI), ASCE, Springer eBooks\n"
                        f"- Area: {lib.get('area_sqft', 9600)} sq.ft with anti-plagiarism tools and reading rooms."
                    ),
                    metadata={"school": school}
                ))

            # Incubation & Entrepreneurship
            inc = overview_data.get("incubation_centre", {})
            if inc and isinstance(inc, dict):
                hl = inc.get("highlights", {})
                chunks.append(TextChunk(
                    chunk_id=f"{school}_incubation",
                    title=f"AIKTC Innovation & Incubation Centre",
                    category="facilities",
                    content=(
                        f"Innovation & Entrepreneurship Incubation Centre:\n"
                        f"- In-Charge: {inc.get('head', 'Prof. Abdul Majid Ansari')}\n"
                        f"- Startups Incubated: {hl.get('startups_incubated', 67)} | Funding Secured: {hl.get('funding_secured', '86+ lakhs')}\n"
                        f"- Paid Internships: {hl.get('paid_internships', 80)}+ | Chanakya Training Partner recognized."
                    ),
                    metadata={"school": school}
                ))

        # Fees
        fees_data = _load_json_safe(school_dir / "fees.json")
        if isinstance(fees_data, dict):
            lines = [f"Fee Structure for School of {school.capitalize()} (Academic Year {fees_data.get('academic_year', '2025-26')}):"]
            programs = fees_data.get("programs", {})
            for prog_key, prog in programs.items():
                pname = prog.get("program_type", prog_key.upper())
                lines.append(f"\nProgram: {pname} (Duration: {prog.get('duration_years', '')} yrs)")
                for y in prog.get("annual_fees", []):
                    lines.append(
                        f"  Year {y.get('year')}: Tuition ₹{y.get('tuition_fees', 0):,}, "
                        f"Development ₹{y.get('development_fees', 0):,}, Total Annual Fee: ₹{y.get('total_fees', 0):,}"
                    )
            notes = fees_data.get("notes")
            if notes:
                lines.append(f"Notes: {notes}")
            chunks.append(TextChunk(
                chunk_id=f"{school}_fees",
                title=f"{school.capitalize()} Annual Tuition & Total Fee Structure",
                category="fee",
                content="\n".join(lines),
                metadata={"school": school}
            ))

        # Refund Policy
        refund_data = _load_json_safe(school_dir / "refund_policy.json")
        if isinstance(refund_data, dict):
            lines = [f"Admission Cancellation and Fee Refund Rules for {school.capitalize()}:"]
            for k, v in refund_data.items():
                if isinstance(v, list):
                    for item in v:
                        lines.append(f"- {item}")
                elif isinstance(v, dict):
                    for dk, dv in v.items():
                        lines.append(f"- {dk.replace('_', ' ').capitalize()}: {dv}")
                else:
                    lines.append(f"- {k.replace('_', ' ').capitalize()}: {v}")
            chunks.append(TextChunk(
                chunk_id=f"{school}_refund_policy",
                title=f"Admission Cancellation & Fee Refund Policy ({school.capitalize()})",
                category="fee",
                content="\n".join(lines),
                metadata={"school": school}
            ))

        # Departments
        dept_dir = school_dir / "departments"
        if dept_dir.is_dir():
            for df in dept_dir.glob("*.json"):
                ddata = _load_json_safe(df)
                if not isinstance(ddata, dict):
                    continue
                dname = ddata.get("name", df.stem.upper())
                dcode = ddata.get("code", df.stem.upper())

                # Dept Overview & Faculty
                hod = ddata.get("hod", {})
                hod_name = hod.get('name', 'N/A') if isinstance(hod, dict) else str(hod)
                hod_qual = hod.get('qualification', '') if isinstance(hod, dict) else ''
                hod_desig = hod.get('designation', 'HOD') if isinstance(hod, dict) else 'HOD'
                hod_exp = hod.get('experience', 'N/A') if isinstance(hod, dict) else 'N/A'
                hod_img = hod.get('image_url') if isinstance(hod, dict) else None

                fac_lines = [
                    f"Department: {dname} ({dcode}) - School of {school.capitalize()}",
                    f"Intake: {ddata.get('intake', 'N/A')} seats | Duration: {ddata.get('duration', '4 years')}",
                    f"Head of Department (HOD): {hod_name} ({hod_qual}), Designation: {hod_desig}, Experience: {hod_exp}",
                ]
                if hod_img:
                    fac_lines.append(f"HOD Photo: ![{hod_name}]({hod_img})")

                faculty_list = ddata.get("faculty", [])
                if faculty_list:
                    fac_lines.append("Faculty Members:")
                    if isinstance(faculty_list, list):
                        for f in faculty_list:
                            if isinstance(f, dict):
                                f_img = f.get('image_url')
                                f_line = f"  - {f.get('name', '')}: {f.get('designation', '')} ({f.get('qualification', '')})"
                                if f_img:
                                    f_line += f" | Photo: ![{f.get('name')}]({f_img})"
                                fac_lines.append(f_line)
                            else:
                                fac_lines.append(f"  - {f}")
                    elif isinstance(faculty_list, str):
                        fac_lines.append(f"  - {faculty_list}")

                chunks.append(TextChunk(
                    chunk_id=f"{school}_{df.stem}_faculty",
                    title=f"{dname} ({dcode}) - HOD and Faculty Profile",
                    category="faculty",
                    content="\n".join(fac_lines),
                    metadata={"school": school, "dept": dcode, "image_url": hod_img}
                ))

                # Dept Labs & Facilities
                labs = ddata.get("labs", [])
                if labs:
                    lab_lines = [f"Laboratories and Infrastructure in {dname} ({dcode}):"]
                    lab_images = []
                    for l in labs:
                        l_name = l.get('name', '')
                        l_loc = l.get('location', '')
                        l_desc = l.get('description', '')
                        l_img = l.get('image_url')
                        l_line = f"- **{l_name}** ({l_loc}): {l_desc}"
                        if l_img:
                            l_line += f"\n  Lab Photo: ![{l_name}]({l_img})"
                            lab_images.append(l_img)
                        lab_lines.append(l_line)
                    
                    lab_title = f"{dname} ({dcode}) - Laboratories & Facilities"
                    if dcode == "COMP":
                        lab_title = "Computer Engineering / Computer Science & Engineering (COMP / CSE) - Laboratories & Facilities"
                    
                    chunks.append(TextChunk(
                        chunk_id=f"{school}_{df.stem}_labs",
                        title=lab_title,
                        category="facilities",
                        content="\n".join(lab_lines),
                        metadata={"school": school, "dept": dcode, "images": lab_images}
                    ))

    # 4. Placements
    placements = _load_json_safe(kb_path / "placements_stats.json")
    if isinstance(placements, dict):
        overall = placements.get("overall", {})
        rec_list = []
        for r in placements.get("top_recruiters", []):
            if isinstance(r, dict):
                rec_list.append(f"{r.get('company')} ({r.get('count')} offers)")
            else:
                rec_list.append(str(r))
        p_lines = [
            "Campus Placement Statistics & Training Cell (TPO):",
            f"- Total Placements: {overall.get('total_placements', 310)}",
            f"- Highest Package: {overall.get('highest_package_lpa', 6.0)} LPA",
            f"- Average Package: {overall.get('average_package_lpa', 2.2)} LPA",
            f"- Top Recruiting Companies: {', '.join(rec_list) if rec_list else 'Suchi Pvt Ltd, Kosmics, Reliance Jio, Tikona'}",
            "- Placement Activities: Aptitude training, soft skills workshops, mock technical interviews, campus drives."
        ]
        chunks.append(TextChunk(
            chunk_id="campus_placements",
            title="Campus Placements, Top Recruiters, Packages & TPO Cell",
            category="placement",
            content="\n".join(p_lines),
            metadata={"source": "placements_stats.json"}
        ))

    # 5. CAP Rounds & State Centralized Admission Process
    cap = _load_json_safe(kb_path / "cap.json")
    if isinstance(cap, dict):
        cap_lines = [
            "How to Apply for Admission to AIKTC (Centralised Admission Process - CAP):",
            "To apply for admission to Engineering, Pharmacy, or Architecture at AIKTC:",
            "  1. Online Registration: Register online on Maharashtra State CET Cell portal (cetcell.mahacet.org) and submit the application form.",
            "  2. Document Verification: Complete document verification online (e-Scrutiny) or at a physical Scrutiny Center (FC).",
            "  3. Merit List: Verify your name and details on the provisional and final State Merit Lists.",
            "  4. Option Form & Choice Filling: Fill option forms for CAP Rounds. Enter AIKTC Institute Choice Code (DTE Code: 3217 for Engineering).",
            "  5. Seat Allotment & Reporting: Accept allotted seat, download allotment letter, and report to AIKTC Campus with original documents and fees.",
            "Institute-Level & Vacant Seats: For vacant seats after CAP rounds, apply directly at the AIKTC Admissions Office (Helpline: +91 8104363070).",
            "Required Documents: MHT-CET/JEE Scorecard, 10th & 12th Marks Memo, School Leaving / Transfer Certificate, Domicile / Nationality Certificate, Minority Affidavit (for Muslim minority quota), Caste & Income Certificate (if applicable)."
        ]
        chunks.append(TextChunk(
            chunk_id="cap_admission_process",
            title="How to Apply for Admission to AIKTC - Centralised Admission Process (CAP) & Required Documents",
            category="admission_process",
            content="\n".join(cap_lines),
            metadata={"source": "cap.json", "school": "central"}
        ))

    # 6. Activities & Campus Life
    activities = _load_json_safe(kb_path / "activities.json")
    if isinstance(activities, dict):
        act_lines = ["Campus Life, Student Chapters & Technical Activities:"]
        for k, v in activities.items():
            if isinstance(v, list):
                act_lines.append(f"- {k.replace('_', ' ').capitalize()}: {', '.join(str(i) for i in v)}")
            elif isinstance(v, dict):
                act_lines.append(f"- {k.replace('_', ' ').capitalize()}: {json.dumps(v)}")
        chunks.append(TextChunk(
            chunk_id="campus_activities",
            title="Student Clubs, Professional Chapters (IEEE, CSI) & Technical Events",
            category="facilities",
            content="\n".join(act_lines),
            metadata={"source": "activities.json"}
        ))

    return chunks
