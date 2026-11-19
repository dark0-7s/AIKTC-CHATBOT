import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from kb.retriever import get_vector_store
from engine.classifier import classify_intent
from engine.extractor import extract_entities

vs = get_vector_store()

test_queries = [
    # Fees & Refund
    ('fees for engineering', 'engineering_fees'),
    ('fees for pharmacy', 'pharmacy_fees'),
    ('fees for architecture', 'architecture_fees'),
    ('hostel fee', 'inst_hostel'),
    ('refund policy for engineering', 'engineering_refund_policy'),
    ('cancellation rules', 'refund_policy'),

    # Faculty & Leadership
    ('who is the director', 'inst_leadership'),
    ('principal of engineering', 'inst_leadership'),
    ('dean of engineering', 'engineering_dean'),
    ('dean of pharmacy', 'pharmacy_dean'),
    ('dean of architecture', 'architecture_dean'),
    ('faculty of computer engineering', 'engineering_computer_faculty'),
    ('faculty in civil engineering', 'engineering_civil_faculty'),
    ('hod of mechanical engineering', 'engineering_mechanical_faculty'),

    # Facilities & Labs
    ('labs for computer engineering', 'engineering_computer_labs'),
    ('labs for mechanical', 'engineering_mechanical_labs'),
    ('central library', 'engineering_library'),
    ('incubation center', 'engineering_incubation'),
    ('student clubs and technical events', 'campus_activities'),

    # Scholarships
    ('scholarships in aiktc', 'scholarship_overview'),
    ('documents for scholarship', 'scholarship_documents'),
    ('mahadbt scholarship', 'scholarship_mahadbt'),
    ('minority scholarship', 'scholarship_minority'),
    ('sc st scholarship', 'scholarship_sc_st'),
    ('obc scholarship', 'scholarship_obc'),

    # Admission & Eligibility
    ('eligibility for engineering', 'engineering_admission_eligibility'),
    ('eligibility for pharmacy', 'pharmacy_admission_eligibility'),
    ('eligibility for architecture', 'architecture_admission_eligibility'),
    ('how to apply for admission', 'cap_admission_process'),

    # Contact & Placements
    ('how to reach aiktc contact number', 'inst_contact'),
    ('placement packages and top recruiters', 'campus_placements'),

    # Academic Programs & Courses Offered
    ('what are available course', 'inst_programs_courses'),
    ('what course does aiktc offere', 'inst_programs_courses'),
    ('courses in engineering', 'engineering_programs_courses'),
    ('courses in pharmacy', 'pharmacy_programs_courses'),
    ('courses in architecture', 'architecture_programs_courses'),
]

print(f"Testing {len(test_queries)} queries for exact top-1 chunk match...")
failed = []
for q, expected in test_queries:
    intent = classify_intent(q)
    entities = extract_entities(q, [])
    results = vs.search(q, top_k=1, category=intent, entities=entities)
    top_chunk = results[0][0] if results else None
    top_id = top_chunk.chunk_id if top_chunk else 'NONE'
    matched = expected in top_id
    status = 'PASS' if matched else 'FAIL'
    if not matched:
        failed.append((q, expected, top_id))
    print(f"[{status}] Q: {q:<38} -> Got: {top_id:<32} (Expected: {expected})")

print("=" * 60)
print(f"Total: {len(test_queries)}, Passed: {len(test_queries) - len(failed)}, Failed: {len(failed)}")
if failed:
    print("Failed queries:")
    for q, exp, got in failed:
        print(f"  Query: {q} | Expected: {exp} | Got: {got}")
    sys.exit(1)
else:
    print("ALL 31 QUERY DISAMBIGUATION CHECKS PASSED!")
