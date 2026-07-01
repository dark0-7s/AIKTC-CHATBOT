import { useState, useEffect } from 'react';

export function useVoice() {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  // Placeholder – actual Web Speech API implementation when required
  return { listening, transcript, startListening: () => {}, stopListening: () => {} };
}