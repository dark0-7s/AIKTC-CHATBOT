# backend/engine/workflow.py
"""
AIKTC AI Chatbot — Algorithm 1 Implementation Workflow
======================================================
Executes Algorithm 1: Multilingual institutional query processing and response generation.

Procedure PROCESS_QUERY(Q, C):
  1. Language detection & preprocessing (DETECT_LANGUAGE, PREPROCESS)
  2. Intent classification & entity extraction (CLASSIFY_INTENT, EXTRACT_ENTITIES)
  3. Dynamic / time-sensitive check (IS_DYNAMIC, GET_OFFICIAL_SOURCE)
  4. Knowledge retrieval (RETRIEVE_KNOWLEDGE)
  5. Grounded prompt generation & LLM call (BUILD_PROMPT, CALL_LLM)
  6. Structured response formatting (DECIDE_RESPONSE_TYPE, FORMAT_RESPONSE)
  7. Logging and session management (LOG_QUERY)
"""

import json
import logging
from typing import Any, AsyncGenerator

from prompt.builder import detect_language, build_prompt
from engine.classifier import preprocess, classify_intent
from engine.extractor import extract_entities
from engine.dynamic_resolver import is_dynamic, get_official_source
from engine.context_builder import build_context_note
from kb.retriever import retrieve_knowledge

logger = logging.getLogger("aiktc.workflow")

def execute_algorithm_1(
    message: str,
    history: list[dict],
    kb_dict: dict,
    full_kb_markdown: str
) -> dict[str, Any]:
    """
    Executes the analytical and retrieval steps of Algorithm 1.
    
    Returns execution metadata and prepared context ready for LLM streaming.
    """
    # ── Step 1: Language detection and preprocessing ───────────────────────
    lang = detect_language(message)
    q_prep = preprocess(message)
    logger.info(f"[Step 1] Lang: {lang} | Preprocessed: '{q_prep}'")

    # ── Step 2: Intent classification and entity extraction ────────────────
    intent = classify_intent(q_prep, context=history)
    entities = extract_entities(q_prep, history)
    logger.info(f"[Step 2] Intent: {intent} | Entities: {entities}")

    # ── Step 3: Check for dynamic/time-sensitive information ───────────────
    is_dyn = is_dynamic(intent, entities, q_prep)
    official_source = None
    if is_dyn:
        official_source = get_official_source(intent, entities)
        logger.info(f"[Step 3] Dynamic query detected! Resolved official sources.")

    # ── Step 4: Retrieve relevant context from institutional knowledge base 
    # Uses genuine RAG vector retrieval if kb_dict is available, else full markdown
    if kb_dict:
        retrieved_context = retrieve_knowledge(intent, entities, kb_dict, query=q_prep)
    else:
        retrieved_context = full_kb_markdown
    logger.info(f"[Step 4] Retrieved context size: {len(retrieved_context)} characters")

    # ── Step 5: Deterministic context note & prompt construction ───────────
    context_note = build_context_note(q_prep, history)
    prompt = build_prompt(
        kb_markdown=retrieved_context,
        context_note=context_note,
        history=history,
        message=q_prep
    )

    return {
        "lang": lang,
        "q_prep": q_prep,
        "intent": intent,
        "entities": entities,
        "is_dynamic": is_dyn,
        "official_source": official_source,
        "retrieved_context": retrieved_context,
        "context_note": context_note,
        "prompt": prompt
    }
