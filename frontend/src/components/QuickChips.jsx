import { CHIPS } from "../data/chips";

export default function QuickChips({ onChipClick }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <p style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>Try asking</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {CHIPS.map((chip, i) => (
          <button
            key={i}
            onClick={() => onChipClick(chip.message)}
            style={{ background: "#f1f5f9", border: "none", borderRadius: 40, padding: "6px 14px", fontSize: 13, cursor: "pointer" }}
          >
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  );
}