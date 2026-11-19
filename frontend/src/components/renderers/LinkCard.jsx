// frontend/src/components/renderers/LinkCard.jsx

import React from 'react';

export default function LinkCard({ title, url, icon = "🌐" }) {
  const isTablerIcon = typeof icon === "string" && icon.startsWith("ti-");
  const hasIcon = icon && icon !== "ti-currency-dollar";

  let domain = "";
  try {
    const parsed = new URL(url);
    domain = parsed.hostname.replace(/^www\./, "");
  } catch (e) {
    domain = url ? url.slice(0, 30) : "";
  }

  const isCet = domain.includes("mahacet.org") || domain.includes("dtemaharashtra");
  const badgeBg = isCet ? "#fef3c7" : "#eff6ff";
  const badgeColor = isCet ? "#b45309" : "#1d4ed8";
  const borderColor = isCet ? "#fde68a" : "#bfdbfe";

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 14px",
        marginBottom: 8,
        borderRadius: 12,
        border: "1px solid #e2e8f0",
        borderLeft: `4px solid ${isCet ? '#f59e0b' : '#3b82f6'}`,
        background: "#ffffff",
        textDecoration: "none",
        color: "#0f172a",
        transition: "all .2s cubic-bezier(0.4, 0, 0.2, 1)",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        cursor: "pointer",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "#f8fafc";
        e.currentTarget.style.transform = "translateY(-1px)";
        e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "#ffffff";
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "0 1px 3px rgba(0,0,0,0.04)";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
        {hasIcon && (
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: badgeBg,
              color: badgeColor,
              border: `1px solid ${borderColor}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 18,
              flexShrink: 0,
            }}
          >
            {isTablerIcon ? <i className={`ti ${icon}`} aria-hidden="true" /> : icon}
          </div>
        )}
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontWeight: 650,
              fontSize: 13.5,
              color: "#0f172a",
              lineHeight: 1.35,
              whiteSpace: "normal",
            }}
          >
            {title}
          </div>
          {domain && (
            <div
              style={{
                fontSize: 11,
                color: "#64748b",
                marginTop: 2,
                display: "flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              <span>🔗 {domain}</span>
            </div>
          )}
        </div>
      </div>

      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          background: "#f1f5f9",
          color: "#475569",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 13,
          fontWeight: 700,
          flexShrink: 0,
          marginLeft: 10,
        }}
      >
        ↗
      </div>
    </a>
  );
}
