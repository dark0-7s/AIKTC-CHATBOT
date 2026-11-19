import { useState, useEffect } from "react";
export default function UserBubble({ content }) {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);

    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 10 }}>
      <div
        style={{
          maxWidth: isMobile ? "88%" : "75%",
          background: "linear-gradient(135deg, #0f766e 0%, #0d9488 100%)",
          color: "#ffffff",
          borderRadius: "18px 18px 4px 18px",
          padding: "10px 16px",
          fontSize: 14,
          lineHeight: 1.5,
          fontWeight: 500,
          boxShadow: "0 2px 8px rgba(13, 148, 136, 0.25)",
          wordBreak: "break-word",
        }}
      >
        {content}
      </div>
    </div>
  );
}