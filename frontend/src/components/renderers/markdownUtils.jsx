// frontend/src/components/renderers/markdownUtils.jsx
import React from 'react';

export function sanitize(text) {
  if (!text) return '';
  return text
    .replace(/\berstwhile\b/gi, 'formerly')
    .replace(/\*/g, '\u200B*\u200B')
    .replace(/\u200B\*\u200B\u200B\*\u200B/g, '**')
    .replace(/\u200B\*\u200B/g, '*');
}

/**
 * Universal inline markdown tokenizer & renderer:
 * Handles images, bold, italics, inline code, and clickable link pills.
 */
export function parseInline(text) {
  if (!text) return '';
  const tokenRegex = /(!\[.*?\]\(.*?\)|\*\*.*?\*\*|\*.*?\*|\[.*?\]\(.*?\)|`.*?`)/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, i) => {
    // 1. Images
    if (part.startsWith('![') && part.includes('](') && part.endsWith(')')) {
      const closingBracketIndex = part.indexOf('](');
      const altText = part.slice(2, closingBracketIndex);
      const url = part.slice(closingBracketIndex + 2, -1);
      return (
        <span key={i} style={{ display: 'block', margin: '10px 0' }}>
          <img
            src={url}
            alt={altText}
            style={{
              maxWidth: '100%',
              maxHeight: 240,
              borderRadius: 12,
              objectFit: 'cover',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              border: '1px solid rgba(0,0,0,0.06)'
            }}
            onError={(e) => { e.currentTarget.style.display = 'none'; }}
          />
          {altText && (
            <span style={{ display: 'block', fontSize: 11, color: '#64748b', marginTop: 4, fontWeight: 500 }}>
              📸 {altText}
            </span>
          )}
        </span>
      );
    }

    // 2. Bold text
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} style={{ fontWeight: 650, color: '#0f172a' }}>
          {part.slice(2, -2)}
        </strong>
      );
    }

    // 3. Italic text
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={i} style={{ fontStyle: 'italic', color: '#475569' }}>{part.slice(1, -1)}</em>;
    }

    // 4. Inline code
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={i}
          style={{
            background: '#f1f5f9',
            padding: '2px 6px',
            borderRadius: 4,
            fontSize: '0.9em',
            fontFamily: 'monospace',
            color: '#0f172a'
          }}
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    // 5. Links (rendered as clean, clickable pills with icon)
    if (part.startsWith('[') && part.includes('](') && part.endsWith(')')) {
      const closingBracketIndex = part.indexOf('](');
      const linkText = part.slice(1, closingBracketIndex);
      const url = part.slice(closingBracketIndex + 2, -1);
      return (
        <a
          key={i}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            padding: '2px 8px',
            margin: '1px 2px',
            background: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: 6,
            color: '#1d4ed8',
            textDecoration: 'none',
            fontWeight: 600,
            fontSize: '0.92em',
            transition: 'all 0.2s ease',
            verticalAlign: 'middle'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#dbeafe';
            e.currentTarget.style.borderColor = '#93c5fd';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#eff6ff';
            e.currentTarget.style.borderColor = '#bfdbfe';
          }}
        >
          <span>{linkText}</span>
          <span style={{ fontSize: '0.85em' }}>↗</span>
        </a>
      );
    }

    return part;
  });
}

export function isTableRow(line) {
  const trimmed = line.trim();
  return trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.length > 2;
}

export function isTableSeparator(line) {
  const trimmed = line.trim();
  return trimmed.startsWith('|') && trimmed.endsWith('|') && /^[\s|:-]+$/.test(trimmed);
}
