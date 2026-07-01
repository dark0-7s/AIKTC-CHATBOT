# backend/routes/chat.py
"""
AIKTC AI Chatbot — Chat Route
==============================
Handles the main /chat endpoint with Server-Sent Events (SSE) streaming.
Also provides a /chat/debug endpoint for testing the stream pipeline.

Endpoints:
  POST /chat        — Main streaming chat endpoint
  POST /chat/debug  — Debug endpoint to test SSE stream
"""

import asyncio
import json
import logging
import re
import uuid
from typing import Any, AsyncGenerator

def clean_cjk(value: Any) -> Any:
    """Recursively strip CJK (Chinese/Japanese/Korean) characters from strings/dicts/lists."""
    if isinstance(value, str):
        pattern = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\uff00-\uffef]')
        return pattern.sub('', value)
    elif isinstance(value, dict):
        return {k: clean_cjk(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [clean_cjk(x) for x in value]
    return value


from fastapi import APIRouter, Request, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import settings
from cache.cache_manager import cache_manager
from engine.context_builder import build_context_note
from llm.gemini_client import (
    call_gemini_stream,
    create_cached_content,
    get_router_key,
    stream_with_cache,
)
from logger.query_logger import log_query
from logger.analytics import classify_topic, extract_query_departments
from prompt.builder import (
    build_prompt,
    get_cacheable_system_instruction,
    get_tools_for_cache,
)
from session.manager import load_session, save_session

# ==============================================================================
# LOGGING
# ==============================================================================
logger = logging.getLogger("aiktc.chat")

# ==============================================================================
# ROUTER & RATE LIMITER
# ==============================================================================
router  = APIRouter(tags=["Chat"])
limiter = Limiter(key_func=get_remote_address)

# ==============================================================================
# CONSTANTS
# ==============================================================================
MAX_MESSAGE_LENGTH = 500
SSE_CONTENT_TYPE   = "text/event-stream"

# Fallback contact shown when Gemini is unavailable
FALLBACK_CONTACT_ARGS = {
    "reason": (
        "The AI service is temporarily unavailable. "
        "Please contact the admissions office directly for assistance."
    ),
    "contacts": [
        {
            "label": "Admissions Office (Engineering)",
            "phone": "+91 8104363070",
            "email": "admissions@aiktc.ac.in",
        },
        {
            "label": "General Enquiry",
            "phone": "+91 91371 23439",
            "email": "aiktc.newpanvel@aiktc.ac.in",
        },
    ],
}


# ==============================================================================
# REQUEST MODEL
# ==============================================================================
class ChatRequest(BaseModel):
    """
    Request body for the /chat endpoint.

    Fields:
        session_id : Unique session identifier.
                     Send null or omit for first message — a new UUID will be generated.
        message    : Student's message (1–500 characters)
    """

    session_id: str | None = Field(
        default=None,
        description="Session ID — send null for first message, reuse for follow-ups",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        description="Student's message (max 500 characters)",
    )

    @validator("message")
    def message_not_empty(cls, v: str) -> str:
        """Strip whitespace and reject empty messages."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace only")
        return stripped

    @validator("session_id", pre=True, always=True)
    def generate_session_id_if_missing(cls, v: str | None) -> str:
        """Auto-generate a UUID session_id if not provided."""
        if not v or not str(v).strip():
            return str(uuid.uuid4())
        return str(v).strip()

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": None,
                "message"   : "What is the cutoff for Computer Engineering?",
            }
        }
ChatRequest.model_rebuild()



# ==============================================================================
# SSE HELPERS
# ==============================================================================
def _sse(data: dict) -> str:
    """Format a dict as a Server-Sent Event string."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _sse_text(content: str) -> str:
    """Format a text chunk as SSE."""
    return _sse({"type": "text_chunk", "content": content})


def _sse_function(name: str, args: dict) -> str:
    """Format a function call as SSE."""
    return _sse({"type": "function_call", "name": name, "args": args})


def _sse_error(message: str) -> str:
    """Format an error as SSE."""
    return _sse({"type": "error", "message": message})


def _sse_done(session_id: str) -> str:
    """Format a done signal as SSE — signals frontend stream is complete."""
    return _sse({"type": "done", "session_id": session_id})


# ==============================================================================
# STREAM GENERATOR
# ==============================================================================
async def _stream_response(
    request   : Request,
    session_id: str,
    message   : str,
) -> AsyncGenerator[str, None]:
    logger.info(f"STREAM STARTED: {message}")
    """
    Core streaming generator for the /chat endpoint.

    Flow:
      1. Load session (history + anchor)
      2. Build deterministic context note from engine
      3. Build full LLM prompt
      4. Attempt to use Gemini cached content (first turn creates cache)
      5. Stream Gemini response chunk by chunk
      6. Handle function calls and text chunks separately
      7. On cache error, fall back seamlessly to full prompt
      8. Log query to database
      9. Save updated session

    Yields:
        str: SSE-formatted strings
    """
    # -- Load session --
    session  = load_session(session_id)
    history  = session["history"]
    anchor   = session["anchor"]

    # -- Build prompt --
    context_note = build_context_note(message, history)
    prompt       = build_prompt(
        kb_markdown  = request.app.state.kb_markdown,
        context_note = context_note,
        history      = history,
        message      = message,
    )

    # -- Determine caching path --
    use_cache = settings.gemini_cache_enabled
    cache_name: str | None = None

    if use_cache:
        cache_name = cache_manager.get(session_id)

        # First turn in session — create a new cache
        if cache_name is None and not history:
            try:
                static_system = get_cacheable_system_instruction(
                    request.app.state.kb_markdown
                )
                tool_info = get_tools_for_cache()
                cache_name = await create_cached_content(
                    system_instruction_text=static_system,
                    tools=tool_info["tools"],
                    tool_config=tool_info["toolConfig"],
                )
                if cache_name:
                    cache_manager.set(session_id, cache_name)
            except Exception as e:
                logger.warning(f"Cache creation failed, using full prompt: {e}")
                cache_name = None

    # -- Build cached contents (inject context_note into user message) --
    cached_contents: list[dict] | None = None
    if cache_name:
        # When using cached mode, the system instruction in the cache has a
        # placeholder for context_note.  We prepend the real context_note to
        # the user's message so the LLM always sees fresh deterministic context.
        context_prefix = (
            f"[DETERMINISTIC CONTEXT (this turn):\n"
            f"{context_note or '(No deterministic context — answer from KB.)'}\n"
            f"]\n\n"
        )
        # Re-use the same contents structure from the full prompt, but
        # replace the last user message with the context-prefixed version.
        cached_contents = list(prompt["contents"])  # shallow copy
        last_user_msg = cached_contents[-1]  # always the current user message
        cached_contents[-1] = {
            "role": "user",
            "parts": [{"text": context_prefix + message}],
        }

    # -- Streaming state --
    response_type  : str            = "text"
    raw_output     : str            = ""
    final_function : str | None     = None
    final_args     : dict | None    = None

    # -- Stream from Gemini (cached path with fallback) --
    try:
        used_cache = False
        fell_back  = False

        if cache_name and cached_contents is not None:
            used_cache = True
            async for chunk in stream_with_cache(cache_name, cached_contents):
                chunk_type = chunk.get("type")

                if chunk_type == "error" and not fell_back:
                    # Cache expired or deleted — evict and fall back
                    cache_manager.remove(session_id)
                    logger.warning(
                        f"Cache {cache_name} failed, falling back to full prompt"
                    )
                    fell_back = True
                    # Fall through to full-prompt loop below
                    break

                if chunk_type == "function_call":
                    final_function = chunk["name"]
                    final_args     = clean_cjk(chunk["args"])
                    response_type  = get_router_key(final_function)
                    yield _sse_function(final_function, final_args)

                elif chunk_type == "text_chunk":
                    content     = clean_cjk(chunk.get("content", ""))
                    raw_output += content
                    yield _sse_text(content)

                else:
                    logger.warning(f"Unknown chunk type: {chunk_type}")

        # Full-prompt path (original behaviour or fallback from cache failure)
        if not used_cache or fell_back:
            async for chunk in call_gemini_stream(prompt):
                chunk_type = chunk.get("type")

                if chunk_type == "function_call":
                    final_function = chunk["name"]
                    final_args     = clean_cjk(chunk["args"])
                    response_type  = get_router_key(final_function)
                    yield _sse_function(final_function, final_args)

                elif chunk_type == "text_chunk":
                    content     = clean_cjk(chunk.get("content", ""))
                    raw_output += content
                    yield _sse_text(content)

                elif chunk_type == "error":
                    logger.error(f"LLM error: {chunk.get('message', 'Unknown error')}")
                    yield _sse_function("show_contact", FALLBACK_CONTACT_ARGS)
                    response_type  = "contact"
                    final_function = "show_contact"
                    final_args     = FALLBACK_CONTACT_ARGS
                    break

                else:
                    logger.warning(f"Unknown chunk type: {chunk_type}")

    except Exception as exc:
        logger.exception(f"Exception during /chat stream | session={session_id[:8]}")
        yield _sse_function("show_contact", FALLBACK_CONTACT_ARGS)
        yield _sse_done(session_id)
        return

    # -- Classify for analytics --
    try:
        topic = classify_topic(message, response_type)
        departments = extract_query_departments(message, response_type, final_args)
    except Exception as e:
        logger.error(f"Analytics classification failed: {e}")
        topic = "other"
        departments = "[]"

    # -- Log query to database --
    try:
        log_query(
            session_id            = session_id,
            message               = message,
            response_type         = response_type,
            raw_llm_output        = raw_output if response_type == "text" else json.dumps(final_args or {}),
            deterministic_context = context_note,
            topic                 = topic,
            departments           = departments,
        )
    except Exception as e:
        logger.error(f"Failed to log query: {e}")

    # -- Build updated history --
    new_history = history + [{"role": "user", "content": message}]

    if final_function and final_args is not None:
        # Store function call result as structured assistant message
        assistant_content = json.dumps(
            {"function": final_function, "args": final_args},
            ensure_ascii=False
        )
    else:
        assistant_content = raw_output

    new_history.append({"role": "assistant", "content": assistant_content})

    # -- Save session --
    try:
        is_type_a = "Confidence: HIGH" in context_note
        save_session(session_id, new_history, anchor, is_type_a=is_type_a)
    except Exception as e:
        logger.error(f"Failed to save session {session_id[:8]}: {e}")

    # -- Signal stream complete --
    yield _sse_done(session_id)


# ==============================================================================
# ROUTES
# ==============================================================================
@router.post(
    "/chat",
    summary     = "Main chat endpoint — streams AI response via SSE",
    description = (
        "Send a student message and receive a streaming AI response.\n\n"
        "**First message:** Send `session_id` as `null` — a UUID is auto-generated.\n\n"
        "**Follow-up messages:** Use the `session_id` returned in the `done` event.\n\n"
        "**Response format:** Server-Sent Events (SSE) with these event types:\n"
        "- `text_chunk` — A token of the text response\n"
        "- `function_call` — A structured response (table, card, contact, etc.)\n"
        "- `error` — An error occurred\n"
        "- `done` — Stream is complete, contains final `session_id`"
    ),
)
@limiter.limit("60/minute")
async def chat(request: Request, payload: ChatRequest = Body(...)):
    """
    Main chat endpoint.
    Streams the AI response as Server-Sent Events.
    """
    logger.info(
        f"Chat request | session={payload.session_id[:8]}... | "
        f"message_len={len(payload.message)}"
    )

    return StreamingResponse(
        _stream_response(request, payload.session_id, payload.message),
        media_type = SSE_CONTENT_TYPE,
        headers    = {
            "Cache-Control"    : "no-cache",
            "X-Accel-Buffering": "no",   # Disable Nginx buffering for SSE
        },
    )


@router.post(
    "/chat/debug",
    summary     = "Debug endpoint — tests SSE stream pipeline",
    description = (
        "Sends a test SSE stream with 3 chunks and a done event.\n"
        "Use this to verify the frontend SSE connection is working correctly."
    ),
)
async def chat_debug(request: Request):
    """
    Debug endpoint — streams test SSE events.
    Does not call Gemini or touch the database.
    """
    async def _debug_stream() -> AsyncGenerator[str, None]:
        test_session_id = str(uuid.uuid4())
        chunks = [
            "Hello! ",
            "This is a debug stream. ",
            "SSE is working correctly! ✅",
        ]
        for chunk in chunks:
            yield _sse_text(chunk)
            await asyncio.sleep(0.1)

        yield _sse_done(test_session_id)

    logger.info("Debug stream requested")
    return StreamingResponse(
        _debug_stream(),
        media_type = SSE_CONTENT_TYPE,
        headers    = {
            "Cache-Control"    : "no-cache",
            "X-Accel-Buffering": "no",
        },
    )