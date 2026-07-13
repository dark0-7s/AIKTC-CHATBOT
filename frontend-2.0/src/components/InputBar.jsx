import { useState, useContext, useEffect } from "react";
import { LangContext } from "../context/LangContext";
import { useLabel } from "../utils/labels";
import { useVoice } from "../hooks/useVoice";

export default function InputBar({ onSend, disabled }) {
  const [text, setText] = useState("");
  const { lang } = useContext(LangContext);
  const placeholder = useLabel(lang, "input_placeholder");
  const sendLabel = useLabel(lang, "send_button");

  const { supported: micSupported, listening, transcript, startListening, stopListening } = useVoice();

  // When voice transcript arrives, populate the input
  useEffect(() => {
    if (transcript) {
      setText(transcript);
    }
  }, [transcript]);

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text);
      setText("");
    }
  };

  const handleMicClick = () => {
    if (listening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <div style={{ padding: 12, borderTop: "0.5px solid #e2e8f0", display: "flex", gap: 8, background: "white" }}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        placeholder={placeholder}
        disabled={disabled}
        style={{ flex: 1, padding: "10px 14px", border: "1px solid #cbd5e1", borderRadius: 40, outline: "none", fontSize: 14 }}
      />
      {micSupported && (
        <button
          onClick={handleMicClick}
          disabled={disabled}
          className={`mic-btn${listening ? ' listening' : ''}`}
          title={listening ? "Stop listening" : "Voice input"}
        >
          <i className={`ti ti-${listening ? 'player-stop' : 'microphone'}`} style={{ fontSize: 16 }} />
        </button>
      )}
      <button
        onClick={handleSend}
        disabled={disabled}
        style={{ background: "#0F6E56", border: "none", borderRadius: 40, padding: "0 18px", color: "white", fontWeight: 500, cursor: "pointer" }}
      >
        {sendLabel}
      </button>
    </div>
  );
}
