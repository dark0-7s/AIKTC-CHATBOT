-- backend/session/schema.sql
-- SQLite database schema for AIKTC Admission Chatbot

-- Sessions table: stores conversation history and anchor
CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT    PRIMARY KEY,
    history     TEXT    NOT NULL DEFAULT '[]',
    anchor      TEXT    DEFAULT NULL,
    created_at  INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at  INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Queries table: logs every query for analytics
CREATE TABLE IF NOT EXISTS queries (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp             TEXT    DEFAULT (datetime('now')),
    session_id            TEXT,
    message               TEXT,
    response_type         TEXT,
    raw_llm_output        TEXT,
    deterministic_context TEXT,
    topic                 TEXT,
    departments           TEXT
);

-- Feedback table: stores user thumbs up/down
CREATE TABLE IF NOT EXISTS feedback (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp            TEXT    DEFAULT (datetime('now')),
    session_id           TEXT,
    rating               INTEGER CHECK(rating IN (1, -1)),
    comment              TEXT,
    conversation_snippet TEXT
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_queries_response_type
    ON queries(response_type);
CREATE INDEX IF NOT EXISTS idx_queries_session
    ON queries(session_id);
CREATE INDEX IF NOT EXISTS idx_queries_timestamp
    ON queries(timestamp);
CREATE INDEX IF NOT EXISTS idx_queries_topic
    ON queries(topic);
CREATE INDEX IF NOT EXISTS idx_feedback_rating
    ON feedback(rating);
CREATE INDEX IF NOT EXISTS idx_feedback_session
    ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated
    ON sessions(updated_at);
