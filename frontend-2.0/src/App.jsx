import React, { useState } from 'react';
import ChatShell from './components/ChatShell';
import { LangContext } from './context/LangContext';
import { getLabels } from './utils/labels';
import './index.css';

export default function App() {
  const [lang, setLang] = useState('en'); // en, hi, hinglish
  const labels = getLabels();
  return (
    <LangContext.Provider value={{ lang, setLang, labels }}>
      <div style={{ maxWidth: 480, margin: '2rem auto' }}>
        <ChatShell />
      </div>
    </LangContext.Provider>
  );
}
