import { parseInline } from "./TextBubble";

export default function StepFlow({ data }) {
  const { title, steps } = data || {};
  if (!steps) return null;
  return (
    <div style={{ background: "#f8fafc", borderRadius: 16, padding: 12 }}>
      <p style={{ fontWeight: 600, marginBottom: 8 }}>{parseInline(title)}</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {steps?.map((step, i) => (
          <div key={i} style={{ display: "flex", gap: 10 }}>
            <div style={{ width: 24, height: 24, background: "#0F6E56", color: "white", borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 600 }}>{i+1}</div>
            <div>
              <p style={{ fontWeight: 600, fontSize: 13 }}>{parseInline(step?.title)}</p>
              <p style={{ fontSize: 12, color: "#475569" }}>{parseInline(step?.detail)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}