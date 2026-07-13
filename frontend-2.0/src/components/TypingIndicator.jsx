export default function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
      <div style={{ width: 30, height: 30, background: "#E1F5EE", borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <i className="ti ti-school" style={{ fontSize: 16, color: "#0F6E56" }} />
      </div>
      <div style={{ background: "#f1f5f9", borderRadius: 18, padding: "10px 14px", display: "flex", gap: 4 }}>
        <span className="typing-dot" style={{ animationDelay: "0s" }} />
        <span className="typing-dot" style={{ animationDelay: "0.2s" }} />
        <span className="typing-dot" style={{ animationDelay: "0.4s" }} />
      </div>
    </div>
  );
}
