// frontend/src/components/renderers/ContactCard.jsx

import React from 'react';

export default function ContactCard({ data }) {
  const { reason, contacts } = data || {};
  if (!contacts || contacts.length === 0) return null;

  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: 14,
        padding: "14px 16px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        margin: "8px 0",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 18 }}>🏛️</span>
        <div style={{ fontWeight: 700, fontSize: 14, color: "#0f172a" }}>
          AIKTC Contact & Admissions Support
        </div>
      </div>

      {reason && (
        <p
          style={{
            fontSize: 12.5,
            color: "#475569",
            lineHeight: 1.5,
            marginBottom: 12,
            padding: "8px 10px",
            background: "#f8fafc",
            borderRadius: 8,
            borderLeft: "3px solid #64748b",
          }}
        >
          {reason}
        </p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {contacts.map((c, i) => (
          <div
            key={i}
            style={{
              padding: "10px 12px",
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: 10,
            }}
          >
            <div style={{ fontWeight: 650, fontSize: 13, color: "#1e293b", marginBottom: 6 }}>
              {c.label}
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {c.phone && (
                <a
                  href={`tel:${c.phone.replace(/[^0-9+]/g, '')}`}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "4px 10px",
                    background: "#ecfdf5",
                    border: "1px solid #a7f3d0",
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    color: "#065f46",
                    textDecoration: "none",
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "#d1fae5"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "#ecfdf5"; }}
                >
                  <span>📞</span>
                  <span>{c.phone}</span>
                </a>
              )}

              {c.email && (
                <a
                  href={`mailto:${c.email}`}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "4px 10px",
                    background: "#eff6ff",
                    border: "1px solid #bfdbfe",
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    color: "#1d4ed8",
                    textDecoration: "none",
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "#dbeafe"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "#eff6ff"; }}
                >
                  <span>✉️</span>
                  <span>{c.email}</span>
                </a>
              )}

              {c.whatsapp && (
                <a
                  href={`https://wa.me/${c.whatsapp.replace(/[^0-9]/g, '')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "4px 10px",
                    background: "#f0fdf4",
                    border: "1px solid #bbf7d0",
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    color: "#15803d",
                    textDecoration: "none",
                  }}
                >
                  <span>📱</span>
                  <span>WhatsApp: {c.whatsapp}</span>
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
