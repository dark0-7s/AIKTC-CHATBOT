// frontend/src/components/renderers/ListCards.jsx

import React, { useState, useEffect } from "react";
import ImageWithFallback from "./ImageWithFallback";
import { parseInline } from "./TextBubble";

export default function ListCards({ data }) {
  const { title, items } = data || {};
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  if (!items || items.length === 0) return null;

  return (
    <div style={{ margin: "10px 0" }}>
      {title && (
        <div style={{ fontWeight: 700, fontSize: 14, color: "#0f172a", marginBottom: 10 }}>
          {parseInline(title)}
        </div>
      )}
      <div
        style={{
          display: "grid",
          gap: isMobile ? 8 : 10,
          gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fill, minmax(280px, 1fr))",
        }}
      >
        {items.map((item, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              gap: 10,
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: 12,
              padding: "10px 12px",
              alignItems: "flex-start",
              boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#cbd5e1";
              e.currentTarget.style.boxShadow = "0 4px 10px rgba(0,0,0,0.06)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "#e2e8f0";
              e.currentTarget.style.boxShadow = "0 1px 3px rgba(0,0,0,0.03)";
            }}
          >
            {(item.image_url || item.initials) && (
              <div style={{ flexShrink: 0 }}>
                <ImageWithFallback
                  src={item.image_url}
                  initials={item.initials}
                  size={isMobile ? 42 : 46}
                  alt={item.name || ""}
                />
              </div>
            )}
            <div style={{ minWidth: 0, flex: 1 }}>
              <div
                style={{
                  fontWeight: 650,
                  fontSize: 13,
                  color: "#0f172a",
                  lineHeight: 1.35,
                }}
              >
                {parseInline(item.name)}
              </div>
              {item.location && (
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 3,
                    fontSize: 11,
                    color: "#0369a1",
                    background: "#f0f9ff",
                    padding: "1px 6px",
                    borderRadius: 4,
                    marginTop: 3,
                    marginBottom: 3,
                    fontWeight: 500,
                  }}
                >
                  <span>📍</span>
                  <span>{parseInline(item.location)}</span>
                </div>
              )}
              {item.description && (
                <div style={{ fontSize: 11.5, color: "#475569", lineHeight: 1.45, marginTop: 2 }}>
                  {parseInline(item.description)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
