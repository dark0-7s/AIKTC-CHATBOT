import ImageWithFallback from "./ImageWithFallback";

export default function MediaCard({ data }) {
  const { name, designation, initials, image_url, profile_url, details } = data || {};
  const showAvatar = !!image_url || !!initials;
  return (
    <div style={{ background: "#f8fafc", borderRadius: 16, padding: 14, display: "flex", gap: 14, alignItems: "center", width: "100%", boxSizing: "border-box" }}>
      {showAvatar && (
        <ImageWithFallback src={image_url} initials={initials} size={56} alt={name || ""} />
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontWeight: 700, margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{name}</p>
        <p style={{ fontSize: 12, color: "#475569", marginBottom: 6, marginTop: 2 }}>{designation}</p>
        {details?.map((d, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, marginTop: 2 }}>
            <i className={`ti ti-${d.icon}`} style={{ fontSize: 14 }} />
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{d.label}: {d.value}</span>
          </div>
        ))}
        {profile_url && (
          <div style={{ marginTop: 6 }}>
            <a
              href={profile_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                fontSize: 11,
                color: "var(--color-primary)",
                textDecoration: "none",
                fontWeight: 600
              }}
            >
              View Profile <i className="ti ti-external-link" style={{ fontSize: 11 }} />
            </a>
          </div>
        )}
      </div>
    </div>
  );
}