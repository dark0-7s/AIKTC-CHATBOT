import UserBubble from "./UserBubble";
import BotMessage from "./BotMessage";
import TypingIndicator from "./TypingIndicator";

export default function MessageList({ messages, loading }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {messages.map((msg, idx) => (
        msg.role === "user" ? (
          <UserBubble key={idx} content={msg.content} />
        ) : (
          <BotMessage key={idx} content={msg.content} functionName={msg.functionName} args={msg.args} />
        )
      ))}
      {loading && <TypingIndicator />}
    </div>
  );
}
