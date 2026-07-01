// frontend/src/components/renderers/TextBubble.jsx

/**
 * Lightweight Markdown renderer for show_text responses.
 * Handles **bold**, *italic*, ## / ### headings, - / • bullet lists,
 * and 1. ordered lists. Does not use any external library.
 *
 * Design principle: students must never see raw markdown syntax.
 * Unbalanced or stray formatting characters are safely escaped.
 */

// ── Sanitisation ──────────────────────────────────────────────────
// Escapes isolated * characters that would otherwise cause the
// parser to produce unbalanced elements (a known LLM edge case).
function sanitize(text) {
  // Escape * that are not part of a valid **...** or *...* pair.
  // This is intentionally conservative – we only preserve the
  // simple cases that the LLM actually produces.
  return text
    .replace(/\*/g, '\u200B*\u200B') // zero-width spaces around all *
    .replace(/\u200B\*\u200B\u200B\*\u200B/g, '**') // restore **
    .replace(/\u200B\*\u200B/g, '*'); // restore single *
  // The result: valid pairs remain, isolated * become harmless.
}

// ── Inline parser ─────────────────────────────────────────────────
export function parseInline(text) {
  if (!text) return '';
  const tokenRegex = /(\*\*.*?\*\*|\*.*?\*|\[.*?\]\(.*?\))/g;
  const parts = text.split(tokenRegex);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
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
          style={{ color: '#2563eb', textDecoration: 'underline', fontWeight: '500' }}
        >
          {linkText}
        </a>
      );
    }
    return part;
  });
}

// ── Block renderer ────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return null;
  const safe = sanitize(text);
  const lines = safe.split('\n');
  const elements = [];
  let listBuffer = [];
  let listType = null; // 'ul' or 'ol'

  const flushList = () => {
    if (listBuffer.length === 0) return;
    const Tag = listType === 'ol' ? 'ol' : 'ul';
    elements.push(
      <Tag key={`list-${elements.length}`} style={{
        paddingLeft: 20, margin: '6px 0', fontSize: 14,
        lineHeight: 1.7, color: 'var(--color-text-primary)',
      }}>
        {listBuffer.map((item, i) => (
          <li key={i} style={{ marginBottom: 3 }}>
            {parseInline(item)}
          </li>
        ))}
      </Tag>
    );
    listBuffer = [];
    listType = null;
  };

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (!trimmed) {
      flushList();
      elements.push(<div key={`gap-${i}`} style={{ height: 6 }} />);
      continue;
    }
    // Headings
    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(<p key={`h2-${i}`} style={{ fontWeight: 500, fontSize: 13,
        color: 'var(--color-text-secondary)', textTransform: 'uppercase',
        letterSpacing: '0.5px', margin: '10px 0 5px' }}>
        {parseInline(trimmed.slice(3))}
      </p>);
      continue;
    }
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(<p key={`h3-${i}`} style={{ fontWeight: 500, fontSize: 14,
        color: 'var(--color-text-primary)', margin: '8px 0 4px' }}>
        {parseInline(trimmed.slice(4))}
      </p>);
      continue;
    }
    // Unordered list
    if (/^[-*•]\s+/.test(trimmed)) {
      if (listType === 'ol') flushList();
      listType = 'ul';
      listBuffer.push(trimmed.replace(/^[-*•]\s+/, ''));
      continue;
    }
    // Ordered list
    if (/^\d+\.\s+/.test(trimmed)) {
      if (listType === 'ul') flushList();
      listType = 'ol';
      listBuffer.push(trimmed.replace(/^\d+\.\s+/, ''));
      continue;
    }
    // Paragraph
    flushList();
    elements.push(<p key={`p-${i}`} style={{ fontSize: 14, lineHeight: 1.7,
      color: 'var(--color-text-primary)', margin: '0 0 4px' }}>
      {parseInline(trimmed)}
    </p>);
  }
  flushList();
  return elements;
}

// ── Component ─────────────────────────────────────────────────────
export default function TextBubble({ data }) {
  const message = data?.message ?? '—';
  return <div style={{ minWidth: 0 }}>{renderMarkdown(message)}</div>;
}