import ResponseRouter from "./ResponseRouter";
import TextBubble from "./renderers/TextBubble";
import { useContext } from "react";
import { LangContext } from "../context/LangContext";

export default function BotMessage({ content, functionName, args }) {
  const { lang } = useContext(LangContext);
  if (functionName) {
    return <ResponseRouter functionName={functionName} args={args} lang={lang} />;
  }
  return <TextBubble data={{ message: content }} lang={lang} />;
}