# backend/kb/vector_store.py
"""
AIKTC In-Memory Vector Store & Semantic Retrieval Engine
========================================================
Implements genuine vector-space embedding, cosine similarity calculation,
and top-k nearest neighbor retrieval for RAG.
"""

import re
import math
import logging
from collections import Counter
from typing import Any
from .chunker import TextChunk

logger = logging.getLogger("aiktc.vector_store")

STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
    "by", "of", "is", "are", "was", "were", "be", "been", "have", "has",
    "had", "do", "does", "did", "can", "could", "will", "would", "shall",
    "should", "may", "might", "must", "it", "its", "that", "this", "these",
    "those", "what", "which", "who", "whom", "where", "when", "why", "how",
    "hai", "kya", "ka", "ki", "ke", "ko", "se", "mein", "pe", "karo", "karna",
    # Domain & conversational query filler words
    "aiktc", "college", "campus", "institute", "tell", "show", "give", "me",
    "please", "about", "detail", "details", "info", "information", "want", "know"
}


DEPT_CANONICAL_MAP = {
    "CSE": {"CSE", "COMP", "CO"},
    "COMP": {"CSE", "COMP", "CO"},
    "CO": {"CSE", "COMP", "CO"},
    "IT": {"IT", "INFT", "BSIT", "BSCIT"},
    "ECS": {"ECS", "EXTC", "ETRX"},
    "MECH": {"MECH"},
    "CIVIL": {"CIVIL"},
    "CHEM": {"CHEM"},
    "CSDS": {"CSDS", "DS", "DATA_SCIENCE"},
    "AIML": {"AIML", "CSAIML", "AI"},
    "BPHARM": {"BPHARM", "PHARMACY"},
    "MPHARM": {"MPHARM"},
    "BARCH": {"BARCH", "ARCHITECTURE"}
}

DEPT_SCHOOL_MAP = {
    "CSE": "engineering", "COMP": "engineering", "CO": "engineering",
    "IT": "engineering", "INFT": "engineering", "BSIT": "engineering", "BSCIT": "engineering",
    "ECS": "engineering", "EXTC": "engineering", "ETRX": "engineering",
    "MECH": "engineering", "CIVIL": "engineering", "CHEM": "engineering",
    "CSDS": "engineering", "DS": "engineering", "DATA_SCIENCE": "engineering",
    "AIML": "engineering", "CSAIML": "engineering", "AI": "engineering",
    "BPHARM": "pharmacy", "PHARMACY": "pharmacy",
    "MPHARM": "pharmacy",
    "BARCH": "architecture", "ARCHITECTURE": "architecture"
}

def tokenize(text: str) -> list[str]:
    """Tokenize, stem common inflections, and filter stopwords for vector generation."""
    t_clean = text.lower()
    # Normalize common department aliases for consistent lexical matching
    if "computer science" in t_clean or "computer engg" in t_clean or "computer engineering" in t_clean:
        t_clean += " cse comp co"
    if "data science" in t_clean:
        t_clean += " csds ds"
    if "artificial intelligence" in t_clean or "machine learning" in t_clean:
        t_clean += " aiml ai"
    if "extc" in t_clean or "telecom" in t_clean or "electronics" in t_clean:
        t_clean += " ecs"

    tokens = re.findall(r'[a-zA-Z0-9_\u0900-\u097f]+', t_clean)
    normalized: list[str] = []
    for t in tokens:
        if t in STOPWORDS or len(t) <= 1:
            continue
        # Stem common plural / inflected forms
        if t in ("fees", "feez"):
            normalized.append("fee")
        elif t in ("labs", "laboratories"):
            normalized.append("lab")
        elif t in ("courses", "cours"):
            normalized.append("course")
        elif t in ("departments", "depts"):
            normalized.append("department")
        elif t in ("faculties", "professors", "teachers"):
            normalized.append("faculty")
        elif t in ("hostels",):
            normalized.append("hostel")
        elif t in ("placements", "packages"):
            normalized.append("placement")
        elif t in ("scholarships",):
            normalized.append("scholarship")
        elif t in ("cutoffs",):
            normalized.append("cutoff")
        elif t in ("admissions",):
            normalized.append("admission")
        elif t.endswith("s") and len(t) > 4 and not t.endswith(("ss", "us", "is")):
            normalized.append(t[:-1])
        else:
            normalized.append(t)
    return normalized


class VectorStore:
    """
    In-memory vector store implementing cosine similarity retrieval.
    """

    def __init__(self):
        self.chunks: list[TextChunk] = []
        self.doc_vectors: list[dict[str, float]] = []
        self.idf: dict[str, float] = {}
        self.vocab: set[str] = set()

    def build_index(self, chunks: list[TextChunk]) -> None:
        """
        Builds the vector space index from a list of document chunks.
        Computes IDF and normalized TF-IDF document vectors.
        """
        self.chunks = chunks
        num_docs = len(chunks)
        if num_docs == 0:
            return

        # 1. Document frequency
        df: Counter[str] = Counter()
        tokenized_docs: list[list[str]] = []

        for chunk in chunks:
            # Index both title and content (giving title 2x weight)
            full_text = f"{chunk.title} {chunk.title} {chunk.content}"
            tokens = tokenize(full_text)
            tokenized_docs.append(tokens)
            unique_terms = set(tokens)
            df.update(unique_terms)

        # 2. Compute IDF with smoothing
        self.idf = {
            term: math.log(1.0 + (num_docs / (count + 1.0))) + 1.0
            for term, count in df.items()
        }
        self.vocab = set(self.idf.keys())

        # 3. Compute normalized TF-IDF vector for each document
        self.doc_vectors = []
        for tokens in tokenized_docs:
            vec = self._compute_normalized_vector(tokens)
            self.doc_vectors.append(vec)

        logger.info(f"Vector store indexed {num_docs} chunks. Vocabulary size: {len(self.vocab)} terms.")

    def _compute_normalized_vector(self, tokens: list[str]) -> dict[str, float]:
        """Compute L2-normalized sublinear TF-IDF vector."""
        if not tokens:
            return {}
        tf = Counter(tokens)
        vec: dict[str, float] = {}
        sq_sum = 0.0

        for term, count in tf.items():
            if term in self.idf:
                # Sublinear term frequency scaling: 1 + ln(tf)
                weight = (1.0 + math.log(count)) * self.idf[term]
                vec[term] = weight
                sq_sum += weight * weight

        # L2-normalization for cosine distance
        norm = math.sqrt(sq_sum)
        if norm > 0.0:
            return {term: val / norm for term, val in vec.items()}
        return {}

    def _cosine_similarity(self, q_vec: dict[str, float], doc_vec: dict[str, float]) -> float:
        """Dot product of two L2-normalized vectors equals cosine similarity."""
        if not q_vec or not doc_vec:
            return 0.0
        # Dot product on intersecting keys
        if len(q_vec) < len(doc_vec):
            return sum(val * doc_vec.get(term, 0.0) for term, val in q_vec.items())
        else:
            return sum(val * q_vec.get(term, 0.0) for term, val in doc_vec.items())

    def search(
        self,
        query: str,
        top_k: int = 3,
        category: str | None = None,
        entities: dict[str, Any] | None = None,
        min_score: float = 0.02
    ) -> list[tuple[TextChunk, float]]:
        """
        Retrieves the top-k most semantically relevant chunks for a query.
        
        Args:
            query: User's raw or preprocessed question.
            top_k: Number of chunks to retrieve.
            category: Optional intent/category to provide a relevance boost.
            entities: Optional extracted entities (departments, person_intent) for precision boosting.
            min_score: Minimum cosine similarity threshold.
            
        Returns:
            List of (TextChunk, similarity_score) sorted descending.
        """
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        # Prepare entity target departments, target schools, and person intent
        target_depts: set[str] = set()
        target_schools: set[str] = set()
        person_intent: str | None = None

        q_lower = query.lower()
        if "engineering" in q_lower or "engg" in q_lower or "btech" in q_lower or "b.tech" in q_lower:
            target_schools.add("engineering")
        if "pharmacy" in q_lower or "pharm" in q_lower or "bpharm" in q_lower or "b.pharm" in q_lower or "mpharm" in q_lower:
            target_schools.add("pharmacy")
        if "architecture" in q_lower or "arch" in q_lower or "barch" in q_lower or "b.arch" in q_lower:
            target_schools.add("architecture")

        if entities:
            raw_depts = entities.get("departments", [])
            for d in raw_depts:
                d_str = str(d).upper()
                target_depts.update(DEPT_CANONICAL_MAP.get(d_str, {d_str}))
                if d_str in DEPT_SCHOOL_MAP:
                    target_schools.add(DEPT_SCHOOL_MAP[d_str])
            person_intent = entities.get("person_intent")

        q_vec = self._compute_normalized_vector(q_tokens)
        results: list[tuple[TextChunk, float]] = []

        for i, doc_vec in enumerate(self.doc_vectors):
            base_score = self._cosine_similarity(q_vec, doc_vec)
            chunk = self.chunks[i]

            # 1. Category boost: if intent matches chunk category, boost score by 80%
            score = base_score
            category_matched = False
            if category:
                if chunk.category == category:
                    score *= 1.8
                    category_matched = True
                elif category == "admission_process" and chunk.category in ("admission_process", "cap"):
                    score *= 1.8
                    category_matched = True
                elif category in ("facilities", "labs") and chunk.category == "facilities":
                    score *= 1.8
                    category_matched = True

            # 2. Entity / Department & School metadata boost
            chunk_dept = str(chunk.metadata.get("dept", "")).upper()
            chunk_school = str(chunk.metadata.get("school", "")).lower()

            if target_depts and chunk_dept and chunk_dept in target_depts:
                score *= 2.5
            elif target_schools and chunk_school and chunk_school in target_schools:
                score *= 2.0

            # 3. Person Intent boost: 2.5x boost for leadership queries
            if person_intent:
                if person_intent in ("director", "principal") and chunk.chunk_id == "inst_leadership":
                    score *= 2.5
                elif person_intent == "dean" and "dean" in chunk.chunk_id:
                    score *= 2.5

            # 4. Fee Structure vs Refund Policy Disambiguation
            is_refund_query = bool(re.search(r'\b(?:refund|cancellation|canceling|cancel|deduct|deduction)\b', query.lower()))
            if is_refund_query:
                if "refund" in chunk.chunk_id:
                    score *= 3.0
            else:
                if "refund" in chunk.chunk_id:
                    score *= 0.2
                elif "_fees" in chunk.chunk_id:
                    score *= 2.0

            if score >= min_score:
                results.append((chunk, score))

        # Sort descending by similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
