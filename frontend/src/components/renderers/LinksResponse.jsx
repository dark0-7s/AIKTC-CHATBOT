// frontend/src/components/renderers/LinksResponse.jsx

import React from 'react';
import LinkCard from "./LinkCard";

export default function LinksResponse({ data }) {
  if (!data || !data.links || data.links.length === 0) return null;

  return (
    <div style={{ margin: "8px 0" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 10,
          padding: "6px 10px",
          background: "#eff6ff",
          borderRadius: 8,
          borderLeft: "4px solid #2563eb",
        }}
      >
        <span style={{ fontSize: 16 }}>🌐</span>
        <div style={{ fontWeight: 700, fontSize: 13.5, color: "#1e40af" }}>
          {data.title || "Official Portals & Navigation"}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {data.links.map((link, i) => (
          <LinkCard
            key={i}
            title={link.title}
            url={link.url}
            icon={link.icon}
          />
        ))}
      </div>
    </div>
  );
}
