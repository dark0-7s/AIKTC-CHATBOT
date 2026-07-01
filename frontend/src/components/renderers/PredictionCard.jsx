import { useLabel } from "../../utils/labels";

export default function PredictionCard({ data, lang }) {
  const l = (key) => useLabel(lang, key);
  const { dept, percentile, category, verdict, reasoning, alternatives } = data || {};
  const verdictColor = verdict === "HIGH" ? "#10b981" : verdict === "MEDIUM" ? "#f59e0b" : "#ef4444";
  return (
    <div style={{ background: "#f8fafc", borderRadius: 16, padding: 14, marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <span style={{ fontWeight: 700 }}>{dept}</span>
        <span style={{ background: verdictColor, padding: "2px 10px", borderRadius: 40, color: "white", fontSize: 12 }}>{verdict ? l(`verdict_${verdict.toLowerCase()}`) : ""}</span>
      </div>
      <p style={{ fontSize: 13, color: "#475569", marginBottom: 6 }}>{l("percentile_label")}: {percentile}</p>
      <p style={{ fontSize: 13, marginBottom: 8 }}>{reasoning}</p>
      {alternatives?.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <p style={{ fontSize: 12, fontWeight: 600 }}>{l("alternatives_label")}</p>
          <ul style={{ marginTop: 4, paddingLeft: 20 }}>
            {alternatives?.map((alt, i) => (
              <li key={i} style={{ fontSize: 12 }}>
                {alt?.dept} ({alt?.verdict ? l(`verdict_${alt.verdict.toLowerCase()}`) : ""})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}