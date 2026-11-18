import ResponseRouter from "./ResponseRouter";
import TextBubble from "./renderers/TextBubble";
import { useContext, useState, useEffect } from "react";
import { LangContext } from "../context/LangContext";

export default function BotMessage({ content, functionName, args }) {
  const { lang } = useContext(LangContext);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div
      style={{
        alignSelf: "flex-start",
        maxWidth: isMobile ? "96%" : "90%",
        width: "fit-content",
        background: "#ffffff",
        borderRadius: 16,
        padding: isMobile ? 12 : 16,
        boxShadow: "0 2px 10px rgba(0,0,0,.08)",
        marginBottom: 10,
      }}
    >
      {functionName && (
        <ResponseRouter
          functionName={functionName}
          args={args}
          lang={lang}
        />
      )}
      {content && (
        <div style={{ marginTop: functionName ? 12 : 0, paddingTop: functionName ? 10 : 0, borderTop: functionName ? "1px solid #e2e8f0" : "none" }}>
          <TextBubble
            data={{ message: content }}
            lang={lang}
          />
        </div>
      )}
    </div>
  );
}