# tests/test_bizarre_and_multilingual.py
"""
AIKTC CHATBOT — Unique, Bizarre, Multilingual & Out-of-Scope Stress Test Suite
=============================================================================
Audits non-standard student interactions across 7 challenging dimensions:
  1. Out-of-Scope General (Cooking, Sports trivia, Code generation, Crypto)
  2. Out-of-Scope Other Colleges (VJTI, COEP, SPIT, IIT Bombay, BITS, ICT)
  3. Food, Canteen, Cafeteria & Hostel Mess
  4. Specific Faculty by Name (Tabrez Khan, Ramzan Khatik, Bandanawaz, etc.)
  5. Bizarre / Extreme Placement Inquiries (50 LPA, FAANG, Core recruiters)
  6. Specific Events, Clubs & Hackathons (Bonhomie, Algorithm, Nexathon, e-Yantra)
  7. Multilingual Queries (Devanagari Hindi, Marathi, Hinglish, Roman Urdu)
"""

import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import kb.retriever
kb.retriever._GLOBAL_VECTOR_STORE = None
vs = kb.retriever.get_vector_store()

from engine.classifier import classify_intent
from engine.extractor import extract_entities
from engine.rag_synthesizer import synthesize_grounded_answer

TEST_CASES = [
    # ── 1. Out-of-Scope General ──────────────────────────────────────────────
    ("how to cook chicken biryani at home", "out_of_scope", None),
    ("recipe for delicious butter chicken", "out_of_scope", None),
    ("who won the 2023 ICC cricket world cup", "out_of_scope", None),
    ("write a python script to reverse a linked list", "out_of_scope", None),
    ("what is the current price of bitcoin in dollars", "out_of_scope", None),
    ("solve math equation 2x + 10 = 50", "out_of_scope", None),
    ("who is the president of the united states", "out_of_scope", None),
    ("write me an essay on global climate change", "out_of_scope", None),

    # ── 2. Out-of-Scope Other Colleges ───────────────────────────────────────
    ("tell me about VJTI cutoff for computer engineering", "out_of_scope", None),
    ("is COEP better than AIKTC for mechanical", "out_of_scope", None),
    ("how to apply for admission in IIT Bombay", "out_of_scope", None),
    ("what is the fee structure of SPIT college", "out_of_scope", None),
    ("BITS Pilani direct admission process and fees", "out_of_scope", None),
    ("ICT Mumbai bachelor of pharmacy fees", "out_of_scope", None),
    ("MIT Pune average placement package for btech", "out_of_scope", None),

    # ── 3. Food, Canteen, Cafeteria & Hostel Mess ─────────────────────────────
    ("is there a canteen available on campus", "facilities", "inst_canteen"),
    ("what food is served in the hostel mess", "hostel", "inst_hostel"),
    ("canteen facilities and food quality in aiktc", "facilities", "inst_canteen"),
    ("hostel mess fees per month", "hostel", "inst_hostel"),
    ("is halal food available in college cafeteria", "facilities", "inst_canteen"),
    ("canteen breakfast and evening snacks timings", "facilities", "inst_canteen"),
    ("canteen tea coffee and lunch thali facilities", "facilities", "inst_canteen"),

    # ── 4. Specific Faculty by Name ──────────────────────────────────────────
    ("who is Prof Tabrez Khan", "faculty", "engineering_computer_faculty"),
    ("tell me about Dr Ramzan Khatik", "faculty", "inst_leadership"),
    ("experience of Prof Bandanawaz Kotiyal", "faculty", "engineering_electronics_computer_faculty"),
    ("who is Dr Shariq Syed", "faculty", "pharmacy_dean"),
    ("profile of Prof Raj Mhatre", "faculty", "architecture_dean"),
    ("who is Prof Zakir Ansari", "faculty", "engineering_mechanical_faculty"),
    ("Prof Fauwaz Parkar civil department", "faculty", "engineering_civil_faculty"),
    ("Prof Salim Shaikh AIML department head", "faculty", "engineering_cs_aiml_faculty"),

    # ── 5. Bizarre / Extreme Placement Inquiries ──────────────────────────────
    ("did anyone get 50 lakh package in aiktc", "placement", "campus_placements"),
    ("does Google or Microsoft visit AIKTC for campus placement", "placement", "campus_placements"),
    ("which core companies recruit for mechanical engineering", "placement", "campus_placements"),
    ("what are the placement opportunities for B.Pharm students", "placement", "campus_placements"),
    ("highest package kya hai college ka", "placement", "campus_placements"),
    ("average package kitna milta hai", "placement", "campus_placements"),
    ("internship opportunities with corporate companies", "placement", "campus_placements"),
    ("placement cell training and aptitude workshops", "placement", "campus_placements"),

    # ── 6. Specific Events, Clubs & Competitions ──────────────────────────────
    ("what is Algorithm Hackathon organized by Programmers Club", "facilities", "campus_activities"),
    ("tell me about e-Yantra Robotics Club at AIKTC", "facilities", "campus_activities"),
    ("details about TechnoScope and TechSprint competitions", "facilities", "campus_activities"),
    ("SAEINDIA Collegiate Club activities and formula kart", "facilities", "campus_activities"),
    ("Bonhomie Fuerza annual cricket tournament", "facilities", "campus_activities"),
    ("Film Club and Art Club activities at AIKTC", "facilities", "campus_activities"),
    ("DataNexus Club events for data science students", "facilities", "campus_activities"),
    ("ACM Student Chapter NeurOnyx Club", "facilities", "campus_activities"),

    # ── 7. Multilingual (Hinglish, Marathi, Devanagari, Roman Urdu) ───────────
    ("fees kitni hai computer engineering ki", "fee", "engineering_fees"),
    ("कम्प्यूटर इंजीनियरिंग की फीस कितनी है", "fee", "engineering_fees"),
    ("engineering chi fee kiti ahe", "fee", "engineering_fees"),
    ("admission sathi konti documents lagtat", "admission_process", "cap_admission_process"),
    ("hostel me khana kaisa milta hai aur mess charges kitne hai", "hostel", "inst_hostel"),
    ("pharmacy me admission lene ke liye mht cet lagta hai kya", "admission_process", "pharmacy_admission_eligibility"),
    ("college kahan pe hai aur panvel station se kaise pahunche", "contact", "inst_contact"),
    ("bhai mechanical me admission lena hai eligibility criteria kya hai", "admission_process", "engineering_admission_eligibility"),
    ("वास्तुशास्त्र (architecture) प्रवेशासाठी NATA आवश्यक आहे का", "admission_process", "architecture_admission_eligibility"),
    ("कॉलेजमधील कॅन्टीन आणि जेवणाची सोय कशी आहे", "facilities", "inst_canteen"),
]

def run_suite():
    print("=" * 80)
    print(f"RUNNING BIZARRE, OUT-OF-SCOPE & MULTILINGUAL STRESS TEST SUITE ({len(TEST_CASES)} QUERIES)")
    print("=" * 80)
    
    start_time = time.time()
    passed = 0
    failed = []

    for idx, (query, expected_intent, expected_chunk) in enumerate(TEST_CASES, 1):
        ent = extract_entities(query, [])
        intent = classify_intent(query, ent)
        res = vs.search(query, top_k=2, category=intent, entities=ent)
        top_c = res[0][0] if res else None
        top_id = top_c.chunk_id if top_c else "NONE"
        
        t_title = top_c.title if top_c else ""
        t_content = top_c.content if top_c else ""
        ctx = f"### [DOCUMENT 1: {t_title}]\n{t_content}"
        algo = {"intent": intent, "entities": ent, "lang": "en", "q_prep": query, "retrieved_context": ctx}
        answer = synthesize_grounded_answer(query, algo)
        
        # Validation checks
        if expected_intent == "out_of_scope":
            is_valid = intent == "out_of_scope" and "AIKTC Institutional AI Assistant" in answer
        else:
            intent_ok = (intent == expected_intent) or (expected_intent == "facilities" and intent in ("facilities", "general"))
            chunk_ok = expected_chunk in top_id if expected_chunk else True
            no_hallucination = "Department Overview: Bachelor of Architecture" not in answer or expected_chunk == "architecture_barch_overview"
            is_valid = intent_ok and chunk_ok and no_hallucination

        if is_valid:
            passed += 1
            print(f"  [PASS] #{idx:02d} Q: '{query}' -> Intent: {intent} | Chunk: {top_id}")
        else:
            failed.append((idx, query, expected_intent, intent, expected_chunk, top_id))
            print(f"  [FAIL] #{idx:02d} Q: '{query}' -> Exp Intent: {expected_intent}, Got: {intent} | Exp Chunk: {expected_chunk}, Got: {top_id}")

    elapsed = time.time() - start_time
    print("=" * 80)
    print(f"TEST COMPLETED IN {elapsed:.2f}s")
    print(f"Results: {passed} / {len(TEST_CASES)} PASSED ({passed/len(TEST_CASES)*100:.1f}%)")
    print("=" * 80)

    if failed:
        sys.exit(1)
    else:
        print("ALL BIZARRE, MULTILINGUAL & OUT-OF-SCOPE TESTS PASSED WITH 100% SUCCESS!")
        sys.exit(0)

if __name__ == "__main__":
    run_suite()
