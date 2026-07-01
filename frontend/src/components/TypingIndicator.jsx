export default function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
      <div style={{ width: 30, height: 30, background: "#E1F5EE", borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <i className="ti ti-school" style={{ fontSize: 16, color: "#0F6E56" }} />
      </div>
      <div style={{ background: "#f1f5f9", borderRadius: 18, padding: "10px 14px", display: "flex", gap: 4 }}>
        <span style={{ width: 6, height: 6, background: "#94a3b8", borderRadius: "50%", animation: "pulse 1.2s infinite" }} />
        <span style={{ width: 6, height: 6, background: "#94a3b8", borderRadius: "50%", animation: "pulse 1.2s 0.2s infinite" }} />
        <span style={{ width: 6, height: 6, background: "#94a3b8", borderRadius: "50%", animation: "pulse 1.2s 0.4s infinite" }} />
      </div>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.2); }
        }
      `}</style>
    </div>
  );
}