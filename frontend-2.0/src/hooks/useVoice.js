import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * useVoice — Web Speech API integration (conditional).
 * Only activates if the browser supports SpeechRecognition.
 * The mic button in InputBar is hidden when `supported` is false.
 */
export function useVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const supported = !!SpeechRecognition;

  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!supported) return;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-IN';

    recognition.onresult = (event) => {
      const text = event.results[0]?.[0]?.transcript || '';
      setTranscript(text);
      setListening(false);
    };

    recognition.onerror = () => {
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
    };
  }, [supported]);

  const startListening = useCallback(() => {
    if (!supported || !recognitionRef.current) return;
    setTranscript('');
    setListening(true);
    recognitionRef.current.start();
  }, [supported]);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    recognitionRef.current.stop();
    setListening(false);
  }, []);

  return { supported, listening, transcript, startListening, stopListening };
}
