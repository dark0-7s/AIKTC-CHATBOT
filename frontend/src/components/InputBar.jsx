import { useState } from "react";

export default function InputBar({ onSend, disabled }) {
  const [text, setText] = useState("");

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text);
      setText("");
    }
  };

  return (
    <div style={{ padding: 12, borderTop: "0.5px solid #e2e8f0", display: "flex", gap: 8, background: "white" }}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyPress={(e) => e.key === "Enter" && handleSend()}
        placeholder="Ask anything about admissions, fees, faculty..."
        disabled={disabled}
        style={{ flex: 1, padding: "10px 14px", border: "1px solid #cbd5e1", borderRadius: 40, outline: "none", fontSize: 14 }}
      />
      <button onClick={handleSend} disabled={disabled} style={{ background: "#0F6E56", border: "none", borderRadius: 40, padding: "0 18px", color: "white", fontWeight: 500, cursor: "pointer" }}>
        Send
      </button>
    </div>
  );
}