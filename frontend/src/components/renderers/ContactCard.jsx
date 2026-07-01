export default function ContactCard({ data }) {
  const { reason, contacts } = data || {};
  if (!contacts) return null;
  return (
    <div style={{ background: "#f8fafc", borderRadius: 16, padding: 12 }}>
      {reason && <p style={{ fontSize: 13, marginBottom: 8 }}>{reason}</p>}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {contacts.map((c, i) => (
          <div key={i}>
            <p style={{ fontWeight: 600 }}>{c.label}</p>
            {c.phone && <p style={{ fontSize: 12 }}>📞 {c.phone}</p>}
            {c.email && <p style={{ fontSize: 12 }}>✉️ {c.email}</p>}
            {c.whatsapp && <p style={{ fontSize: 12 }}>📱 {c.whatsapp}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}