import { useLabel } from "../../utils/labels";

export default function MultiPredictionCards({ data, lang }) {
  const l = (key) => useLabel(lang, key);
  const { predictions } = data || {};
  if (!predictions) return null;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {predictions?.map((pred, i) => {
        const verdictColor = pred?.verdict === "HIGH" ? "#10b981" : pred?.verdict === "MEDIUM" ? "#f59e0b" : "#ef4444";
        return (
          <div key={i} style={{ background: "#f8fafc", borderRadius: 16, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontWeight: 700 }}>{pred?.dept}</span>
              <span style={{ background: verdictColor, padding: "2px 10px", borderRadius: 40, color: "white", fontSize: 11 }}>
                {pred?.verdict ? l(`verdict_${pred.verdict.toLowerCase()}`) : ""}
              </span>
            </div>
            <p style={{ fontSize: 12, color: "#475569" }}>{pred?.cutoff_range}</p>
            <p style={{ fontSize: 13, marginTop: 6 }}>{pred?.reasoning}</p>
          </div>
        );
      })}
    </div>
  );
}