# backend/kb/retriever.py
"""
AIKTC AI Chatbot — RAG (Retrieval-Augmented Generation) & Knowledge Base Retriever
==================================================================================
Implements Step 4 of Algorithm 1:
  - retrieve_knowledge(intent, entities, kb, query="")

Combines:
  1. Dense-Sparse Vector Similarity Search (Semantic RAG Retrieval via VectorStore)
  2. Structured Section-Level Fallback Filter
  3. Grounded Context Formatting with Source Attribution to minimize LLM hallucination.
"""

import logging
from pathlib import Path
from typing import Any

from kb.chunker import create_chunks_from_kb, TextChunk
from kb.vector_store import VectorStore
from kb.markdown import (
    kb_to_markdown,
    _render_engineering,
    _render_pharmacy,
    _render_architecture,
    _render_activities
)

logger = logging.getLogger("aiktc.kb.retriever")

ENGINEERING_DEPTS = {"CSE", "IT", "ECS", "MECH", "CIVIL", "CHEM"}
PHARMACY_DEPTS = {"BPHARM", "MPHARM"}
ARCHITECTURE_DEPTS = {"BARCH"}

_GLOBAL_VECTOR_STORE: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Singleton accessor for the in-memory RAG vector store."""
    global _GLOBAL_VECTOR_STORE
    if _GLOBAL_VECTOR_STORE is None:
        _GLOBAL_VECTOR_STORE = VectorStore()
        kb_path = Path(__file__).parent.parent / "data" / "kb"
        if kb_path.exists():
            chunks = create_chunks_from_kb(kb_path)
            _GLOBAL_VECTOR_STORE.build_index(chunks)
            logger.info(f"Initialized RAG Vector Store with {len(chunks)} semantic chunks.")
    return _GLOBAL_VECTOR_STORE


def _render_common_header(kb: dict) -> list[str]:
    """Render common college header information."""
    lines: list[str] = ["# AIKTC College Knowledge Base (Retrieved Context)\n"]
    common = kb.get("common", {})
    if not common:
        return lines

    lines.append("## College Overview")
    lines.append(f"- **Name:** {common.get('name', 'AIKTC')}")
    lines.append(f"- **Address:** {common.get('address', '')}")
    lines.append(f"- **Website:** {common.get('website', '')}")
    lines.append(f"- **Established:** {common.get('established', '')}")
    lines.append(f"- **Affiliated to:** {common.get('affiliated_to', '')}")

    director = common.get("director", {})
    if director:
        lines.append(f"- **Director:** {director.get('name', '')} ({director.get('qualification', '')})")

    principal = common.get("principal", {})
    if principal:
        lines.append(f"- **Principal:** {principal.get('name', '')} ({principal.get('qualification', '')})")

    contacts = common.get("contacts", {})
    if contacts:
        lines.append("\n### Contact Information")
        for k, v in contacts.items():
            lines.append(f"- **{k}:** {v}")

    return lines


def retrieve_knowledge(
    intent: str,
    entities: dict | None,
    kb: dict,
    query: str = ""
) -> str:
    """
    Algorithm 1, Step 4: Retrieve relevant context from institutional knowledge base.
    
    Uses genuine Vector RAG search when a user query is present, with
    grounded source citations to eliminate hallucination.
    Falls back gracefully to section-level JSON filtering if query is absent.
    """
    # ── Phase A: Vector RAG Semantic Retrieval ─────────────────────────────
    if query:
        vs = get_vector_store()
        target_depts = list(entities.get("departments", [])) if entities else []
        if len(target_depts) >= 2 or intent == "compare_departments":
            matches = []
            seen_chunk_ids = set()
            for d in target_depts[:2]:
                d_entities = dict(entities) if entities else {}
                d_entities["departments"] = [d]
                d_matches = vs.search(f"{d} department overview curriculum scope", top_k=2, category="department", entities=d_entities)
                for chunk, score in d_matches:
                    if chunk.chunk_id not in seen_chunk_ids:
                        seen_chunk_ids.add(chunk.chunk_id)
                        matches.append((chunk, score))
            # Supplement with general query matches
            gen_matches = vs.search(query, top_k=2, category=intent, entities=entities)
            for chunk, score in gen_matches:
                if chunk.chunk_id not in seen_chunk_ids and len(matches) < 4:
                    seen_chunk_ids.add(chunk.chunk_id)
                    matches.append((chunk, score))
        else:
            matches = vs.search(query, top_k=3, category=intent, entities=entities, min_score=0.03)

        if matches:
            logger.info(f"RAG Vector Search retrieved {len(matches)} relevant chunks for query: '{query}'")
            rag_lines = [
                "# AIKTC Grounded Knowledge Base (RAG Retrieved Context)",
                "The following passages were retrieved using semantic vector similarity against the verified college repository:\n"
            ]
            for i, (chunk, score) in enumerate(matches, 1):
                rag_lines.append(f"### [DOCUMENT {i}: {chunk.title}] (Vector Relevance: {score:.2f})")
                rag_lines.append(f"Domain: {chunk.category.upper()} | Metadata: {chunk.metadata}")
                rag_lines.append(chunk.content)
                rag_lines.append("\n" + "-" * 40 + "\n")
            return "\n".join(rag_lines)

    # ── Phase B: Deterministic Section Filtering (Fallback) ────────────────
    if not kb:
        return ""

    departments = set(entities.get("departments", [])) if entities else set()

    has_eng = bool(departments & ENGINEERING_DEPTS)
    has_pharm = bool(departments & PHARMACY_DEPTS)
    has_arch = bool(departments & ARCHITECTURE_DEPTS)

    # 1. School-specific queries
    if has_eng and not (has_pharm or has_arch):
        logger.info(f"Retrieving Engineering context for departments: {departments}")
        lines = _render_common_header(kb)
        if kb.get("engineering"):
            lines.extend(_render_engineering(kb["engineering"]))
        return "\n".join(lines)

    if has_pharm and not (has_eng or has_arch):
        logger.info(f"Retrieving Pharmacy context for departments: {departments}")
        lines = _render_common_header(kb)
        if kb.get("pharmacy"):
            lines.extend(_render_pharmacy(kb["pharmacy"]))
        return "\n".join(lines)

    if has_arch and not (has_eng or has_pharm):
        logger.info(f"Retrieving Architecture context for departments: {departments}")
        lines = _render_common_header(kb)
        if kb.get("architecture"):
            lines.extend(_render_architecture(kb["architecture"]))
        return "\n".join(lines)

    # 2. Topic-specific queries
    if intent == "cap" and kb.get("cap"):
        logger.info("Retrieving CAP round & CET Cell context")
        lines = _render_common_header(kb)
        cap = kb["cap"]
        lines.append("\n---\n## CAP (Centralised Admission Process) – Maharashtra State")
        lines.append(f"**{cap.get('meta', {}).get('notice_title', '')}**")
        lines.append(f"**⚠️ {cap.get('meta', {}).get('disclaimer', '')}**")
        schedule = cap.get("schedule", [])
        if schedule:
            lines.append("\n### Provisional Schedule")
            lines.append("| Activity | Start Date | End Date |")
            lines.append("|----------|------------|----------|")
            for s in schedule:
                lines.append(f"| {s.get('activity', '')} | {s.get('start', '')} | {s.get('end', '')} |")
        docs = cap.get("documents_required", [])
        if docs:
            lines.append("\n### Required Documents")
            for d in docs:
                lines.append(f"- **{d['name']}**")
        return "\n".join(lines)

    if intent == "hostel":
        logger.info("Retrieving Hostel context")
        lines = _render_common_header(kb)
        hostel = kb.get("common", {}).get("hostel", {})
        if hostel:
            lines.append("\n### Hostel Information")
            lines.append(f"- Boys capacity: {hostel.get('boys_capacity', '')} | Girls capacity: {hostel.get('girls_capacity', '')}")
            lines.append(f"- Fees per year: ₹{hostel.get('fees_per_year', 0):,} | Mess per month: ₹{hostel.get('mess_per_month', 0):,}")
            fac = hostel.get("facilities", [])
            if fac:
                lines.append(f"- Facilities: {', '.join(fac)}")
        return "\n".join(lines)

    if intent == "placement":
        logger.info("Retrieving Placements context")
        lines = _render_common_header(kb)
        for school in ("engineering", "pharmacy"):
            placements = kb.get(school, {}).get("placements", {})
            if placements:
                lines.append(f"\n### {school.title()} Placements")
                for k, v in placements.items():
                    if isinstance(v, list):
                        lines.append(f"- **{k.title()}:** {', '.join(str(x) for x in v[:10])}")
                    elif isinstance(v, str):
                        lines.append(f"- **{k.title()}:** {v}")
        return "\n".join(lines)

    if intent == "facilities" and kb.get("activities"):
        logger.info("Retrieving Campus Activities & Facilities context")
        lines = _render_common_header(kb)
        lines.extend(_render_activities(kb["activities"]))
        return "\n".join(lines)

    # 3. Graceful Fallback: For general or broad queries, return full KB markdown
    logger.info("Intent/department broad or unclassified — using full knowledge base")
    return kb_to_markdown(kb)
