import { useState, useEffect, useRef } from "react";
import MessageList from "./MessageList";
import InputBar from "./InputBar";
import QuickChips from "./QuickChips";
import ErrorBoundary from "./ErrorBoundary";
import { useChat } from "../hooks/useChat";
import { getSessionId } from "../utils/sessionId";

export default function ChatShell() {
  const sessionId = getSessionId();
  const { messages, loading, sendMessage } = useChat(sessionId);
  const showChips = !messages || messages.length === 0;
  const isMobile = window.innerWidth <= 768;
  const messagesRef = useRef(null);

useEffect(() => {
  if (!messagesRef.current) return;

  messagesRef.current.scrollTo({
    top: messagesRef.current.scrollHeight,
    behavior: "smooth",
  });
}, [messages.length, loading]);
  // Use a base64 encoded fallback watermark if image doesn't load
  const logoFallback = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect width='200' height='200' fill='%23667eea' opacity='0.3'/%3E%3Ctext x='50%25' y='50%25' font-size='40' font-weight='bold' fill='%23667eea' text-anchor='middle' dy='.3em' opacity='0.5'%3EAIKTC%3C/text%3E%3C/svg%3E";

  return (
   <div
  style={{
    width: "100%",
    height: "100%",
    maxWidth: isMobile ? "100%" : "1200px",
    borderRadius: isMobile ? 0 : 20,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  }}
>
      
     <div
  style={{
    flex: 1,
    height: "100%",
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
    minHeight: 0,
    position: "relative",
    overflow: "hidden",
  }}
>
        {/* Header */}
        <div
          style={{
            padding: "12px 18px",
            background: "linear-gradient(135deg,#667eea 0%, #764ba2 100%)",
            color: "#fff",
            display: "flex",
            alignItems: "center",
            gap: 15,
            flexShrink: 0,
            zIndex: 10,
            position: "relative",
          }}
        >
          <img
            src="/aiktc-logo.png"
            alt="AIKTC"
            style={{
              width: isMobile ? 36 : 42,
              height: isMobile ? 36 : 42,
              borderRadius: 10,
              background: "#fff",
              padding: 4,
            }}
            onError={(e) => {
              e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='42' height='42'%3E%3Crect width='42' height='42' fill='%23667eea'/%3E%3Ctext x='50%25' y='50%25' font-size='16' font-weight='bold' fill='%23fff' text-anchor='middle' dy='.3em'%3EAIK%3C/text%3E%3C/svg%3E";
            }}
          />

          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <h3
              style={{
                margin: 0,
               fontSize: isMobile ? 16 : 20,
                fontWeight: 700,
              }}
            >
              AIKTC AI Assistant
            </h3>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginTop: 4,
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "#22c55e",
                }}
              />

              <span
                style={{
                  fontSize: isMobile ? 11 : 12,
                }}
              >
                Online • Ready to help
              </span>
            </div>
          </div>

        <a
  href={`${import.meta.env.VITE_API_URL || "http://localhost:8001"}/api/admin/dashboard`}
  target="_blank"
  rel="noopener noreferrer"
            style={{
              width: isMobile ? 40 : 48,
              height: isMobile ? 40 : 48,
              borderRadius: 10,
              background: "#fff",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              textDecoration: "none",
              color: "#64748b",
            }}
          >
            <i className="ti ti-shield-lock" />
          </a>
        </div>

        {/* Chat Container */}
<div
  style={{
    flex: 1,
    display: "flex",
    flexDirection: "column",
    minHeight: 0,
    overflow: "hidden",
    position: "relative",
    background: "#111827",
  }}
>
          {/* Fixed Watermark - Using both image and text fallback */}
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              width: isMobile ? "160px" : "280px",
              maxWidth: "70%",
              pointerEvents: "none",
              zIndex: 1,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              flexDirection: "column",
            }}
          >
            <img
              src="/aiktc-logo.png"
              alt="AIKTC"
              style={{
                width: "100%",
                height: "auto",
                display: "block",
                userSelect: "none",
                opacity: 0.12,
                filter: "grayscale(0.2)",
              }}
              onError={(e) => {
                // Hide image and show text fallback
                e.target.style.display = "none";
                const parent = e.target.parentElement;
                parent.innerHTML = `
                  <div style="font-size: 72px; font-weight: 900; color: #667eea; opacity: 0.12; letter-spacing: 8px; text-align: center; font-family: Arial, sans-serif;">
                    AIKTC
                    <div style="font-size: 24px; font-weight: 400; opacity: 0.8; letter-spacing: 4px; margin-top: 8px;">Assistant</div>
                  </div>
                `;
              }}
            />
          </div>

          {/* Scrollable Messages Area */}
<div
  ref={messagesRef}
  style={{
    flex: 1,
    height: 0,
    minHeight: 0,
    overflowY: "auto",
    overflowX: "hidden",
    padding: isMobile ? 10 : 18,
    position: "relative",
    display: "flex",
    flexDirection: "column",
  }}
>
            {/* Content - sits on top of watermark */}
            <div
  style={{
    position: "relative",
    zIndex: 5,
    display: "flex",
    flexDirection: "column",
    width: "100%",
  }}
>
              {showChips && <QuickChips onChipClick={sendMessage} />}

           <ErrorBoundary>
  <MessageList
    messages={messages}
    loading={loading}
    sessionId={sessionId}
  />
</ErrorBoundary>

            </div>
          </div>
        </div>

        {/* Input */}
        <div
  style={{
    padding: 16,
    background: "#fff",
    borderTop: "1px solid #e5e7eb",
    flexShrink: 0,
    position: "sticky",
    bottom: 0,
    zIndex: 10,
  }}
>
          <InputBar onSend={sendMessage} disabled={loading} />
        </div>
      </div>
    </div>
  );
}