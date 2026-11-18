# tests/test_algorithm_1.py
"""Unit and integration test suite for Algorithm 1 and paper alignment modules."""
import unittest
import sys
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from engine.classifier import preprocess, classify_intent
from engine.dynamic_resolver import is_dynamic, get_official_source
from kb.retriever import retrieve_knowledge
from engine.workflow import execute_algorithm_1
from kb.loader import load_and_merge_kb
from kb.markdown import kb_to_markdown


class TestAlgorithm1Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        kb_path = Path(__file__).parent.parent / "backend" / "data" / "kb"
        cls.kb = load_and_merge_kb(str(kb_path))
        cls.kb_markdown = kb_to_markdown(cls.kb)

    def test_step1_preprocessing(self):
        """Test whitespace normalization and Devanagari numeral transliteration."""
        raw = "  फीस   कितनी   है   १२३४५  "
        processed = preprocess(raw)
        self.assertEqual(processed, "फीस कितनी है 12345")

        devanagari_all = "०१२३४५६७८९"
        self.assertEqual(preprocess(devanagari_all), "0123456789")

    def test_step2_intent_classification(self):
        """Test classification across core institutional domains."""
        cases = [
            ("What is the fee for Computer Engineering?", "fee"),
            ("What was the cutoff for CSE last year?", "admission_cutoff"),
            ("How do I register for CAP round?", "cap"),
            ("Tell me about scholarships for minority students", "scholarship"),
            ("Who is the HOD of Electrical Engineering?", "faculty"),
            ("What are the hostel rules and facilities?", "hostel"),
            ("Show me placement records for 2024", "placement"),
            ("How to apply for admission in B.Tech?", "admission_process"),
            ("What facilities are available on campus?", "facilities"),
            ("What is the college address and contact number?", "contact"),
            ("What is the weather in Mumbai today?", "out_of_scope"),
        ]
        for query, expected_intent in cases:
            with self.subTest(query=query):
                self.assertEqual(classify_intent(query), expected_intent)

    def test_step3_dynamic_resolution(self):
        """Test dynamic query detection and official source resolution."""
        dynamic_queries = [
            ("admission_cutoff", "What is the cut off for CSE?"),
            ("admission_cutoff", "What is the CET cutoff?"),
            ("cap", "Where do I register for CAP round 1?"),
            ("cap", "Show me the seat matrix for cap rounds"),
        ]
        for intent, query in dynamic_queries:
            with self.subTest(query=query):
                self.assertTrue(is_dynamic(intent, {}, query))
                source = get_official_source(intent, {})
                self.assertIsNotNone(source)
                self.assertIn("links", source)
                self.assertTrue(len(source["links"]) > 0)
                self.assertTrue(source["links"][0]["url"].startswith("http"))

        static_query = "What is the history of AIKTC?"
        self.assertFalse(is_dynamic("general", {}, static_query))

    def test_step4_kb_retrieval(self):
        """Test section-level KB retrieval."""
        result = retrieve_knowledge("fee", {"departments": ["CSE"]}, self.kb)
        self.assertIn("Fee", result)
        self.assertLess(len(result), len(self.kb_markdown))

        # Fallback for out of scope or empty
        oos_result = retrieve_knowledge("out_of_scope", {}, self.kb)
        self.assertTrue(len(oos_result) > 0)

    def test_step5_workflow_execution(self):
        """Test full Algorithm 1 execution."""
        # Dynamic query
        dyn_res = execute_algorithm_1(
            "What is the MHT CET cutoff for CSE?",
            [],
            self.kb,
            self.kb_markdown
        )
        self.assertEqual(dyn_res["intent"], "admission_cutoff")
        self.assertTrue(dyn_res["is_dynamic"])
        self.assertIsNotNone(dyn_res["official_source"])

        # Static query
        stat_res = execute_algorithm_1(
            "What scholarships are available?",
            [],
            self.kb,
            self.kb_markdown
        )
        self.assertEqual(stat_res["intent"], "scholarship")
        self.assertFalse(stat_res["is_dynamic"])
        self.assertIsNone(stat_res["official_source"])
        self.assertIn("scholarship", stat_res["retrieved_context"].lower())


if __name__ == "__main__":
    unittest.main()
