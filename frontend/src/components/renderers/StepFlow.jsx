// frontend/src/components/renderers/StepFlow.jsx

import React from 'react';
import { parseInline } from "./markdownUtils";

export default function StepFlow({ data }) {
  const { title, steps } = data || {};
  if (!steps || steps.length === 0) return null;

  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: 14,
        padding: "14px 16px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.03)",
        margin: "8px 0",
      }}
    >
      {title && (
        <div
          style={{
            fontWeight: 700,
            fontSize: 14,
            color: "#0f172a",
            marginBottom: 12,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span>📋</span>
          <span>{parseInline(title)}</span>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", position: "relative" }}>
        {steps.map((step, i) => {
          const isLast = i === steps.length - 1;
          return (
            <div
              key={i}
              style={{
                display: "flex",
                gap: 12,
                position: "relative",
                paddingBottom: isLast ? 0 : 14,
              }}
            >
              {/* Connector Line */}
              {!isLast && (
                <div
                  style={{
                    position: "absolute",
                    left: 13,
                    top: 26,
                    bottom: 0,
                    width: 2,
                    background: "#e2e8f0",
                  }}
                />
              )}

              {/* Number Badge */}
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: "#0284c7",
                  color: "#ffffff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 12.5,
                  fontWeight: 700,
                  flexShrink: 0,
                  zIndex: 1,
                  boxShadow: "0 2px 4px rgba(2, 132, 199, 0.3)",
                }}
              >
                {i + 1}
              </div>

              {/* Content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontWeight: 650,
                    fontSize: 13.5,
                    color: "#0f172a",
                    lineHeight: 1.35,
                    marginBottom: 2,
                  }}
                >
                  {parseInline(step?.title)}
                </div>
                {step?.detail && (
                  <div style={{ fontSize: 12, color: "#475569", lineHeight: 1.5 }}>
                    {parseInline(step.detail)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
