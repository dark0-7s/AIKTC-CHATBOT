import React, { useState, useEffect } from 'react';
import ChatShell from './components/ChatShell';
import { LangContext } from './context/LangContext';
import { getLabels } from './utils/labels';

export default function App() {
  const [lang, setLang] = useState('en'); // en, hi, hinglish
  const labels = getLabels();
  return (
    <LangContext.Provider value={{ lang, setLang, labels }}>
      <div
        style={{
          width: "100vw",
          height: "100vh",
          display: "flex",
          justifyContent: "center",
          alignItems: "stretch",
          padding: 0,
          margin: 0,
          overflow: "hidden",
          background: "#ffffff",
          minHeight: 0,
        }}
      >
        <ChatShell />
      </div>
    </LangContext.Provider>
  );
}