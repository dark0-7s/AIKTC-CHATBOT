import { useLabel } from "../../utils/labels";

export default function ComparisonCards({ data, lang }) {
  const { title, items } = data || {};

  // Pre-fetch all possible label translations at top level (hooks rules compliance)
  const labelFees   = useLabel(lang, "table_fees");
  const labelIntake = useLabel(lang, "table_intake");

  if (!items || !Array.isArray(items)) return null;

  const resolveLabel = (item) => {
    const c = item.label?.toLowerCase()?.trim();
    if (c === "fees" || c === "fee")       return labelFees;
    if (c === "intake" || c === "seats")   return labelIntake;
    // For arbitrary labels pass through unchanged; useLabel returns key if missing
    return item.label;
  };

  return (
    <div style={{ background: "#f8fafc", borderRadius: 16, padding: 12 }}>
      {title && <p style={{ fontWeight: 600, marginBottom: 8 }}>{title}</p>}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
        {items.map((item, i) => {
          if (!item) return null;
          const displayLabel = resolveLabel(item);

          return (
            <div
              key={i}
              style={{
                background: "white",
                borderRadius: 12,
                padding: "10px 16px",
                minWidth: 120,
                textAlign: "center",
                boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
              }}
            >
              <p style={{ fontSize: 12, color: "#475569" }}>{displayLabel}</p>
              <p style={{ fontWeight: 700, fontSize: 16 }}>{item.value ?? "—"}</p>
              {item.sublabel && (
                <p style={{ fontSize: 10, color: "#64748b", marginTop: 4 }}>{item.sublabel}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}