# backend/llm/gemini_client.py
import httpx
import json
import os
import logging
from typing import AsyncGenerator

from config import settings

logger = logging.getLogger("aiktc.llm")

# ---------------------------------------------------------------------------
# Gemini Context Caching API
# ---------------------------------------------------------------------------
GEMINI_CACHE_URL = "https://generativelanguage.googleapis.com/v1beta/cachedContents"


async def create_cached_content(
    system_instruction_text: str,
    tools: list[dict],
    tool_config: dict,
    model: str | None = None,
    ttl: int = 3600,
) -> str | None:
    """Upload static system instruction + tools as a Gemini cached content.

    Returns the cache name (e.g. 'cachedContents/abc123') or None on failure.
    The cache lives server-side for ``ttl`` seconds, during which any
    generateContent call can reference it to skip re-sending those tokens.
    """
    api_key = settings.gemini_api_key
    if not api_key:
        logger.error("Cannot create cache — GEMINI_API_KEY not set")
        return None

    model_id = model or settings.gemini_model or "gemini-2.5-flash"

    cache_payload = {
        "model": f"models/{model_id}",
        "systemInstruction": {
            "parts": [{"text": system_instruction_text}]
        },
        "tools": tools,       # already in REST format: [{"functionDeclarations": [...]}]
        "toolConfig": tool_config,
        "ttl": f"{ttl}s",
    }

    url = f"{GEMINI_CACHE_URL}?key={api_key}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=cache_payload)
            if response.status_code == 200:
                data = response.json()
                cache_name = data.get("name")
                logger.info(f"Created Gemini cache: {cache_name} (model={model_id}, ttl={ttl}s)")
                return cache_name
            else:
                logger.warning(
                    f"Cache creation failed: HTTP {response.status_code} — {response.text[:300]}"
                )
        except Exception as e:
            logger.exception(f"Exception creating Gemini cache: {e}")
    return None


async def stream_with_cache(
    cache_name: str,
    contents: list[dict],
    model: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Stream a response using a previously created Gemini cached content.

    ``contents`` should contain only the conversation turns (user + model) —
    the system instruction and tools are already inside the cache.

    Yields the same chunk dicts as ``call_gemini_stream``:
      - {"type": "function_call", "name": ..., "args": ...}
      - {"type": "text_chunk", "content": ...}
      - {"type": "error", "message": ...}
    """
    api_key = settings.gemini_api_key
    model_id = model or settings.gemini_model or "gemini-2.5-flash"

    headers = {"Content-Type": "application/json"}
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}"
        f":streamGenerateContent?key={api_key}&alt=sse"
    )

    payload = {
        "contents": contents,
        "cachedContent": cache_name,
        # NOTE: systemInstruction and tools are NOT sent — they live in the cache.
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    logger.warning(
                        f"Cached stream failed: HTTP {response.status_code} — {body.decode()[:300]}"
                    )
                    yield {"type": "error", "message": f"API error {response.status_code}"}
                    return

                logger.info(f"Cached stream connected: model={model_id}, cache={cache_name}")

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    candidates = chunk.get("candidates", [])
                    for candidate in candidates:
                        content = candidate.get("content", {})
                        for part in content.get("parts", []):
                            if "functionCall" in part:
                                fc = part["functionCall"]
                                yield {
                                    "type": "function_call",
                                    "name": fc.get("name", "show_text"),
                                    "args": fc.get("args", {}),
                                }
                                return
                            elif "text" in part:
                                yield {"type": "text_chunk", "content": part["text"]}

                    # End of stream
                return

    except httpx.TimeoutException:
        logger.warning(f"Cached stream timed out: cache={cache_name}")
        yield {"type": "error", "message": "Request timed out. Please try again."}
    except Exception as e:
        logger.exception(f"Exception during cached stream: {e}")
        yield {"type": "error", "message": "Something went wrong. Please try again."}

async def call_gemini_stream(prompt: dict) -> AsyncGenerator[dict, None]:
    """
    Send prompt to Gemini model with function calling.
    Yields parsed chunks as they arrive.
    
    If the primary model is rate-limited (HTTP 429) or unavailable (HTTP 503),
    automatically falls back to alternative Gemini models to prevent service outages.
    
    On successful function call, yields:
      {"type": "function_call", "name": "show_prediction", "args": {...}}
    
    On text response (fallback), yields:
      {"type": "text_chunk", "content": "..."}
    
    On error, yields:
      {"type": "error", "message": "..."}
    
    The caller (chat route) converts these to SSE events for the frontend.
    """
    api_key = settings.gemini_api_key
    if not api_key:
        yield {"type": "error", "message": "GEMINI_API_KEY is not configured in env."}
        return

    primary_model = settings.gemini_model or "gemini-3.5-flash"
    
    # Priority list of models to fallback to in case of rate limits
    fallback_models = [
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-flash-latest",
        "gemini-2.5-pro",
        "gemini-pro-latest"
    ]
    
    # Ensure primary model is first, followed by others without duplicates
    models_to_try = [primary_model]
    for m in fallback_models:
        if m != primary_model:
            models_to_try.append(m)

    headers = {"Content-Type": "application/json"}
    
    # Map builder's snake_case prompt dict to camelCase REST API schema
    rest_payload = {
        "contents": prompt["contents"]
    }
    if "system_instruction" in prompt:
        rest_payload["systemInstruction"] = {
            "parts": [{"text": prompt["system_instruction"]}]
        }
    if "tools" in prompt:
        # REST API expects: [{"functionDeclarations": [...]}]
        rest_payload["tools"] = [
            {"functionDeclarations": prompt["tools"]}
        ]
    if "tool_config" in prompt:
        # REST API expects: {"toolConfig": {"functionCallingConfig": {"mode": "ANY"}}}
        rest_payload["toolConfig"] = {
            "functionCallingConfig": {
                "mode": prompt["tool_config"]["function_calling_config"]["mode"]
            }
        }

    # Save raw REST payload for debug inspection
    try:
        with open("debug_payload.json", "w", encoding="utf-8") as debug_f:
            json.dump(rest_payload, debug_f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save debug payload: {e}")

    for idx, model in enumerate(models_to_try):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}&alt=sse"
        logger.info(f"Attempting Gemini stream call with model: {model} (attempt {idx + 1}/{len(models_to_try)})")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=rest_payload, headers=headers) as response:
                    # Check for rate-limiting or service unavailability
                    if response.status_code in (429, 503):
                        body = await response.aread()
                        logger.warning(
                            f"Model {model} failed with status {response.status_code}. "
                            f"Retrying next model. Error details: {body.decode()}"
                        )
                        continue
                    
                    if response.status_code != 200:
                        body = await response.aread()
                        logger.error(f"Gemini API returned status {response.status_code} for model {model}: {body.decode()}")
                        # If this is the last model, return the error
                        if idx == len(models_to_try) - 1:
                            yield {"type": "error", "message": f"API error {response.status_code}"}
                            return
                        continue
                    
                    # Successfully established stream connection (status 200)
                    logger.info(f"Successfully connected stream with model: {model}")
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        
                        # Extract function call if present
                        candidates = chunk.get("candidates", [])
                        for candidate in candidates:
                            content = candidate.get("content", {})
                            for part in content.get("parts", []):
                                if "functionCall" in part:
                                    fc = part["functionCall"]
                                    yield {
                                        "type": "function_call",
                                        "name": fc.get("name", "show_text"),
                                        "args": fc.get("args", {})
                                    }
                                    return
                                elif "text" in part:
                                    yield {"type": "text_chunk", "content": part["text"]}
                    
                    # Successfully processed full stream response
                    return

        except httpx.TimeoutException:
            logger.warning(f"Model {model} stream request timed out.")
            if idx == len(models_to_try) - 1:
                yield {"type": "error", "message": "Request timed out. Please try again."}
                return
        except Exception as e:
            logger.exception(f"Exception during stream call with model {model}")
            if idx == len(models_to_try) - 1:
                yield {"type": "error", "message": "Something went wrong. Please try again."}
                return


def get_router_key(function_name: str) -> str:
    """
    Convert Gemini function name to frontend renderer key.
    Strips the show_ prefix. This is the ONLY routing signal.
    
    Examples:
      show_prediction → prediction
      show_multi_pred → multi_pred
      show_faculty_grid → faculty_grid
    """
    return function_name.replace("show_", "", 1)