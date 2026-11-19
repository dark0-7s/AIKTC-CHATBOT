const API_BASE = import.meta.env.VITE_API_URL || "";

export async function sendChatMessage(sessionId, message, onChunk) {
  const url = API_BASE ? `${API_BASE}/api/chat` : '/api/chat';
  const response = await fetch(url, {
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
