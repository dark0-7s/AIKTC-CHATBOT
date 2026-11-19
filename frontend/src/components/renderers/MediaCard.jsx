// frontend/src/components/renderers/MediaCard.jsx

import React from 'react';
import ImageWithFallback from "./ImageWithFallback";

export default function MediaCard({ data }) {
  const { name, designation, initials, image_url, details } = data || {};
  const showAvatar = !!image_url || !!initials;

  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: 14,
        padding: "12px 14px",
        display: "flex",
        gap: 12,
        alignItems: "center",
        boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
        transition: "all 0.2s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "#cbd5e1";
        e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.06)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "#e2e8f0";
        e.currentTarget.style.boxShadow = "0 1px 4px rgba(0,0,0,0.04)";
      }}
    >
      {showAvatar && (
        <div style={{ flexShrink: 0 }}>
          <ImageWithFallback
            src={image_url}
            initials={initials}
            size={52}
            alt={name || ""}
          />
        </div>
      )}
      <div style={{ minWidth: 0, flex: 1 }}>
        <div
          style={{
            fontWeight: 700,
            fontSize: 13.5,
            color: "#0f172a",
            lineHeight: 1.3,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {name}
        </div>
        <div
          style={{
            fontSize: 11.5,
            fontWeight: 500,
            color: "#0369a1",
            marginTop: 2,
            marginBottom: details && details.length > 0 ? 6 : 0,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {designation}
        </div>
        {details?.map((d, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 5,
              fontSize: 11.5,
              color: "#475569",
              marginTop: 2,
            }}
          >
            <span style={{ fontSize: 12 }}>🔹</span>
            <span style={{ fontWeight: 500 }}>{d.label}:</span>
            <span style={{ color: "#1e293b" }}>{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
