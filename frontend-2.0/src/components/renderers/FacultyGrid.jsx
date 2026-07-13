import MediaCard from "./MediaCard";

export default function FacultyGrid({ data }) {
  const { department, source_url, members } = data || {};
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <p style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--color-text-primary)", margin: 0 }}>
          {department} Faculty
        </p>
      </div>
      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
        {members?.map((m, i) => {
          const cardData = {
            name: m.name,
            designation: m.designation,
            initials: m.initials,
            image_url: m.image_url,
            profile_url: m.profile_url,
            details: [
              m.specialization && { icon: "school", label: "Qual.", value: m.specialization },
              m.experience && { icon: "briefcase", label: "Exp.", value: m.experience }
            ].filter(Boolean)
          };
          return <MediaCard key={i} data={cardData} />;
        })}
      </div>
      {source_url && (
        <a 
          href={source_url} 
          target="_blank" 
          rel="noreferrer" 
          style={{ 
            display: "inline-flex", 
            alignItems: "center", 
            gap: 6,
            marginTop: 12,
            padding: "8px 16px",
            backgroundColor: "var(--color-primary)",
            color: "white",
            textDecoration: "none",
            borderRadius: 6,
            fontWeight: 500,
            fontSize: 14
          }}
        >
          View Full Faculty Details <i className="ti ti-external-link" />
        </a>
      )}
    </div>
  );
}
