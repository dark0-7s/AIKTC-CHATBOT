import { useContext } from "react";
import { CHIPS } from "../data/chips";
import { LangContext } from "../context/LangContext";
import { useLabel } from "../utils/labels";

export default function QuickChips({ onChipClick }) {
  const { lang } = useContext(LangContext);
  const chipsTitle = useLabel(lang, "chips_title");

  return (
    <div style={{ marginBottom: 20 }}>
      <p style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>{chipsTitle}</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {CHIPS.map((chip, i) => {
          const chipLabel = chip.label?.[lang] ?? chip.label?.en ?? chip.label;
          return (
            <button
              key={i}
              onClick={() => onChipClick(chip.message)}
              className="chip-btn"
            >
              {chipLabel}
            </button>
          );
        })}
      </div>
    </div>
  );
}
