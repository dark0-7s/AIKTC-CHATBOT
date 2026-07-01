import ImageWithFallback from "./ImageWithFallback";

export default function MediaCard({ data }) {
  const { name, designation, initials, image_url, details } = data || {};
  const showAvatar = !!image_url || !!initials;
  return (
    <div style={{ background: "#f8fafc", borderRadius: 16, padding: 14, display: "flex", gap: 14, alignItems: "center" }}>
      {showAvatar && (
        <ImageWithFallback src={image_url} initials={initials} size={56} alt={name || ""} />
      )}
      <div>
        <p style={{ fontWeight: 700 }}>{name}</p>
        <p style={{ fontSize: 12, color: "#475569", marginBottom: 6 }}>{designation}</p>
        {details?.map((d, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
            <i className={`ti ti-${d.icon}`} style={{ fontSize: 14 }} />
            <span>{d.label}: {d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}