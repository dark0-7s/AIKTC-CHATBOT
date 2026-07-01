import ImageWithFallback from "./ImageWithFallback";
import { parseInline } from "./TextBubble";

export default function ListCards({ data }) {
  const { title, items } = data || {};
  if (!items) return null;
  return (
    <div>
      <p style={{ fontWeight: 600, marginBottom: 8 }}>{parseInline(title)}</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {items.map((item, i) => (
          <div key={i} style={{ display: "flex", gap: 10, background: "#f8fafc", borderRadius: 12, padding: 10 }}>
            {(item.image_url || item.initials) && (
              <ImageWithFallback src={item.image_url} initials={item.initials} size={48} alt={item.name || ""} />
            )}
            <div>
              <p style={{ fontWeight: 600 }}>{parseInline(item.name)}</p>
              <p style={{ fontSize: 12, color: "#475569" }}>{parseInline(item.description)}</p>
              {item.location && <p style={{ fontSize: 11, color: "#64748b" }}>📍 {parseInline(item.location)}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}