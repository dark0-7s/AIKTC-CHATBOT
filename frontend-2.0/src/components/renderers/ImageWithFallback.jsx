import { useState } from "react";
import { avatarPalette } from "../../utils/avatarPalette";

export default function ImageWithFallback({ src, initials, size = 44, alt = "" }) {
  const [failed, setFailed] = useState(false);
  const pal = avatarPalette(initials || "??");
  
  if (!src || failed) {
    if (!initials) return null;
    return (
      <div style={{
        width: size, height: size, borderRadius: "50%",
        background: pal.bg, color: pal.color,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontWeight: 500, fontSize: Math.round(size * 0.35),
        flexShrink: 0
      }}>
        {initials.slice(0, 2).toUpperCase()}
      </div>
    );
  }
  
  return (
    <img
      src={src}
      alt={alt}
      style={{ width: size, height: size, borderRadius: "50%", objectFit: "cover", flexShrink: 0 }}
      onError={() => setFailed(true)}
    />
  );
}
