# backend/kb/markdown.py
"""
Convert the merged KB dict into a structured Markdown string for the LLM.

DESIGN PRINCIPLES
-----------------
1. Markdown tables are more reliably parsed by LLMs than raw JSON.
2. Units (percentile vs marks) are made explicit in section headers.
3. Modular KB data (overview, fees, departments) is rendered inline —
   the LLM sees one unified document, not separate file fragments.
4. Every section is optional — missing data is silently omitted.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _render_urls(data: dict) -> list[str]:
    """Helper to render all URL fields in a dictionary."""
    lines = []
    for key in sorted(data.keys()):
        if key.endswith("_url") and data[key]:
            label = key[:-4].replace('_', ' ').title()
            lines.append(f"- **{label} URL:** {data[key]}")
    return lines


def _faculty_table(faculty: list[dict], label: str = "Faculty") -> list[str]:
    """Render a faculty list as a Markdown table."""
    lines = [
        f"\n#### {label}",
        "| Name | Designation | Qualification | Experience | Image URL |",
        "|------|-------------|---------------|------------|-----------|",
    ]
    for f in faculty:
        img_url = f.get('image_url', '') or ''
        lines.append(
            f"| {f.get('name','')} | {f.get('designation','')} | "
            f"{f.get('qualification', f.get('specialization',''))} | "
            f"{f.get('experience','')} | {img_url} |"
        )
    return lines


def _cutoff_table(cutoffs: list[dict], unit_label: str, code: str) -> list[str]:
    """Render a cutoff table for a department."""
    lines = [
        f"\n#### {code} Cutoffs ({unit_label})",
        "| Year | Open | OBC | SC | ST | EWS | TFWS |",
        "|------|------|-----|----|----|-----|------|",
    ]
    for c in cutoffs:
        lines.append(
            f"| {c['year']} | {c.get('open','-')} | "
            f"{c.get('obc','-')} | {c.get('sc','-')} | {c.get('st','-')} | "
            f"{c.get('ews','-')} | {c.get('tfws','-')} |"
        )
    return lines


def _fees_table(fees: dict) -> list[str]:
    """Render fee programs as Markdown tables."""
    lines = []
    if not fees or not fees.get("programs"):
        return lines

    lines.append(f"\n### Fees ({fees.get('academic_year', '2025-26')})")
    for prog_key, prog in fees["programs"].items():
        prog_name = prog.get("program_type", prog_key.upper())
        lines.append(f"\n#### {prog_name}")
        lines.append("| Year | Tuition (₹) | Development (₹) | Total (₹) |")
        lines.append("|------|------------|-----------------|-----------|")
        for row in prog.get("annual_fees", []):
            lines.append(
                f"| {row.get('year','')} | {row.get('tuition_fees',0):,} | "
                f"{row.get('development_fees',0):,} | {row.get('total_fees',0):,} |"
            )
    if fees.get("notes"):
        lines.append(f"\n> {fees['notes']}")
    return lines


def _refund_section(refund: dict) -> list[str]:
    if not refund or not refund.get("policy"):
        return []
    return [
        "\n### Refund Policy",
        f"{refund['policy']}",
        f"*(Source: {refund.get('source', 'Prospectus 2025')})*",
    ]


def _labs_list(labs) -> list[str]:
    """Render labs — supports both list-of-str and list-of-dict."""
    if not labs:
        return []
    lines = []
    for lab in labs:
        if isinstance(lab, str):
            lines.append(f"- {lab}")
        elif isinstance(lab, dict):
            loc  = f" ({lab['location']})" if lab.get("location") else ""
            desc = f" — {lab['description']}" if lab.get("description") else ""
            cap  = f" · Capacity: {lab['capacity']}" if lab.get("capacity") else ""
            lines.append(f"- **{lab.get('name','')}**{loc}{desc}{cap}")
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# School renderers
# ─────────────────────────────────────────────────────────────────────────────

def _render_engineering(eng: dict) -> list[str]:
    lines = ["\n---\n## Engineering School"]

    # Basic Info
    if eng.get("school_name"):
        lines.append(f"- **School:** {eng['school_name']} (DTE code: {eng.get('dte_code','')})")
    if eng.get("autonomous"):
        lines.append("- **Status:** Autonomous Institute")
    if eng.get("affiliated_to"):
        lines.append(f"- **Affiliated to:** {eng['affiliated_to']}")
    if eng.get("dean"):
        dean = eng["dean"]
        dean_line = f"- **Dean:** {dean.get('name','')} · {dean.get('qualification','')}"
        if dean.get("image_url"):
            dean_line += f" · Image URL: {dean.get('image_url')}"
        lines.append(dean_line)
    if eng.get("accreditation"):
        lines.append(f"- **Accreditation:** {eng['accreditation']}")
    if eng.get("vision"):
        lines.append(f"- **Vision:** {eng['vision']}")
    if eng.get("mission"):
        lines.append(f"- **Mission:** {eng['mission']}")

    mission_elements = eng.get("mission_elements", [])
    if mission_elements:
        lines.append("\n### Mission Elements")
        for me in mission_elements:
            lines.append(f"- {me}")

    # Contact
    contact = eng.get("contact", {})
    if contact:
        lines.append("\n### Engineering Contact Information")
        if contact.get("address"):
            lines.append(f"- **Address:** {contact['address']}")
        if contact.get("phone"):
            lines.append(f"- **Phone:** {contact['phone']}")
        if contact.get("admission_engineering"):
            lines.append(f"- **Admission Contact:** {contact['admission_engineering']}")
        if contact.get("email"):
            lines.append(f"- **Email:** {contact['email']}")
        if contact.get("admissions_email"):
            lines.append(f"- **Admissions Email:** {contact['admissions_email']}")
        if contact.get("website"):
            lines.append(f"- **Website:** {contact['website']}")

    # Programs Offered
    programs = eng.get("programs_offered", {})
    if programs:
        lines.append("\n### Programs Offered")
        for p_key, p_val in programs.items():
            name = p_key.upper()
            if isinstance(p_val, dict):
                duration = f" ({p_val['duration']})" if "duration" in p_val else ""
                intake = f" · Intake: {p_val['intake']}" if "intake" in p_val else ""
                specs = p_val.get("specializations", [])
                spec_str = f" · Specializations: {', '.join(specs)}" if specs else ""
                field = p_val.get("field", "")
                field_str = f" · Field: {field}" if field else ""
                lines.append(f"- **{name}**{duration}{intake}{field_str}{spec_str}")

    # Admission process
    adm = eng.get("admission_process", {})
    if adm:
        lines.append("\n### Admission Process")
        if isinstance(adm, dict):
            for key, val in adm.items():
                label = key.replace('_', ' ').title()
                lines.append(f"- **{label}:** {val}")
        elif isinstance(adm, list):
            for step in adm:
                lines.append(f"**{step.get('title','')}:** {step.get('detail','')}")

    # Incubation Centre
    inc = eng.get("incubation_centre", {})
    if inc:
        lines.append(f"\n### Incubation Centre (Head: {inc.get('head', '')})")
        highlights = inc.get("highlights", {})
        if highlights:
            for k, v in highlights.items():
                label = k.replace('_', ' ').title()
                lines.append(f"- **{label}:** {v}")

    # Library
    lib = eng.get("library", {})
    if lib:
        lines.append(f"\n### Knowledge Resources & Relay Centre (KRRC) - Library")
        if lib.get("name"):
            lines.append(f"- **Name:** {lib['name']}")
        if lib.get("area_sqft"):
            lines.append(f"- **Area:** {lib['area_sqft']} sqft")
        lines.append(f"- **Volumes:** {lib.get('volumes', '')} | **Titles:** {lib.get('titles', '')}")
        lines.append(f"- **Journals:** National: {lib.get('national_journals', '')} · International: {lib.get('international_journals', '')}")
        resources = lib.get("e_resources", [])
        if resources:
            lines.append(f"- **E-Resources:** {', '.join(resources)}")
        if lib.get("website"):
            lines.append(f"- **Library Website:** {lib['website']}")

    # Campus
    campus = eng.get("campus", {})
    if campus:
        lines.append("\n### Campus Infrastructure")
        if campus.get("area_acres"):
            lines.append(f"- **Area:** {campus['area_acres']} acres")
        if campus.get("built_up_sqft"):
            lines.append(f"- **Built-up Area:** {campus['built_up_sqft']:,} sqft")
        if campus.get("established_year"):
            lines.append(f"- **Established:** {campus['established_year']}")

    # Scholarships
    scholarships = eng.get("scholarships", {})
    if scholarships:
        lines.append("\n### Scholarships & Fee Waivers")
        for k, v in scholarships.items():
            label = k.replace('_', ' ').title()
            lines.append(f"- **{label}:** {v}")

    # School-level fees
    lines.extend(_fees_table(eng.get("fees", {})))

    # Refund policy
    lines.extend(_refund_section(eng.get("refund_policy", {})))

    # Departments
    for dept in eng.get("departments", []):
        code = dept.get("code", "?")
        lines.append(f"\n### Engineering — {dept.get('name','?')} ({code})")
        
        # HOD / Coordinator rendering
        hod = dept.get("hod") or dept.get("programme_coordinator")
        if isinstance(hod, dict):
            designation = hod.get("designation", "HOD")
            hod_line = (
                f"- **{designation}:** {hod.get('name','')} · "
                f"{hod.get('qualification','')} · Experience: {hod.get('experience','')}"
            )
            if hod.get("image_url"):
                hod_line += f" · Image URL: {hod.get('image_url')}"
            lines.append(hod_line)
        elif hod:
            hod_line = f"- **HOD:** {hod}"
            if dept.get("hod_image_url"):
                hod_line += f" · Image URL: {dept.get('hod_image_url')}"
            lines.append(hod_line)

        lines.append(f"- **Intake:** {dept.get('intake', '')} seats")
        if dept.get("duration"):
            lines.append(f"- **Duration:** {dept['duration']}")
        if dept.get("established_year"):
            lines.append(f"- **Established Year:** {dept['established_year']}")
        if dept.get("eligibility"):
            lines.append(f"- **Eligibility:** {dept['eligibility']}")
        if dept.get("vision"):
            lines.append(f"- **Vision:** {dept['vision']}")
        if dept.get("mission"):
            lines.append(f"- **Mission:** {dept['mission']}")

        # Postgraduate details
        postgrad = dept.get("postgraduate")
        if postgrad:
            mtech_specs = postgrad.get("mtech_specializations", [])
            phd_avail = postgrad.get("phd_available", False)
            if mtech_specs:
                lines.append(f"- **M.Tech Specializations:** {', '.join(mtech_specs)}")
            if phd_avail:
                lines.append("- **Ph.D Program Available:** Yes")

        # Faculty
        faculty = dept.get("faculty", [])
        if faculty:
            lines.extend(_faculty_table(faculty, f"{code} Faculty"))

        # Labs
        labs = dept.get("labs", [])
        if labs:
            lines.append(f"\n#### {code} Labs")
            lines.extend(_labs_list(labs))

        # Additional Features
        features = dept.get("additional_features", [])
        if features:
            lines.append("\n#### Additional Features")
            for f in features:
                lines.append(f"- {f}")

        # Cutoffs
        if dept.get("cutoffs"):
            unit_label = f"MHT-CET {dept.get('cutoff_unit', 'percentile')}"
            lines.extend(_cutoff_table(dept["cutoffs"], unit_label, code))

        # Alumni testimonial
        alum = dept.get("alumni_testimonial", {})
        if alum:
            batch_or_desg = alum.get('batch') or alum.get('designation')
            batch_str = f" ({batch_or_desg})" if batch_or_desg else ""
            lines.append(
                f"\n> *\"{alum.get('quote','')}\"*  \n"
                f"> — {alum.get('name','')}{batch_str}"
            )

        # Department Links
        dept_urls = _render_urls(dept)
        if dept_urls:
            lines.append("\n#### Official Links")
            lines.extend(dept_urls)

    # Placements
    placements = eng.get("placements", {})
    if placements:
        lines.append("\n### Engineering Placements")
        if placements.get("placement_cell"):
            lines.append(f"- **Placement Cell:** {placements['placement_cell']}")
        activities = placements.get("activities", [])
        if activities:
            lines.append("\n#### Placement Activities")
            for act in activities:
                lines.append(f"- {act}")
        recruiters = placements.get("recruiters_partial_list", [])
        if recruiters:
            lines.append(f"- **Recruiters:** {', '.join(recruiters)}")

    return lines


def _render_pharmacy(pharm: dict) -> list[str]:
    lines = ["\n---\n## Pharmacy School"]

    # Overview fields
    if pharm.get("school_name"):
        lines.append(f"- **School:** {pharm['school_name']} (DTE code: {pharm.get('dte_code','')})")
    if pharm.get("accreditation"):
        lines.append(f"- **Accreditation:** {pharm['accreditation']}")
    if pharm.get("contact"):
        c = pharm["contact"]
        lines.append(f"- **Admission Contact:** {c.get('admission_pharmacy','')} · {c.get('email','')}")

    # Admission process
    adm = pharm.get("admission_process", {})
    if adm:
        lines.append("\n### Pharmacy Admission Process")
        for prog, detail in adm.items():
            lines.append(f"- **{prog.replace('_', ' ').title()}:** {detail}")

    # Fees table
    lines.extend(_fees_table(pharm.get("fees", {})))

    # Refund policy
    lines.extend(_refund_section(pharm.get("refund_policy", {})))

    # Departments
    for dept in pharm.get("departments", []):
        code = dept.get("code", "?")
        lines.append(f"\n### Pharmacy — {dept.get('name','?')} ({code})")

        # HOD — may be nested dict (dpharm) or dean dict (bpharm)
        hod = dept.get("hod") or dept.get("dean", {})
        if isinstance(hod, dict):
            hod_line = (
                f"- **HOD/Dean:** {hod.get('name','')} · "
                f"{hod.get('qualification','')} · {hod.get('experience','')}"
            )
            if hod.get("image_url"):
                hod_line += f" · Image URL: {hod.get('image_url')}"
            lines.append(hod_line)
        elif hod:
            hod_line = f"- **HOD/Dean:** {hod}"
            if dept.get("hod_image_url"):
                hod_line += f" · Image URL: {dept.get('hod_image_url')}"
            lines.append(hod_line)

        lines.append(f"- **Intake:** {dept.get('intake', '')} seats")
        lines.append(f"- **Duration:** {dept.get('duration', '')}")

        if dept.get("eligibility"):
            lines.append(f"- **Eligibility:** {dept['eligibility']}")

        # Faculty (only if it's a proper list, not string)
        faculty = dept.get("faculty", [])
        if isinstance(faculty, list) and faculty:
            lines.extend(_faculty_table(faculty, f"{code} Faculty"))

        # Labs
        labs = dept.get("labs", [])
        if labs:
            lines.append(f"\n#### {code} Labs")
            lines.extend(_labs_list(labs))

        # Achievements
        achievements = dept.get("achievements", [])
        if achievements:
            lines.append(f"\n#### {code} Achievements")
            for ach in achievements:
                lines.append(f"- {ach}")

        # Cutoffs
        if dept.get("cutoffs"):
            unit_label = f"MHT-CET {dept.get('cutoff_unit', 'percentile')}"
            lines.extend(_cutoff_table(dept["cutoffs"], unit_label, code))

        # Alumni testimonial
        alum = dept.get("alumni_testimonial", {})
        if alum:
            lines.append(
                f"\n> *\"{alum.get('quote','')}\"*  \n"
                f"> — {alum.get('name','')} ({alum.get('designation','')})"
            )

        # Department Links
        dept_urls = _render_urls(dept)
        if dept_urls:
            lines.append("\n#### Official Links")
            lines.extend(dept_urls)

    # Placements
    placements = pharm.get("placements", {})
    if placements:
        lines.append("\n### Pharmacy Placements")
        for h in placements.get("highlights", []):
            lines.append(f"- {h}")

    return lines


def _render_architecture(arch: dict) -> list[str]:
    lines = ["\n---\n## Architecture School"]

    # Overview fields
    if arch.get("school_name"):
        lines.append(
            f"- **School:** {arch['school_name']} "
            f"(DTE: {arch.get('dte_code','')} · COA: {arch.get('coa_code','')})"
        )
    if arch.get("accreditation"):
        lines.append(f"- **Accreditation:** {arch['accreditation']}")
    if arch.get("contact"):
        c = arch["contact"]
        lines.append(f"- **Admission Contact:** {c.get('admission_architecture','')} · {c.get('email','')}")

    # Admission process
    adm = arch.get("admission_process", {})
    if adm:
        lines.append("\n### Architecture Admission Process")
        for prog, detail in adm.items():
            lines.append(f"- **{prog.upper()}:** {detail}")

    # Fees table
    lines.extend(_fees_table(arch.get("fees", {})))

    # Refund policy
    lines.extend(_refund_section(arch.get("refund_policy", {})))

    # Departments
    for dept in arch.get("departments", []):
        code = dept.get("code", "?")
        lines.append(f"\n### Architecture — {dept.get('name','?')} ({code})")
        lines.append(f"- **Intake:** {dept.get('intake', '')} seats")
        lines.append(f"- **Duration:** {dept.get('duration', '')}")

        # HOD / Dean rendering
        hod = dept.get("hod") or dept.get("dean")
        if isinstance(hod, dict):
            hod_line = (
                f"- **HOD/Dean:** {hod.get('name','')} · "
                f"{hod.get('qualification','')} · {hod.get('experience','')}"
            )
            if hod.get("image_url"):
                hod_line += f" · Image URL: {hod.get('image_url')}"
            lines.append(hod_line)
        elif hod:
            hod_line = f"- **HOD/Dean:** {hod}"
            if dept.get("hod_image_url"):
                hod_line += f" · Image URL: {dept.get('hod_image_url')}"
            lines.append(hod_line)

        if dept.get("eligibility"):
            lines.append(f"- **Eligibility:** {dept['eligibility']}")
        if dept.get("description"):
            lines.append(f"\n{dept['description']}")

        # Faculty
        faculty = dept.get("faculty", [])
        if isinstance(faculty, list) and faculty:
            lines.extend(_faculty_table(faculty, f"{code} Faculty"))
        elif isinstance(faculty, str) and faculty:
            lines.append(f"\n*Faculty: {faculty}*")

        # Labs
        labs = dept.get("labs", [])
        if labs:
            lines.append(f"\n#### {code} Labs")
            lines.extend(_labs_list(labs))

        # Cutoffs — B.Arch uses NATA marks
        if dept.get("cutoffs"):
            unit_label = "NATA marks out of 200"
            lines.extend(_cutoff_table(dept["cutoffs"], unit_label, code))

        # Alumni testimonial
        alum = dept.get("alumni_testimonial", {})
        if alum:
            lines.append(
                f"\n> *\"{alum.get('quote','')}\"*  \n"
                f"> — {alum.get('name','')} ({alum.get('designation','')})"
            )

        # Department Links
        dept_urls = _render_urls(dept)
        if dept_urls:
            lines.append("\n#### Official Links")
            lines.extend(dept_urls)

    # Events
    events = arch.get("events_and_workshops", [])
    if events:
        lines.append("\n### Architecture Events & Workshops (2024-25)")
        for e in events:
            lines.append(f"- {e}")

    return lines


def _render_activities(act: dict) -> list[str]:
    """Render campus activities, clubs, competitions, and committees as Markdown."""
    lines = ["\n---\n## Campus Activities, Clubs & Competitions"]

    # Festivals
    festivals = act.get("festivals", [])
    if festivals:
        lines.append("\n### Flagship Annual Festivals")
        for f in festivals:
            lines.append(f"\n#### {f.get('name', '')} ({f.get('type', '')})")
            lines.append(f"{f.get('description', '')}")
            cats = f.get("categories", {})
            if cats:
                for cat_name, items in cats.items():
                    label = cat_name.replace('_', ' & ').title()
                    lines.append(f"- **{label}**: {', '.join(items)}")
            
            lines.extend(_render_urls(f))

    # Clubs
    clubs = act.get("clubs", [])
    if clubs:
        lines.append("\n### Student Clubs & Technical Societies")
        for c in clubs:
            lines.append(f"\n#### {c.get('name', '')}")
            if c.get("department"):
                lines.append(f"- **Department/Affiliation**: {c['department']}")
            lines.append(f"- **Description**: {c.get('description', '')}")
            
            activities = c.get("activities", [])
            if activities:
                lines.append("- **Key Activities**:")
                for a in activities:
                    lines.append(f"  - {a}")
            
            events = c.get("events", [])
            if events:
                lines.append("- **Timeline of Events & Workshops**:")
                for e in events:
                    lines.append(f"  - *{e.get('date', 'N/A')}*: {e.get('name', '')}")
            
            achievements = c.get("achievements", [])
            if achievements:
                lines.append("- **Student Achievements & Highlights**:")
                for ach in achievements:
                    lines.append(f"  - {ach}")
            
            internships = c.get("internships", [])
            if internships:
                lines.append("- **Student Internships**:")
                for inter in internships:
                    lines.append(f"  - {inter}")
            
            lines.extend(_render_urls(c))

    # Competitions
    competitions = act.get("competitions", [])
    if competitions:
        lines.append("\n### Key Competitions")
        for comp in competitions:
            lines.append(f"\n#### {comp.get('name', '')} ({comp.get('type', '')})")
            if comp.get("organizer"):
                lines.append(f"- **Organizer**: {comp['organizer']}")
            lines.append(f"- **Description**: {comp.get('description', '')}")
            
            lines.extend(_render_urls(comp))

    # Committees
    committees = act.get("committees", [])
    if committees:
        lines.append("\n### Committees & Extension Cells")
        for comm in committees:
            lines.append(f"\n#### {comm.get('name', '')}")
            lines.append(f"- **Description**: {comm.get('description', '')}")
            
            key_events = comm.get("key_events", [])
            if key_events:
                lines.append(f"- **Key Responsibilities/Events**: {', '.join(key_events)}")
            
            events = comm.get("events", [])
            if events:
                lines.append("- **Past & Planned Activities**:")
                for e in events:
                    lines.append(f"  - *{e.get('date', 'N/A')}*: {e.get('name', '')}")
            
            achievements = comm.get("achievements", [])
            if achievements:
                lines.append("- **Notable Achievements & Medals**:")
                for ach in achievements:
                    lines.append(f"  - {ach}")
            
            lines.extend(_render_urls(comm))

    return lines


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def kb_to_markdown(kb: dict) -> str:
    """
    Convert the merged KB dict to a structured Markdown string.

    The output is injected verbatim into the LLM system prompt.
    Every section is conditional — missing data is silently skipped.
    """
    lines: list[str] = ["# AIKTC College Knowledge Base\n"]

    # ── Common section ────────────────────────────────────────────────────
    common = kb.get("common", {})
    lines.append("## College Information")
    lines.append(f"- **Name:** {common.get('name', 'AIKTC')}")
    lines.append(f"- **Short Name:** {common.get('short_name', 'AIKTC')}")
    lines.append(f"- **Address:** {common.get('address', '')}")
    lines.append(f"- **Website:** {common.get('website', '')}")
    lines.append(f"- **Timing:** {common.get('timing', '')}")
    lines.append(f"- **Established:** {common.get('established', '')}")
    lines.append(f"- **Affiliated to:** {common.get('affiliated_to', '')}")
    approved = common.get("approved_by", [])
    if approved:
        lines.append(f"- **Approved by:** {', '.join(approved)}")

    # Director
    director = common.get("director", {})
    if director:
        lines.append("\n### Director")
        lines.append(f"- **Name:** {director.get('name', '')}")
        lines.append(f"- **Qualification:** {director.get('qualification', '')}")
        lines.append(f"- **Email:** {director.get('email', '')}")
        lines.append(f"- **Phone:** {director.get('phone', '')}")
        if director.get("image_url"):
            lines.append(f"- **Image URL:** {director.get('image_url')}")

    # Principal
    principal = common.get("principal", {})
    if principal:
        lines.append("\n### Principal")
        lines.append(f"- **Name:** {principal.get('name', '')}")
        lines.append(f"- **Qualification:** {principal.get('qualification', '')}")
        lines.append(f"- **Email:** {principal.get('email', '')}")
        lines.append(f"- **Phone:** {principal.get('phone', '')}")
        if principal.get("image_url"):
            lines.append(f"- **Image URL:** {principal.get('image_url')}")

    # Contacts
    contacts = common.get("contacts", {})
    if contacts:
        lines.append("\n### Contact Information")
        for label, info in contacts.items():
            lines.append(f"- **{label}:** {info}")

    # Important dates
    dates = common.get("important_dates", {})
    if dates:
        lines.append("\n### Important Dates")
        for key, val in dates.items():
            lines.append(f"- **{key.replace('_',' ').title()}:** {val}")

    # Hostel
    hostel = common.get("hostel", {})
    if hostel and hostel.get("available"):
        lines.append("\n### Hostel")
        lines.append(f"- Boys capacity: {hostel.get('boys_capacity','')} | Girls capacity: {hostel.get('girls_capacity','')}")
        lines.append(f"- Fees per year: ₹{hostel.get('fees_per_year', 0):,} | Mess per month: ₹{hostel.get('mess_per_month', 0):,}")
        fac = hostel.get("facilities", [])
        if fac:
            lines.append(f"- Facilities: {', '.join(fac)}")

    # ── Schools ───────────────────────────────────────────────────────────
    if kb.get("engineering"):
        lines.extend(_render_engineering(kb["engineering"]))

    if kb.get("pharmacy"):
        lines.extend(_render_pharmacy(kb["pharmacy"]))

    if kb.get("architecture"):
        lines.extend(_render_architecture(kb["architecture"]))

    if kb.get("activities"):
        lines.extend(_render_activities(kb["activities"]))

    return "\n".join(lines)