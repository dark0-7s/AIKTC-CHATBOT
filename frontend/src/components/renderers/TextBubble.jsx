// frontend/src/components/renderers/TextBubble.jsx

import React from 'react';

/**
 * Enhanced, Beautiful Markdown Renderer for AIKTC Chatbot.
 * Handles headings (##, ###, ####), markdown tables, nested lists,
 * official link badges, source badges, images, and bold/italic formatting.
 */

function sanitize(text) {
  if (!text) return '';
  return text
    .replace(/\*/g, '\u200B*\u200B')
    .replace(/\u200B\*\u200B\u200B\*\u200B/g, '**')
    .replace(/\u200B\*\u200B/g, '*');
}

// ── Inline parser ─────────────────────────────────────────────────
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

// Helper to check table rows
function isTableRow(line) {
  const trimmed = line.trim();
  return trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.length > 2;
}

function isTableSeparator(line) {
  const trimmed = line.trim();
  return /^\|[-:\s|]+\|$/.test(trimmed);
}

function parseTableCells(line) {
  return line
    .trim()
    .slice(1, -1)
    .split('|')
    .map(c => c.trim());
}

// ── Block renderer ────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return null;
  const safe = sanitize(text);
  const lines = safe.split('\n');
  const elements = [];

  let listBuffer = [];
  let listType = null; // 'ul' or 'ol'
  let tableBuffer = [];

  const flushList = () => {
    if (listBuffer.length === 0) return;
    const Tag = listType === 'ol' ? 'ol' : 'ul';
    elements.push(
      <Tag
        key={`list-${elements.length}`}
        style={{
          paddingLeft: 22,
          margin: '8px 0',
          fontSize: 14,
          lineHeight: 1.75,
          color: '#334155',
        }}
      >
        {listBuffer.map((item, i) => (
          <li key={i} style={{ marginBottom: 4, paddingLeft: 2 }}>
            {parseInline(item)}
          </li>
        ))}
      </Tag>
    );
    listBuffer = [];
    listType = null;
  };

  const flushTable = () => {
    if (tableBuffer.length < 2) {
      // Not a valid table, flush as paragraphs
      tableBuffer.forEach((tblLine, idx) => {
        elements.push(<p key={`tbl-raw-${elements.length}-${idx}`}>{parseInline(tblLine)}</p>);
      });
      tableBuffer = [];
      return;
    }

    const headerCells = parseTableCells(tableBuffer[0]);
    const bodyRows = tableBuffer
      .slice(1)
      .filter(l => !isTableSeparator(l))
      .map(parseTableCells);

    elements.push(
      <div
        key={`table-${elements.length}`}
        style={{
          overflowX: 'auto',
          margin: '12px 0',
          borderRadius: 10,
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 4px rgba(0,0,0,0.03)'
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
              {headerCells.map((h, idx) => (
                <th key={idx} style={{ padding: '9px 12px', fontWeight: 650, color: '#1e293b' }}>
                  {parseInline(h)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bodyRows.map((r, rIdx) => (
              <tr
                key={rIdx}
                style={{
                  background: rIdx % 2 === 0 ? '#ffffff' : '#fcfcfd',
                  borderBottom: rIdx < bodyRows.length - 1 ? '1px solid #f1f5f9' : 'none'
                }}
              >
                {r.map((cell, cIdx) => (
                  <td key={cIdx} style={{ padding: '8px 12px', color: '#334155' }}>
                    {parseInline(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableBuffer = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // 1. Table handling
    if (isTableRow(trimmed)) {
      flushList();
      tableBuffer.push(trimmed);
      continue;
    } else if (tableBuffer.length > 0) {
      flushTable();
    }

    // 2. Empty line
    if (!trimmed) {
      flushList();
      elements.push(<div key={`gap-${i}`} style={{ height: 6 }} />);
      continue;
    }

    // 3. Horizontal Rule
    if (trimmed === '---' || trimmed === '***' || trimmed === '___') {
      flushList();
      elements.push(
        <hr
          key={`hr-${i}`}
          style={{
            border: 'none',
            borderTop: '1px solid #e2e8f0',
            margin: '14px 0'
          }}
        />
      );
      continue;
    }

    // 4. Source citation footer
    if (trimmed.startsWith('*Source:') || trimmed.startsWith('Source:')) {
      flushList();
      const sourceText = trimmed.replace(/\*/g, '').trim();
      elements.push(
        <div
          key={`source-${i}`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '5px 12px',
            background: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: 20,
            fontSize: 11.5,
            fontWeight: 600,
            color: '#166534',
            marginTop: 8
          }}
        >
          <span style={{ fontSize: 13 }}>🛡️</span>
          <span>{sourceText}</span>
        </div>
      );
      continue;
    }

    // 5. Headings
    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <div
          key={`h2-${i}`}
          style={{
            fontWeight: 700,
            fontSize: 15,
            color: '#0f172a',
            margin: '14px 0 6px',
            paddingBottom: 4,
            borderBottom: '1px solid #e2e8f0'
          }}
        >
          {parseInline(trimmed.slice(3))}
        </div>
      );
      continue;
    }

    if (trimmed.startsWith('### ')) {
      flushList();
      const headingContent = trimmed.slice(4);
      const isOfficialPortal = headingContent.includes('Official') || headingContent.includes('🌐');

      elements.push(
        <div
          key={`h3-${i}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontWeight: 650,
            fontSize: 14.5,
            color: isOfficialPortal ? '#1e40af' : '#0f172a',
            background: isOfficialPortal ? '#eff6ff' : '#f8fafc',
            borderLeft: `4px solid ${isOfficialPortal ? '#3b82f6' : '#0284c7'}`,
            padding: '6px 12px',
            borderRadius: '0 8px 8px 0',
            margin: '14px 0 8px'
          }}
        >
          {parseInline(headingContent)}
        </div>
      );
      continue;
    }

    if (trimmed.startsWith('#### ')) {
      flushList();
      elements.push(
        <div
          key={`h4-${i}`}
          style={{
            fontWeight: 650,
            fontSize: 13.5,
            color: '#1e293b',
            margin: '10px 0 4px',
            paddingLeft: 2
          }}
        >
          {parseInline(trimmed.slice(5))}
        </div>
      );
      continue;
    }

    // 6. Unordered list (- or * or •)
    if (/^[-*•]\s+/.test(trimmed)) {
      if (listType === 'ol') flushList();
      listType = 'ul';
      listBuffer.push(trimmed.replace(/^[-*•]\s+/, ''));
      continue;
    }

    // 7. Ordered list (1. or 2.)
    if (/^\d+\.\s+/.test(trimmed)) {
      if (listType === 'ul') flushList();
      listType = 'ol';
      listBuffer.push(trimmed.replace(/^\d+\.\s+/, ''));
      continue;
    }

    // 8. Normal Paragraph
    flushList();
    elements.push(
      <p
        key={`p-${i}`}
        style={{
          fontSize: 14,
          lineHeight: 1.7,
          color: '#1e293b',
          margin: '0 0 6px'
        }}
      >
        {parseInline(trimmed)}
      </p>
    );
  }

  flushList();
  if (tableBuffer.length > 0) {
    flushTable();
  }

  return elements;
}

// ── Component ─────────────────────────────────────────────────────
export default function TextBubble({ data }) {
  const message = data?.message ?? '—';
  return (
    <div style={{ minWidth: 0, wordBreak: 'break-word', color: '#1e293b' }}>
      {renderMarkdown(message)}
    </div>
  );
}
