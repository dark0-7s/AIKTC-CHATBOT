import ResponseRouter from "./ResponseRouter";
import TextBubble from "./renderers/TextBubble";
import { useContext } from "react";
import { LangContext } from "../context/LangContext";
import FeedbackButtons from "./FeedbackButtons";
import { getSessionId } from "../utils/sessionId";

export default function BotMessage({ content, functionName, args }) {
  const { lang } = useContext(LangContext);
  const sessionId = getSessionId();

  let renderedContent;
  if (functionName) {
    renderedContent = <ResponseRouter functionName={functionName} args={args} lang={lang} />;
  } else {
    renderedContent = <TextBubble data={{ message: content }} lang={lang} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
        {renderedContent}
        <FeedbackButtons sessionId={sessionId} />
    </div>
  );
}
