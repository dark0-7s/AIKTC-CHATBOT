import { useCallback } from "react";
import { useLabel } from "../../utils/labels";

export default function TableResponse({ data, lang }) {
  const { title, columns, rows } = data || {};

  // All labels pre-fetched at component top level — no hooks inside callbacks
  const labelYear   = useLabel(lang, "table_year");
  const labelOpen   = useLabel(lang, "table_open");
  const labelOBC    = useLabel(lang, "table_obc");
  const labelSC     = useLabel(lang, "table_sc");
  const labelST     = useLabel(lang, "table_st");
  const labelEWS    = useLabel(lang, "table_ews");
  const labelTFWS   = useLabel(lang, "table_tfws");
  const labelIntake = useLabel(lang, "table_intake");
  const labelFees   = useLabel(lang, "table_fees");
  const labelNoResults = useLabel(lang, "no_results");

  const translateHeader = useCallback(
    (col) => {
      const c = col?.toLowerCase()?.trim();
      if (c === "year")                                      return labelYear;
      if (c === "open")                                      return labelOpen;
      if (c === "obc")                                       return labelOBC;
      if (c === "sc")                                        return labelSC;
      if (c === "st")                                        return labelST;
      if (c === "ews")                                       return labelEWS;
      if (c === "tfws")                                      return labelTFWS;
      if (c === "intake")                                    return labelIntake;
      if (c === "fees/year" || c === "fees" || c === "fee") return labelFees;
      return col;
    },
    [labelYear, labelOpen, labelOBC, labelSC, labelST, labelEWS, labelTFWS, labelIntake, labelFees]
  );

  if (!columns || !rows) {
    return (
      <div style={{ fontSize: 13, color: "#64748b", padding: 8 }}>
        {labelNoResults}
      </div>
    );
  }

  return (
    <div style={{ marginBottom: 12 }}>
      {title && <p style={{ fontWeight: 600, marginBottom: 8 }}>{title}</p>}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", tableLayout: "fixed", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
              {columns.map((col, i) => (
                <th key={i} style={{ padding: 8, textAlign: "left" }}>{translateHeader(col)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #f1f5f9" }}>
                {row?.map((cell, j) => (
                  <td key={j} style={{ padding: 8, wordBreak: "break-word" }}>{cell ?? "—"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}