export default function UserBubble({ content }) {
  return (
    <div style={{ display: "flex", justifyContent: "flex-end" }}>
      <div style={{ maxWidth: "80%", background: "#0F6E56", color: "white", borderRadius: "18px 18px 4px 18px", padding: "10px 14px", fontSize: 14 }}>
        {content}
      </div>
    </div>
  );
}