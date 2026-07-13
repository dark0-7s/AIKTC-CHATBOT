import { useState, useCallback } from 'react';
import { sendChatMessage } from '../api/chat';

export function useChat(sessionId) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim()) return;
    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    let botMessage = { role: 'assistant', content: '', functionName: null, args: null };
    setMessages(prev => [...prev, botMessage]);

    try {
      await sendChatMessage(sessionId, text, (chunk) => {
        if (chunk.type === 'function_call') {
          botMessage.functionName = chunk.name;
          botMessage.args = chunk.args;
          botMessage.content = ''; // clear any text
          setMessages(prev => [...prev.slice(0, -1), { ...botMessage }]);
        } else if (chunk.type === 'text_chunk') {
          botMessage.content += chunk.content;
          setMessages(prev => [...prev.slice(0, -1), { ...botMessage }]);
        }
      });
    } catch (err) {
      console.error('Chat error:', err);
      botMessage.functionName = 'show_contact';
      botMessage.args = {
        reason: 'Unable to connect to the server. Please check your network or try again later.',
        contacts: [
          {
            label: "Admissions Office (Engineering)",
            phone: "+91 8104363070",
            email: "admissions@aiktc.ac.in"
          },
          {
            label: "General Enquiry",
            phone: "+91 91371 23439",
            email: "aiktc.newpanvel@aiktc.ac.in"
          }
        ]
      };
      setMessages(prev => [...prev.slice(0, -1), { ...botMessage }]);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  return { messages, loading, sendMessage };
}
