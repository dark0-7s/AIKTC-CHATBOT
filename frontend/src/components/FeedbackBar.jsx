import { useState } from "react";
import FeedbackDialog from "./FeedbackDialog";

export default function FeedbackBar({
  question,
  answer,
  sessionId,
  chatId,
  messageId,
}) {
  const [submitted, setSubmitted] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
async function sendFeedback(rating, comment = "", reason = "") {
  if (submitted) return;

  try {
    const apiBase = import.meta.env.VITE_API_URL || "";
    const url = apiBase ? `${apiBase}/api/feedback/` : "/api/feedback/";
    const response = await fetch(
      url,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          chat_id: chatId,
          message_id: String(messageId ?? ""),
          question,
          answer,
          rating,
          reason,
          comment,
        }),
      }
    );

    if (!response.ok) {
  const error = await response.json();
  console.error("Feedback API Error:", error);
  throw new Error("Failed to save feedback");
}

    setSubmitted(true);
  } catch (err) {
    console.error("Feedback error:", err);
  }
}

  if (submitted) {
    return (
      <div
        style={{
          fontSize: 12,
          color: "#16a34a",
          marginTop: 8,
        }}
      >
        ✓ Thank you for your feedback!
      </div>
    );
  }

  return (
    <>
      <div
        style={{
          display: "flex",
          gap: 10,
          marginTop: 8,
        }}
      >
        <button
          onClick={() => sendFeedback("helpful")}
          style={{
            border: "1px solid #ddd",
            borderRadius: 20,
            padding: "5px 12px",
            cursor: "pointer",
          }}
        >
          👍 Helpful
        </button>

        <button
         onClick={() => setDialogOpen(true)}
          style={{
            border: "1px solid #ddd",
            borderRadius: 20,
            padding: "5px 12px",
            cursor: "pointer",
          }}
        >
          👎 Not Helpful
        </button>
      </div>

      <FeedbackDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={(reason, comment) => {
    sendFeedback("not_helpful", comment, reason);
    setDialogOpen(false);
}}
      />
    </>
  );
}