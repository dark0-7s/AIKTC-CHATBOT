import { useState } from 'react';

export default function FeedbackButtons({ sessionId }) {
    const [submitted, setSubmitted] = useState(false);
    const [vote, setVote] = useState(null);

    const handleFeedback = async (rating) => {
        if (submitted) return;
        try {
            await fetch('/api/chat/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    rating: rating,
                })
            });
            setVote(rating);
            setSubmitted(true);
        } catch (e) {
            console.error("Feedback error", e);
        }
    };

    if (submitted) {
        return <div style={{ fontSize: '0.8rem', color: '#666', marginTop: 8 }}>Thank you for your feedback!</div>;
    }

    return (
        <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
            <button
                onClick={() => handleFeedback(1)}
                style={{
                    border: 'none', background: 'none', cursor: 'pointer', fontSize: '1.2rem',
                    color: vote === 1 ? '#22c55e' : '#888', transition: 'color 0.2s'
                }}
                title="Thumbs up"
            >👍</button>
            <button
                onClick={() => handleFeedback(-1)}
                style={{
                    border: 'none', background: 'none', cursor: 'pointer', fontSize: '1.2rem',
                    color: vote === -1 ? '#ef4444' : '#888', transition: 'color 0.2s'
                }}
                title="Thumbs down"
            >👎</button>
        </div>
    );
}
