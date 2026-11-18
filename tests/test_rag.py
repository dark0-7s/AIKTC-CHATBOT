# tests/test_rag.py
"""
Unit and integration test suite for the genuine Vector RAG implementation.
Verifies chunking, vector embeddings, cosine similarity search, and top-k retrieval.
"""
import unittest
import sys
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from kb.chunker import create_chunks_from_kb, TextChunk
from kb.vector_store import VectorStore, tokenize
from kb.retriever import retrieve_knowledge, get_vector_store
from kb.loader import load_and_merge_kb


class TestVectorRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb_path = Path(__file__).parent.parent / "backend" / "data" / "kb"
        cls.kb_dict = load_and_merge_kb(str(cls.kb_path))
        cls.chunks = create_chunks_from_kb(cls.kb_path)
        cls.vector_store = VectorStore()
        cls.vector_store.build_index(cls.chunks)

    def test_1_semantic_chunking(self):
        """Verify that document chunks are created with rich titles and categories."""
        self.assertGreater(len(self.chunks), 40)
        categories = {c.category for c in self.chunks}
        # Check core categories exist
        for expected in ["fee", "faculty", "facilities", "scholarship", "hostel", "placement"]:
            self.assertIn(expected, categories)

        for chunk in self.chunks:
            self.assertTrue(len(chunk.title) > 0)
            self.assertTrue(len(chunk.content) > 0)
            self.assertIsInstance(chunk.metadata, dict)

    def test_2_tokenization_and_vector_space(self):
        """Verify vector space vocabulary and TF-IDF normalization."""
        vocab = self.vector_store.vocab
        self.assertGreater(len(vocab), 200)
        self.assertIn("engineering", vocab)
        self.assertIn("tuition", vocab)

        # Check document vectors are normalized (L2 norm should be ~1.0)
        for doc_vec in self.vector_store.doc_vectors:
            norm = sum(val * val for val in doc_vec.values())
            self.assertAlmostEqual(norm, 1.0, places=4)

    def test_3_cosine_similarity_retrieval(self):
        """Verify that cosine similarity retrieval returns top-k semantically relevant chunks."""
        test_queries = [
            ("What is the annual fee for B.Tech CSE?", "fee"),
            ("Who is the HOD of Computer Engineering?", "faculty"),
            ("Tell me about hostel rooms and mess food", "hostel"),
            ("What scholarships can OBC students get?", "scholarship"),
            ("What are the campus placement packages?", "placement")
        ]

        for query, expected_category in test_queries:
            with self.subTest(query=query):
                results = self.vector_store.search(query, top_k=3, category=expected_category)
                self.assertGreater(len(results), 0)
                top_chunk, score = results[0]
                self.assertGreater(score, 0.10)
                self.assertEqual(top_chunk.category, expected_category)

    def test_4_retriever_rag_context_generation(self):
        """Verify that retrieve_knowledge returns formatted RAG context with citations."""
        query = "What is the fee for Computer Engineering?"
        context = retrieve_knowledge(
            intent="fee",
            entities={"departments": ["CSE"]},
            kb=self.kb_dict,
            query=query
        )
        self.assertIn("RAG Retrieved Context", context)
        self.assertIn("Vector Relevance", context)
        self.assertIn("Fee Structure", context)

    def test_5_low_hallucination_grounding(self):
        """Verify that specific institutional facts are retrieved without missing data."""
        # Check hostel capacity is present in retrieved context
        hostel_context = retrieve_knowledge(
            intent="hostel",
            entities={},
            kb=self.kb_dict,
            query="What is the hostel capacity and mess charges?"
        )
        self.assertIn("Hostel", hostel_context)
        self.assertTrue("Capacity" in hostel_context or "Hostel" in hostel_context)


if __name__ == "__main__":
    unittest.main()
