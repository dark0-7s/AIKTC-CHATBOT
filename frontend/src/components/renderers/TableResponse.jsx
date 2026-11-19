// frontend/src/components/renderers/TableResponse.jsx

import React, { useCallback } from "react";
import { useLabel } from "../../utils/labels";
import { parseInline } from "./markdownUtils";

export default function TableResponse({ data, lang }) {
  const { title, columns, rows } = data || {};

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

  if (!columns || !rows || rows.length === 0) {
    return (
      <div style={{ fontSize: 13, color: "#64748b", padding: 8 }}>
        {labelNoResults}
      </div>
    );
  }

  return (
    <div style={{ margin: "10px 0" }}>
      {title && (
        <div style={{ fontWeight: 700, fontSize: 14, color: "#0f172a", marginBottom: 8 }}>
          {parseInline(title)}
        </div>
      )}

      <div
        style={{
          overflowX: "auto",
          WebkitOverflowScrolling: "touch",
          borderRadius: 10,
          border: "1px solid #e2e8f0",
          boxShadow: "0 1px 4px rgba(0,0,0,0.03)",
        }}
      >
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: 12.5,
            textAlign: "left",
          }}
        >
          <thead>
            <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0" }}>
              {columns.map((col, i) => (
                <th
                  key={i}
                  style={{
                    padding: "9px 12px",
                    fontWeight: 650,
                    color: "#334155",
                    whiteSpace: "nowrap",
                  }}
                >
                  {translateHeader(col)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                style={{
                  background: i % 2 === 0 ? "#ffffff" : "#fcfcfd",
                  borderBottom: i < rows.length - 1 ? "1px solid #f1f5f9" : "none",
                }}
              >
                {row?.map((cell, j) => (
                  <td
                    key={j}
                    style={{
                      padding: "8px 12px",
                      color: "#1e293b",
                      whiteSpace: "nowrap",
                      fontWeight: j === 0 ? 600 : 400,
                    }}
                  >
                    {cell ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
