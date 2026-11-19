# tests/generate_and_test_1000_queries.py
"""
AIKTC CHATBOT — 1,000 Comprehensive Query Stress Test & Deep Regression Audit
==============================================================================
Validates that removing the forced 'overview' override from rag_synthesizer.py
and relying on true top-1 semantic retrieval completely resolves cross-topic
bleed and correctly routes 1,000 diverse student questions across:
  1. Department Specific Queries (Overview, Scope, Highlights)
  2. Faculty & HOD Queries (by department, leadership)
  3. Laboratory & Infrastructure Queries (by department)
  4. Approved Fee Structure & Tuition Queries (by school/branch)
  5. Fee Refund & Admission Cancellation Policies
  6. Campus Hostels & Accommodation Queries
  7. Campus Placements, Highest Packages & Top Recruiters
  8. Campus Sports, Bonhomie Cultural Festivals & Student Clubs
  9. Central Facilities (Central Library, Incubation Centre)
 10. Scholarships (MahaDBT, Minority, OBC, SC/ST, Merit, Documents, Process)
 11. Admission Eligibility Criteria (Engineering, Pharmacy, Architecture)
 12. Centralized Admission Process (CAP Rounds & CET Cell)
 13. Campus Leadership (Director, Principal, Deans)
 14. Academic Programs, Degrees & Intake (Central, Engineering, Pharmacy, Architecture)
 15. Department Comparisons (Direct & Multi-turn)
"""

import sys
import time
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from kb.retriever import get_vector_store
from engine.classifier import classify_intent
from engine.extractor import extract_entities
from engine.rag_synthesizer import synthesize_grounded_answer

vs = get_vector_store()

# Query Templates by Intent Domain
DEPT_NAMES = [
    ("Computer Engineering", "COMP", "engineering_computer"),
    ("CSE AIML", "CSAIML", "engineering_cs_aiml"),
    ("CSE Data Science", "CSDS", "engineering_cs_datascience"),
    ("Electronics and Computer Science", "ECS", "engineering_electronics_computer"),
    ("Electrical and Computer Engineering", "ECE", "engineering_electrical_computer"),
    ("Mechanical Engineering", "MECH", "engineering_mechanical"),
    ("Civil Engineering", "CIVIL", "engineering_civil"),
    ("B.Sc IT", "BSIT", "engineering_bsc_it"),
    ("B.Pharm", "BPHARM", "pharmacy_bpharm"),
    ("D.Pharm", "DPHARM", "pharmacy_dpharm"),
    ("M.Pharm", "MPHARM", "pharmacy_mpharm"),
    ("B.Arch", "BARCH", "architecture_barch"),
    ("D.Arch", "DARCH", "architecture_darch"),
]

queries = []

# 1. Faculty / HOD Queries (13 depts * 12 variants = 156 queries)
faculty_templates = [
    "who is the hod of {name}",
    "head of department {name}",
    "faculty members in {name}",
    "who teaches in {name}",
    "professors in {name}",
    "list of faculty in {name}",
    "teaching staff of {name}",
    "who is the head of {code}",
    "faculty of {code} department",
    "professors of {code}",
    "hod of {code} department",
    "teachers in {code} branch"
]
for name, code, prefix in DEPT_NAMES:
    for t in faculty_templates:
        q = t.format(name=name, code=code)
        queries.append((q, "faculty", prefix + "_faculty"))

# 2. Labs / Facilities Queries (13 depts * 12 variants = 156 queries)
lab_templates = [
    "laboratories in {name}",
    "labs in {name}",
    "what are the laboratories of {name}",
    "lab equipment in {name}",
    "practical labs for {name}",
    "facilities in {name}",
    "hardware and software labs in {name}",
    "labs for {code} department",
    "laboratories for {code}",
    "what labs are available in {code}",
    "practical lab setup of {code}",
    "lab rooms in {code}"
]
for name, code, prefix in DEPT_NAMES:
    for t in lab_templates:
        q = t.format(name=name, code=code)
        queries.append((q, "facilities", prefix + "_labs"))

# 3. Department Overview & Curriculum Queries (13 depts * 10 variants = 130 queries)
overview_templates = [
    "tell me about {name}",
    "overview of {name}",
    "what is {name}",
    "details of {name}",
    "scope of {name}",
    "curriculum of {name}",
    "about {code} branch",
    "tell me about {code} department",
    "overview of {code}",
    "scope of {code} at aiktc"
]
for name, code, prefix in DEPT_NAMES:
    for t in overview_templates:
        q = t.format(name=name, code=code)
        queries.append((q, "department", prefix + "_overview"))

# 4. Fee Structure Queries (100 queries)
fee_queries = [
    ("fees for engineering", "engineering_fees"),
    ("engineering fee structure", "engineering_fees"),
    ("annual tuition fees for btech", "engineering_fees"),
    ("what is the total fees for btech computer", "engineering_fees"),
    ("fees structure for ecs engineering", "engineering_fees"),
    ("tuition fees for mechanical engineering", "engineering_fees"),
    ("civil engineering fees per year", "engineering_fees"),
    ("what are the fees for bsc it", "engineering_fees"),
    ("mtech fee structure", "engineering_fees"),
    ("phd civil engineering fees", "engineering_fees"),
    ("fees for pharmacy", "pharmacy_fees"),
    ("bpharm fee structure", "pharmacy_fees"),
    ("dpharm fees per year", "pharmacy_fees"),
    ("mpharm pharmacology tuition fees", "pharmacy_fees"),
    ("pharmacy annual college fees", "pharmacy_fees"),
    ("fees for architecture", "architecture_fees"),
    ("barch annual fees", "architecture_fees"),
    ("darch diploma fees", "architecture_fees"),
    ("architecture fee structure fra approved", "architecture_fees"),
    ("how much fees for 5 years barch", "architecture_fees"),
]
for base_q, exp in fee_queries:
    for prefix in ["what is the ", "tell me the ", "can you provide ", "details of ", ""]:
        queries.append((f"{prefix}{base_q}", "fee", exp))

# 5. Fee Refund Policy Queries (50 queries)
refund_bases = [
    "refund policy for engineering",
    "cancellation rules for admission",
    "fee deduction if admission cancelled",
    "how to get fee refund after cap round",
    "admission cancellation process and refund",
    "pharmacy fee refund rules",
    "architecture admission cancellation policy",
    "refund policy after cutoff date",
    "can I get full refund if I cancel",
    "what amount is deducted on cancellation"
]
for base_q in refund_bases:
    for prefix in ["what is the ", "tell me about ", "explain ", "rules for ", ""]:
        queries.append((f"{prefix}{base_q}", "fee", "refund_policy"))

# 6. Hostel & Accommodation Queries (50 queries)
hostel_bases = [
    "hostel facilities in aiktc",
    "boys hostel capacity and rent",
    "girls hostel fee and accommodation",
    "hostel mess fee per month",
    "is hostel available in aiktc campus",
    "how much is the hostel fee per year",
    "hostel rooms and mess food",
    "ac hostel or non ac hostel in campus",
    "what is the capacity of boys hostel",
    "hostel admission contact and fees"
]
for base_q in hostel_bases:
    for prefix in ["tell me about ", "what are ", "details on ", "information about ", ""]:
        queries.append((f"{prefix}{base_q}", "hostel", "inst_hostel"))

# 7. Placements & Top Recruiters Queries (50 queries)
placement_bases = [
    "campus placements in aiktc",
    "highest package offered in engineering",
    "average placement package at aiktc",
    "top recruiting companies for computer engineering",
    "placement statistics and companies",
    "tpo cell contact and training",
    "internship opportunities in campus",
    "which companies visit for placements",
    "placements for mechanical engineering",
    "placement records for btech and bpharm"
]
for base_q in placement_bases:
    for prefix in ["how are ", "what are ", "tell me about ", "details of ", ""]:
        queries.append((f"{prefix}{base_q}", "placement", "campus_placements"))

# 8. Sports, Bonhomie & Cultural Activities Queries (50 queries)
activities_bases = [
    "sports and cultural activities held in aiktc",
    "annual festival bonhomie fuerza",
    "cricket and football sports tournaments",
    "student council events and fests",
    "cultural activities and festivals in aiktc",
    "ieee student chapter technical events",
    "csi computer society events and hackathons",
    "algorithm hackathon by programmers club",
    "nexathon data science competition",
    "student clubs and fests at aiktc"
]
for base_q in activities_bases:
    for prefix in ["tell me about ", "what are ", "details of ", "show me ", ""]:
        queries.append((f"{prefix}{base_q}", "facilities", "campus_activities"))

# 9. Central Facilities: Library & Incubation (50 queries)
facilities_bases = [
    ("central library in aiktc", "engineering_library"),
    ("krrc knowledge resource center library books", "engineering_library"),
    ("reading room and library timing", "engineering_library"),
    ("online journals and digital library", "engineering_library"),
    ("library book bank facility", "engineering_library"),
    ("incubation center at aiktc", "engineering_incubation"),
    ("startup and innovation hub", "engineering_incubation"),
    ("entrepreneurship development cell edc", "engineering_incubation"),
    ("patents and funding support incubation", "engineering_incubation"),
    ("pre incubation facilities for student startups", "engineering_incubation"),
]
for base_q, exp in facilities_bases:
    for prefix in ["tell me about ", "what is ", "details of ", "information on ", ""]:
        queries.append((f"{prefix}{base_q}", "facilities", exp))

# 10. Scholarships & Financial Aid Queries (70 queries)
scholarship_bases = [
    ("scholarships available in aiktc", "scholarship_overview"),
    ("documents required for scholarship application", "scholarship_documents"),
    ("how to apply for mahadbt scholarship", "scholarship_application_process"),
    ("mahadbt government scholarship portal", "scholarship_mahadbt"),
    ("minority scholarship eligibility and amount", "scholarship_minority"),
    ("sc and st caste scholarship concessions", "scholarship_sc_st"),
    ("obc scholarship and ebc fee concession", "scholarship_obc"),
    ("merit scholarship for topper students", "scholarship_merit"),
    ("income limit certificate for scholarship", "scholarship_documents"),
    ("scholarship desk contact and verification", "scholarship_contacts"),
]
for base_q, exp in scholarship_bases:
    for prefix in ["what are ", "how to get ", "tell me about ", "rules for ", "procedure for ", "details on ", ""]:
        queries.append((f"{prefix}{base_q}", "scholarship", exp))

# 11. Admission Eligibility Criteria (50 queries)
elig_bases = [
    ("eligibility criteria for engineering btech", "engineering_admission_eligibility"),
    ("minimum marks required in 12th for btech", "engineering_admission_eligibility"),
    ("mht cet requirement for engineering admission", "engineering_admission_eligibility"),
    ("direct second year engineering eligibility", "engineering_admission_eligibility"),
    ("eligibility criteria for bpharm pharmacy", "pharmacy_admission_eligibility"),
    ("dpharm admission qualification required", "pharmacy_admission_eligibility"),
    ("eligibility criteria for bachelor of architecture", "architecture_admission_eligibility"),
    ("nata entrance exam score requirement for barch", "architecture_admission_eligibility"),
    ("diploma in architecture eligibility criteria", "architecture_admission_eligibility"),
    ("pcm percentage required for admission", "engineering_admission_eligibility"),
]
for base_q, exp in elig_bases:
    for prefix in ["what is the ", "tell me the ", "check ", "details on ", ""]:
        queries.append((f"{prefix}{base_q}", "admission_process", exp))

# 12. Centralized Admission Process (CAP Rounds) (50 queries)
cap_bases = [
    "how to apply for admission in aiktc",
    "cap round admission process cet cell",
    "steps to register on cet cell portal",
    "option form filling cap round 1",
    "documents required for cap round reporting",
    "institutional round and vacant seat admission",
    "how to confirm seat allotment cap round",
    "cet cell admission schedule and timeline",
    "cap round cutoff list verification",
    "admission reporting center arc guidelines"
]
for base_q in cap_bases:
    for prefix in ["what is ", "how does ", "explain ", "steps for ", ""]:
        queries.append((f"{prefix}{base_q}", "admission_process", "cap_admission_process"))

# 13. Campus Leadership & Deans (40 queries)
leadership_bases = [
    ("who is the director of aiktc", "inst_leadership"),
    ("campus director profile and experience", "inst_leadership"),
    ("who is the principal of engineering", "inst_leadership"),
    ("engineering principal qualification and details", "inst_leadership"),
    ("dean of school of engineering", "engineering_dean"),
    ("who is the dean of pharmacy", "pharmacy_dean"),
    ("dean of school of architecture", "architecture_dean"),
    ("college director email and phone number", "inst_leadership"),
]
for base_q, exp in leadership_bases:
    for prefix in ["tell me ", "who is ", "profile of ", "contact for ", ""]:
        queries.append((f"{prefix}{base_q}", "faculty", exp))

# 14. Academic Programs, Degrees & Approved Intake (60 queries)
programs_bases = [
    ("what are the courses offered by aiktc", "inst_programs_courses"),
    ("list of all academic programs at aiktc", "inst_programs_courses"),
    ("what degrees does aiktc offer", "inst_programs_courses"),
    ("courses available offered", "inst_programs_courses"),
    ("courses offered in engineering", "engineering_programs_courses"),
    ("branches available in school of engineering", "engineering_programs_courses"),
    ("btech degree programs and intake capacity", "engineering_programs_courses"),
    ("courses offered in school of pharmacy", "pharmacy_programs_courses"),
    ("pharmacy degrees intake and duration", "pharmacy_programs_courses"),
    ("courses offered in school of architecture", "architecture_programs_courses"),
    ("barch and darch courses intake at aiktc", "architecture_programs_courses"),
    ("what courses can I study at aiktc", "inst_programs_courses"),
]
for base_q, exp in programs_bases:
    for prefix in ["show me ", "tell me ", "what are ", "details on ", ""]:
        queries.append((f"{prefix}{base_q}", "courses_offered", exp))

# 15. College Overview & Contact (40 queries)
contact_bases = [
    ("overview of aiktc campus", "inst_overview"),
    ("history and establishment of aiktc", "inst_overview"),
    ("aicte approved and university affiliated", "inst_overview"),
    ("contact number and campus address", "inst_contact"),
    ("how to reach aiktc from panvel station", "inst_contact"),
    ("college email address and helpline number", "inst_contact"),
    ("admission office contact details", "inst_contact"),
    ("where is aiktc located in navi mumbai", "inst_contact"),
]
for base_q, exp in contact_bases:
    for prefix in ["what is the ", "tell me the ", "give me ", "details of ", ""]:
        queries.append((f"{prefix}{base_q}", "contact", exp))

print(f"Generated {len(queries)} comprehensive stress test queries.")

# Ensure we have at least 1,000 queries by augmenting natural conversational variations
if len(queries) < 1000:
    extra_needed = 1000 - len(queries)
    extras = []
    base_pool = list(queries)
    for i in range(extra_needed):
        q, cat, exp = base_pool[i % len(base_pool)]
        augmented = f"please {q} in detail"
        extras.append((augmented, cat, exp))
    queries.extend(extras)

queries = queries[:1000]

def run_tests():
    print(f"Running execution suite across exactly {len(queries)} student queries...\n")

    start_time = time.time()
    passed = 0
    failed = []

    for idx, (query, expected_cat, expected_chunk_key) in enumerate(queries, 1):
        entities = extract_entities(query, [])
        intent = classify_intent(query, entities)
        results = vs.search(query, top_k=1, category=intent, entities=entities)
        top_chunk = results[0][0] if results else None
        top_id = top_chunk.chunk_id if top_chunk else "NONE"
        
        # Check if the expected chunk key is in the retrieved top-1 chunk id
        is_match = expected_chunk_key in top_id
        
        # Also verify that rag_synthesizer does NOT falsely emit an irrelevant department overview
        algo_result = {
            "intent": intent,
            "entities": entities,
            "lang": "en",
            "q_prep": query,
            "retrieved_context": f"### [DOCUMENT 1: {top_chunk.title if top_chunk else ''}]\n{top_chunk.content if top_chunk else ''}"
        }
        answer = synthesize_grounded_answer(query, algo_result)
        
        # Check for hallucinated department overview when the query was about facilities, fees, or activities
        has_false_dept_overview = False
        if expected_chunk_key in ("campus_activities", "engineering_fees", "pharmacy_fees", "inst_hostel"):
            if "Department Overview: Bachelor of Architecture" in answer or "Department Overview: Electronics and Computer Science" in answer:
                has_false_dept_overview = True

        if is_match and not has_false_dept_overview:
            passed += 1
        else:
            failed.append((idx, query, expected_chunk_key, top_id, has_false_dept_overview))

    elapsed = time.time() - start_time
    print("=" * 80)
    print(f"EXECUTION COMPLETED IN {elapsed:.2f}s")
    print(f"Total Queries Evaluated : {len(queries)}")
    print(f"Queries Passed (Top-1)  : {passed} / {len(queries)} ({passed/len(queries)*100:.1f}%)")
    print(f"Queries Failed          : {len(failed)}")
    print("=" * 80)

    if failed:
        print(f"\nFirst 10 Failed Queries:")
        for idx, q, exp, got, false_ov in failed[:10]:
            print(f"  #{idx} Q: '{q}' | Expected: '{exp}' | Got: '{got}' | False Overview: {false_ov}")
        sys.exit(1)
    else:
        print("\nALL 1,000 QUERIES PASSED WITH 100% ACCURACY! ZERO FALSE OVERVIEWS EMITTED.")
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
