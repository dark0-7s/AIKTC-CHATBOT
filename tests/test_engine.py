# backend/tests/test_engine.py
import sys
from pathlib import Path

# Add backend to python path
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from engine.context_builder import build_context_note

TEST_CASES = [
    # ── TYPE A: Clear number + department + category (Confidence: HIGH) ──
    # 1. "Can I get CSE with 92 percentile Open category?"
    {
        "id": 1,
        "query": "Can I get CSE with 92 percentile Open category?",
        "history": [],
        "assert": lambda res: "Confidence: HIGH" in res and "CSE [MEDIUM" in res and "IT [HIGH" in res
    },
    # 2. "CSE milega 92 percentile pe? Open hoon."
    {
        "id": 2,
        "query": "CSE milega 92 percentile pe? Open hoon.",
        "history": [],
        "assert": lambda res: "Confidence: HIGH" in res and "CSE [MEDIUM" in res
    },
    # 3. "CSE, IT, ECS ke chances 88 percentile Open?"
    {
        "id": 3,
        "query": "CSE, IT, ECS ke chances 88 percentile Open?",
        "history": [],
        "assert": lambda res: "Confidence: HIGH" in res and "CSE [LOW" in res and "IT [MEDIUM" in res and "ECS [MEDIUM" in res
    },
    # 5. "Mera NATA score 145 hai, B.Arch milega? OBC."
    {
        "id": 5,
        "query": "Mera NATA score 145 hai, B.Arch milega? OBC.",
        "history": [],
        "assert": lambda res: "Confidence: HIGH" in res and "BARCH [HIGH" in res and "marks" in res
    },
    # 9. "Open" (after Turn 7 and 8)
    {
        "id": 9,
        "query": "Open",
        "history": [
            {"role": "user", "content": "92 percentile hai mera"},
            {"role": "user", "content": "CSE"}
        ],
        "assert": lambda res: "Category not found" not in res  # Category Open is now found
    },
    # 26. "OBC-NCL hoon, ECS milega? Mera percentile 83 hai."
    {
        "id": 26,
        "query": "OBC-NCL hoon, ECS milega? Mera percentile 83 hai.",
        "history": [],
        "assert": lambda res: "Confidence: HIGH" in res and "ECS [HIGH" in res
    },
    # 34. After multi_pred, follow-up: What about MECH?
    {
        "id": 34,
        "query": "What about MECH?",
        "history": [
            {"role": "user", "content": "92 percentile, CSE, IT chances?"},
            {"role": "user", "content": "Open"}
        ],
        "assert": lambda res: "Confidence: HIGH" in res and "MECH [HIGH" in res
    },
    # 38. "My percentile is 78.54345, can I get IT Open?"
    {
        "id": 38,
        "query": "My percentile is 78.54345, can I get IT Open?",
        "history": [],
        "assert": lambda res: "Confidence: HIGH" in res and "IT [LOW" in res
    },
    # 39. "सामान्य वर्ग में 92 percentile, CSE के लिए?"
    {
        "id": 39,
        "query": "सामान्य वर्ग में 92 percentile, CSE के लिए?",
        "history": [],
        "assert": lambda res: "Confidence: HIGH" in res and "CSE [MEDIUM" in res
    },
    # 40. "ओबीसी में 75 percentile, pharmacy milegi?"
    {
        "id": 40,
        "query": "ओबीसी में 75 percentile, pharmacy milegi?",
        "history": [],
        "assert": lambda res: "Confidence: HIGH" in res and "BPHARM [MEDIUM" in res
    },

    # ── TYPE B: Rank/score without dept, or ambiguous number (Confidence: LOW) ──
    # 6. "My JEE rank is 25000, can I get CSE?"
    {
        "id": 6,
        "query": "My JEE rank is 25000, can I get CSE?",
        "history": [],
        "assert": lambda res: "Confidence: LOW" in res and ("JEE" in res or "rank" in res)
    },
    # 27. "50 ke saath CSE mil sakta hai?"
    {
        "id": 27,
        "query": "50 ke saath CSE mil sakta hai?",
        "history": [],
        "assert": lambda res: "Confidence: LOW" in res and "ambiguous" in res and "CSE" in res
    },

    # ── TYPE C: Missing department or missing category (Confidence: LOW) ──
    # 4. "78 percentile hai, CSE IT ECS ke chances?" (Missing category → Type C)
    {
        "id": 4,
        "query": "78 percentile hai, CSE IT ECS ke chances?",
        "history": [],
        "assert": lambda res: "Confidence: LOW" in res and "Category not found" in res
    },
    # 7. "92 percentile hai mera" (Missing department → Type C)
    {
        "id": 7,
        "query": "92 percentile hai mera",
        "history": [],
        "assert": lambda res: "Confidence: LOW" in res and "department=none" in res
    },
    # 8. "CSE" (after Turn 7: 92 percentile, missing category → Type C)
    {
        "id": 8,
        "query": "CSE",
        "history": [{"role": "user", "content": "92 percentile hai mera"}],
        "assert": lambda res: "Confidence: LOW" in res and "Category not found" in res
    },
    # 24. "कंप्यूटर इंजीनियरिंग में मिलेगा? 85 percentile है।" (Missing category → Type C)
    {
        "id": 24,
        "query": "कंप्यूटर इंजीनियरिंग में मिलेगा? 85 percentile है।",
        "history": [],
        "assert": lambda res: "Category not found" in res and "CSE" in res
    },
    # 33. "92 percentile, CSE, IT chances?" (Missing category → Type C)
    {
        "id": 33,
        "query": "92 percentile, CSE, IT chances?",
        "history": [],
        "assert": lambda res: "Category not found" in res and "CSE, IT" in res
    },

    # ── TYPE D: General queries, lookup queries, out of scope (Empty context "") ──
    # 10. "ECS cutoff last 4 years"
    {
        "id": 10,
        "query": "ECS cutoff last 4 years",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 11. "ECS ka cutoff kya hai?"
    {
        "id": 11,
        "query": "ECS ka cutoff kya hai?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 12. "Who is the director?"
    {
        "id": 12,
        "query": "Who is the director?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 13. "Director kaun hain?"
    {
        "id": 13,
        "query": "Director kaun hain?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 14. "Faculty of CSE department"
    {
        "id": 14,
        "query": "Faculty of CSE department",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 15. "CSE ke faculty dikhao"
    {
        "id": 15,
        "query": "CSE ke faculty dikhao",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 16. "Show me the labs in ECS"
    {
        "id": 16,
        "query": "Show me the labs in ECS",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 17. "What is the annual fee for engineering?"
    {
        "id": 17,
        "query": "What is the annual fee for engineering?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 18. "Fees kya hai CSE ke liye?"
    {
        "id": 18,
        "query": "Fees kya hai CSE ke liye?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 19. "Fee comparison — CSE vs MECH vs CIVIL"
    {
        "id": 19,
        "query": "Fee comparison — CSE vs MECH vs CIVIL",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 20. "How do I apply for admission?"
    {
        "id": 20,
        "query": "How do I apply for admission?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 21. "Admission process kya hai?"
    {
        "id": 21,
        "query": "Admission process kya hai?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 22. "I want to speak to someone from admissions"
    {
        "id": 22,
        "query": "I want to speak to someone from admissions",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 23. "Hostel rules kya hain?"
    {
        "id": 23,
        "query": "Hostel rules kya hain?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 25. "यांत्रिक का cutoff बताओ"
    {
        "id": 25,
        "query": "यांत्रिक का cutoff बताओ",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 28. "EWS certificate kaise milta hai?"
    {
        "id": 28,
        "query": "EWS certificate kaise milta hai?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 29. "I got 85 in 12th. Then later: What are the labs?"
    {
        "id": 29,
        "query": "What are the labs?",
        "history": [{"role": "user", "content": "I got 85 in 12th."}],
        "assert": lambda res: res == ""
    },
    # 30. "What's the weather today?"
    {
        "id": 30,
        "query": "What's the weather today?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 31. "Placements 2024 ka data dikhao"
    {
        "id": 31,
        "query": "Placements 2024 ka data dikhao",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 32. "SC category mein CIVIL ka cutoff?"
    {
        "id": 32,
        "query": "SC category mein CIVIL ka cutoff?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 35. "BPharm mein OBC cutoff kya hai?"
    {
        "id": 35,
        "query": "BPharm mein OBC cutoff kya hai?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 36. "Who is the HOD of ECS?"
    {
        "id": 36,
        "query": "Who is the HOD of ECS?",
        "history": [],
        "assert": lambda res: res == ""
    },
    # 37. "Admission deadline kab hai?"
    {
        "id": 37,
        "query": "Admission deadline kab hai?",
        "history": [],
        "assert": lambda res: res == ""
    }
]

def run_tests():
    passed = 0
    failed = 0
    print("=" * 60)
    print("  AIKTC DETERMINISTIC ENGINE TEST SUITE (40 Cases)")
    print("=" * 60)
    
    for case in TEST_CASES:
        query = case["query"]
        history = case["history"]
        case_id = case["id"]
        
        try:
            res = build_context_note(query, history)
            # Run assertion function
            if case["assert"](res):
                print(f"Test {case_id:02}: PASSED | Query: {query}")
                passed += 1
            else:
                print(f"Test {case_id:02}: FAILED | Query: {query}")
                print(f"          Got Context: {res!r}")
                failed += 1
        except Exception as e:
            print(f"Test {case_id:02}: ERROR  | Query: {query} | {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_tests()