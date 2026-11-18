# tests/master_test_runner.py
"""
AIKTC CHATBOT — MASTER COMPREHENSIVE TEST SUITE ORCHESTRATOR
=============================================================
Executes all 6 testing batteries across the entire architecture:
  Suite 1: Vector RAG Unit Tests (test_rag.py)
  Suite 2: Web Navigation & Official Link Accuracy (test_web_navigation.py)
  Suite 3: Algorithm 1 Pipeline Verification (test_algorithm_1.py)
  Suite 4: Real-World Student Scenario Tests (test_e2e_rag_queries.py)
  Suite 5: Microscopic 5-Stage RAG Pipeline Audit (inspect_full_rag.py)
  Suite 6: 200-Query Empirical Benchmark (run_evaluation.py)
"""

import sys
import time
import subprocess
from pathlib import Path

def run_master_tests():
    print("=" * 80)
    print("      AIKTC CHATBOT — MASTER COMPREHENSIVE VERIFICATION & TEST RUNNER")
    print("=" * 80)

    test_dir = Path(__file__).parent
    py_exe = r"C:\Users\Kazi\Documents\AIKTC CHATBOT\python-embed\python.exe"

    test_suites = [
        {
            "name": "Vector RAG Unit Suite",
            "file": test_dir / "test_rag.py",
            "desc": "Chunking, vector embeddings, L2 normalization, cosine similarity"
        },
        {
            "name": "Web Navigation & Official Links",
            "file": test_dir / "test_web_navigation.py",
            "desc": "26 live AIKTC portals, schema, routing accuracy, LinkCard compatibility"
        },
        {
            "name": "Algorithm 1 Pipeline Suite",
            "file": test_dir / "test_algorithm_1.py",
            "desc": "Steps 1–5 (Devanagari, intent classification, dynamic link routing, KB)"
        },
        {
            "name": "Real Student E2E Scenarios",
            "file": test_dir / "test_e2e_rag_queries.py",
            "desc": "10 real-world departmental queries with RAG context grounding"
        },
        {
            "name": "RAG 5-Stage Deep Audit",
            "file": test_dir / "inspect_full_rag.py",
            "desc": "Microscopic audit of ingestion, vocab, L2 norm, ranking, prompt assembly"
        },
        {
            "name": "200-Query Empirical Benchmark",
            "file": test_dir / "run_evaluation.py",
            "desc": "Reproduction of Paper Table 1 & Table 2 metrics across 10 domains"
        }
    ]

    results = []
    overall_start = time.time()

    for idx, suite in enumerate(test_suites, 1):
        s_name = suite["name"]
        s_file = suite["file"]
        s_desc = suite["desc"]

        print(f"\n[{idx}/6] Executing: {s_name} ({s_file.name})")
        print(f"      Scope: {s_desc}")
        print("-" * 80)

        t0 = time.time()
        # For test_web_navigation, we can run it safely with standard execution
        res = subprocess.run([py_exe, str(s_file)], capture_output=True, text=True)
        elapsed = time.time() - t0

        passed = (res.returncode == 0)
        status = "PASSED" if passed else "FAILED"

        # Capture key output lines
        output_lines = [l for l in (res.stdout + res.stderr).splitlines() if l.strip()]
        summary_line = output_lines[-1] if output_lines else "No output"
        if "OK" in summary_line:
            summary_line = "All unit assertions passed (OK)"

        print(f"      Result  : {status} in {elapsed:.2f}s")
        print(f"      Summary : {summary_line}")

        results.append({
            "id": idx,
            "name": s_name,
            "file": s_file.name,
            "status": status,
            "time": elapsed,
            "summary": summary_line
        })

    total_time = time.time() - overall_start

    print("\n" + "=" * 80)
    print("                  MASTER TEST EXECUTION SUMMARY REPORT")
    print("=" * 80)
    print(f"{'#':<3} | {'Test Suite Name':<30} | {'Status':<10} | {'Time':<8} | {'Details'}")
    print("-" * 80)
    for r in results:
        print(f"{r['id']:<3} | {r['name']:<30} | {r['status']:<10} | {r['time']:>5.2f}s  | {r['summary'][:25]}")
    print("=" * 80)

    total_passed = sum(1 for r in results if r["status"] == "PASSED")
    print(f"Overall Results: {total_passed}/{len(results)} Test Batteries Passed ({total_passed/len(results)*100:.1f}%)")
    print(f"Total Execution Time: {total_time:.2f} seconds\n")

if __name__ == "__main__":
    run_master_tests()
