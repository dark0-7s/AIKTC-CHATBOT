import { useState, useRef, useEffect } from "react";
import MessageList from "./MessageList";
import InputBar from "./InputBar";
import QuickChips from "./QuickChips";
import ErrorBoundary from "./ErrorBoundary";
import { useChat } from "../hooks/useChat";
import { getSessionId } from "../utils/sessionId";

export default function ChatShell() {
  const sessionId = getSessionId();
  const { messages, loading, sendMessage } = useChat(sessionId);
  const showChips = messages.length === 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "min(700px, 90vh)", minHeight: 560, background: "white", borderRadius: 24, boxShadow: "0 4px 20px rgba(0,0,0,0.1)", overflow: "hidden" }}>
      <div style={{ padding: "12px 18px", borderBottom: "0.5px solid #e2e8f0", display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
        <div style={{ width: 34, height: 34, borderRadius: 8, background: "#E1F5EE", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <i className="ti ti-school" style={{ fontSize: 18, color: "#0F6E56" }} />
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ fontWeight: 500, fontSize: 14, margin: 0, color: "#0f172a" }}>AIKTC Student Desk</p>
          <p style={{ fontSize: 12, color: "#475569", margin: 0 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", display: "inline-block", marginRight: 5 }} />
            Anjuman-I-Islam's Kalsekar Technical Campus
          </p>
        </div>
        <a
          href="/api/admin/dashboard"
          target="_blank"
          rel="noopener noreferrer"
          title="Admin Dashboard"
          style={{
            width: 32, height: 32, borderRadius: 8,
            background: "#f1f5f9", display: "flex", alignItems: "center", justifyContent: "center",
            color: "#64748b", textDecoration: "none", transition: "all 0.2s ease",
            border: "1px solid #e2e8f0", flexShrink: 0,
          }}
          onMouseEnter={e => { e.currentTarget.style.background = "#e2e8f0"; e.currentTarget.style.color = "#6366f1"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "#f1f5f9"; e.currentTarget.style.color = "#64748b"; }}
        >
          <i className="ti ti-shield-lock" style={{ fontSize: 16 }} />
        </a>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "18px 18px 4px" }}>
        {showChips && <QuickChips onChipClick={sendMessage} />}
        <ErrorBoundary>
          <MessageList messages={messages} loading={loading} />
        </ErrorBoundary>
      </div>
      <InputBar onSend={sendMessage} disabled={loading} />
    </div>
  );
}