const API_BASE = import.meta.env.VITE_API_URL || "";

/**
 * Resilient fetch with automatic retries and direct localhost fallback.
 * Prevents "Unable to connect to the server" errors during transient network glitches,
 * server reloads, or proxy hiccups.
 */
async function resilientFetch(url, options, maxRetries = 2) {
  let lastError = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);

      // If server returned 502/503/504 (e.g. Vite proxy blip during restart), retry
      if ([502, 503, 504].includes(response.status) && attempt < maxRetries) {
        await new Promise((r) => setTimeout(r, 400 * (attempt + 1)));
        continue;
      }

      if (response.ok) {
        return response;
      }

      // If other non-ok HTTP code, record error
      lastError = new Error(`Server returned HTTP ${response.status}`);
    } catch (err) {
      lastError = err;
      if (attempt < maxRetries) {
        await new Promise((r) => setTimeout(r, 400 * (attempt + 1)));
      }
    }
  }

  // Fallback: If relative /api proxy failed, try direct connection to backend port 8001
  const isLocal =
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  if (url.startsWith('/api') && isLocal) {
    try {
      const directUrl = `http://127.0.0.1:8001${url}`;
      const fallbackRes = await fetch(directUrl, options);
      if (fallbackRes.ok) {
        return fallbackRes;
      }
    } catch (_) {
      // Direct connection also failed
    }
  }

  throw lastError || new Error("Failed to connect to AIKTC server");
}

export async function sendChatMessage(sessionId, message, onChunk) {
  const url = API_BASE ? `${API_BASE}/api/chat` : '/api/chat';
  const response = await resilientFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message })
  });

  if (!response.ok) {
    throw new Error(`Server returned HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop();
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          onChunk(data);
        } catch (e) {
          console.warn('SSE JSON parse warning:', e, line);
        }
      }
    }
  }
}
