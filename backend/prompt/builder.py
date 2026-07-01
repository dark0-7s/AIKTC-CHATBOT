# backend/prompt/builder.py
import re
from .system_prompt import SYSTEM_PROMPT
from .functions import FUNCTION_DEFINITIONS

HINGLISH_KEYWORDS = {
    "hai", "kya", "milega", "chahiye", "kab", "kahan", "kaise", "hota", "sakte",
    "apna", "mera", "se", "ko", "ki", "ka", "aur", "toh", "bhi",
    "kitna", "kitni", "kis", "kise", "karke", "karo", "karna", "karne",
    "rha", "raha", "rahe", "rhi", "gaya", "gaye", "gyi", "tha", "thi"
}

# ---------------------------------------------------------------------------
# Static context_note placeholder for cache — the real note goes in contents
# ---------------------------------------------------------------------------
_CACHE_CONTEXT_PLACEHOLDER = (
    "(Deterministic context is provided per-turn at the start of the user "
    "message, prefixed with [DETERMINISTIC CONTEXT (this turn): ...].)"
)


def get_cacheable_system_instruction(kb_markdown: str) -> str:
    """Return the system instruction with KB baked in but context_note as a static
    placeholder.  This string is safe to cache because it never changes across turns.

    The actual per-turn context_note is injected into the user's message by the
    chat route when using cached mode.
    """
    return SYSTEM_PROMPT.format(
        context_note=_CACHE_CONTEXT_PLACEHOLDER,
        kb_markdown=kb_markdown,
    )


def get_tools_for_cache() -> dict:
    """Return function definitions and tool config in REST API format for caching."""
    return {
        "tools": [{"functionDeclarations": FUNCTION_DEFINITIONS}],
        "toolConfig": {"functionCallingConfig": {"mode": "ANY"}},
    }

def detect_language(message: str) -> str:
    """Detect if the message is in Hindi, Hinglish, or English."""
    # Check for Devanagari characters
    if any('\u0900' <= char <= '\u097f' for char in message):
        return "hindi"
    
    # Check for Hinglish words
    message_norm = message.lower()
    words = set(re.findall(r'\b[a-z]+\b', message_norm))
    if words.intersection(HINGLISH_KEYWORDS):
        return "hinglish"
        
    return "english"


def build_prompt(
    kb_markdown  : str,
    context_note : str,
    history      : list[dict],
    message      : str,
) -> dict:
    """
    Assemble the complete prompt for the Gemini API call.
    
    Returns a dict suitable for the Gemini messages API:
    {
        "system_instruction": str,
        "contents": [{"role": ..., "parts": [{"text": ...}]}],
        "tools": [...]
    }
    
    Token budget: Hard cap at 180,000 tokens.
    If exceeded, history is trimmed to last 2 turns (1 pair).
    Gemini 1.5 Flash context: 1,000,000 tokens.
    Our prompt ceiling: 180,000 (leaves 820k for safety margin).
    
    Token estimation: 1 token ≈ 4 characters (English)
    KB markdown at 85k chars ≈ 21,250 tokens
    System prompt ≈ 2,000 tokens
    History (8 messages, ~100 chars each) ≈ 200 tokens
    Current message ≈ 50 tokens
    Total typical: ~23,500 tokens — well within budget.
    """
    # Build system instruction
    system = SYSTEM_PROMPT.format(
        context_note=context_note or "(No deterministic context — answer from KB.)",
        kb_markdown=kb_markdown
    )
    
    # Append dynamic language instruction to override history bias
    lang = detect_language(message)
    if lang == "english":
        lang_directive = (
            "\n[CRITICAL LANGUAGE DIRECTIVE: The student's latest message is in English. "
            "You MUST respond in standard, grammatically correct English. Ignore any prior "
            "Hindi/Hinglish responses in the history and switch to English immediately.]"
        )
    elif lang == "hindi":
        lang_directive = (
            "\n[CRITICAL LANGUAGE DIRECTIVE: The student's latest message is in Devanagari Hindi. "
            "You MUST respond in standard Hindi using the Devanagari script.]"
        )
    else:
        lang_directive = (
            "\n[CRITICAL LANGUAGE DIRECTIVE: The student's latest message is in Hinglish. "
            "You MUST respond in warm, natural Hinglish (Hindi written in the Roman script).]"
        )
    
    system += lang_directive
    
    # Estimate token count (rough: chars / 4)
    estimated_tokens = (len(system) + len(message)) // 4
    
    # Trim history if over budget
    working_history = history[-8:]
    history_tokens = sum(len(t.get("content", "")) for t in working_history) // 4
    
    if estimated_tokens + history_tokens > 180_000:
        working_history = history[-2:]  # Last 1 pair only
    
    # Convert history to Gemini format
    contents = []
    import json
    for turn in working_history:
        role = "user" if turn["role"] == "user" else "model"
        content_text = turn["content"]
        
        if role == "model" and content_text.startswith("{") and "function" in content_text:
            try:
                data = json.loads(content_text)
                func_name = data.get("function")
                args = data.get("args", {})
                
                # Format dynamically based on function to give LLM high-quality semantic context
                if func_name == "show_prediction":
                    content_text = (
                        f"[Rendered Prediction Card]\n"
                        f"Department: {args.get('dept_name', args.get('dept'))}\n"
                        f"Percentile: {args.get('percentile')}\n"
                        f"Category: {args.get('category')}\n"
                        f"Verdict: {args.get('verdict')}\n"
                        f"Reasoning: {args.get('reasoning')}"
                    )
                elif func_name == "show_multi_pred":
                    preds = args.get("predictions", [])
                    preds_str = "\n".join([
                        f"- {p.get('dept_name', p.get('dept'))}: {p.get('verdict')} (Reasoning: {p.get('reasoning')})"
                        for p in preds
                    ])
                    content_text = (
                        f"[Rendered Multiple Predictions Card]\n"
                        f"Percentile: {args.get('percentile')}\n"
                        f"Category: {args.get('category')}\n"
                        f"Predictions:\n{preds_str}"
                    )
                elif func_name == "show_table":
                    content_text = f"[Rendered Table: {args.get('title')}]"
                elif func_name == "show_list":
                    content_text = f"[Rendered List: {args.get('title')}]"
                elif func_name == "show_steps":
                    content_text = f"[Rendered Step-by-Step Guide: {args.get('title')}]"
                elif func_name == "show_contact":
                    content_text = f"[Rendered Contact Details: {args.get('reason')}]"
                elif func_name == "show_media_card":
                    content_text = f"[Rendered Profile Card for {args.get('name')}]"
                elif func_name == "show_faculty_grid":
                    content_text = f"[Rendered Faculty Grid for {args.get('dept_name')}]"
                elif func_name == "show_comparison":
                    content_text = f"[Rendered Fee Comparison: {args.get('title')}]"
            except Exception:
                pass
                
        contents.append({
            "role": role,
            "parts": [{"text": content_text}]
        })
    
    # Add current message
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })
    
    return {
        "system_instruction": system,
        "contents": contents,
        "tools": FUNCTION_DEFINITIONS,
        "tool_config": {"function_calling_config": {"mode": "ANY"}}
    }