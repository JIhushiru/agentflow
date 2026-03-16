import { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { SessionEvent } from '../types';

/** Lightweight markdown-to-JSX renderer for result display. */
function renderMarkdown(text: string): React.ReactNode[] {
  const sections = text.split(/\n---\n/).map((s) => s.trim()).filter(Boolean);

  return sections.map((section, si) => {
    const lines = section.split('\n');
    const elements: React.ReactNode[] = [];
    let heading = '';

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // ## Heading
      const headingMatch = line.match(/^##\s+(.+)/);
      if (headingMatch) {
        heading = headingMatch[1];
        elements.push(
          <h3 key={`h-${si}-${i}`} style={{ color: '#f8fafc', fontSize: 15, fontWeight: 600, margin: '0 0 8px' }}>
            {heading}
          </h3>
        );
        continue;
      }

      // Numbered list item (e.g. "1. Title - Description")
      const listMatch = line.match(/^(\d+)\.\s+(.+)/);
      if (listMatch) {
        elements.push(
          <div key={`li-${si}-${i}`} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
            <span style={{ color: '#3b82f6', fontWeight: 600, flexShrink: 0 }}>{listMatch[1]}.</span>
            <span style={{ color: '#cbd5e1' }}>{renderInline(listMatch[2])}</span>
          </div>
        );
        continue;
      }

      // Blank line
      if (!line.trim()) continue;

      // Regular paragraph
      elements.push(
        <p key={`p-${si}-${i}`} style={{ color: '#cbd5e1', margin: '0 0 6px' }}>
          {renderInline(line)}
        </p>
      );
    }

    return (
      <div
        key={`section-${si}`}
        style={{
          padding: 14,
          background: '#1e293b',
          borderRadius: 8,
          border: '1px solid #334155',
          marginBottom: si < sections.length - 1 ? 10 : 0,
        }}
      >
        {elements}
      </div>
    );
  });
}

/** Render inline markdown: bold, links, and URLs. */
function renderInline(text: string): React.ReactNode[] {
  // Match **bold**, [text](url), or bare URLs
  const parts = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)|https?:\/\/[^\s),]+)/g);
  return parts.map((part, i) => {
    // Bold
    const boldMatch = part.match(/^\*\*(.+)\*\*$/);
    if (boldMatch) {
      return <strong key={i} style={{ color: '#f8fafc', fontWeight: 600 }}>{boldMatch[1]}</strong>;
    }
    // Markdown link
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      return (
        <a key={i} href={linkMatch[2]} target="_blank" rel="noopener noreferrer"
          style={{ color: '#60a5fa', textDecoration: 'underline', textUnderlineOffset: 2 }}>
          {linkMatch[1]}
        </a>
      );
    }
    // Bare URL
    if (/^https?:\/\//.test(part)) {
      return (
        <a key={i} href={part} target="_blank" rel="noopener noreferrer"
          style={{ color: '#60a5fa', textDecoration: 'underline', textUnderlineOffset: 2 }}>
          {part}
        </a>
      );
    }
    return part;
  });
}

interface Props {
  events: SessionEvent[];
  isLoading: boolean;
  result: string | null;
  onSubmit: (goal: string) => void;
}

const EVENT_LABELS: Record<string, string> = {
  session_started: 'Session started',
  planning_started: 'Planning task decomposition...',
  planning_complete: 'Plan ready',
  task_started: 'Task started',
  agent_thinking: 'Agent thinking',
  task_complete: 'Task completed',
  task_failed: 'Task failed',
  session_complete: 'All tasks complete',
  session_failed: 'Session failed',
};

function EventItem({ event }: { event: SessionEvent }) {
  const label = EVENT_LABELS[event.event_type] ?? event.event_type;
  const isError = event.event_type.includes('failed');
  const isComplete = event.event_type.includes('complete');

  let detail = '';
  if (event.data.description) detail = String(event.data.description);
  else if (event.data.agent) detail = String(event.data.agent);
  else if (event.data.error) detail = String(event.data.error);
  else if (event.data.num_tasks) detail = `${event.data.num_tasks} tasks`;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      style={{
        padding: '8px 12px',
        borderLeft: `3px solid ${isError ? '#ef4444' : isComplete ? '#22c55e' : '#3b82f6'}`,
        background: '#1e293b',
        borderRadius: '0 6px 6px 0',
        fontSize: 13,
      }}
    >
      <div style={{ color: isError ? '#ef4444' : '#f8fafc', fontWeight: 500 }}>
        {label}
      </div>
      {detail && (
        <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 2 }}>{detail}</div>
      )}
    </motion.div>
  );
}

export function ChatPanel({ events, isLoading, result, onSubmit }: Props) {
  const [input, setInput] = useState('');
  const eventsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSubmit(input.trim());
    setInput('');
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#0f172a',
      }}
    >
      {/* Events feed — compact, scrollable */}
      <div style={{
        maxHeight: result ? 120 : undefined,
        flex: result ? '0 0 auto' : 1,
        overflow: 'auto',
        padding: '12px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        borderBottom: result ? '1px solid #334155' : undefined,
      }}>
        <AnimatePresence>
          {events.map((event, i) => (
            <EventItem key={i} event={event} />
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            style={{ color: '#3b82f6', fontSize: 13, padding: '8px 12px' }}
          >
            Processing...
          </motion.div>
        )}

        <div ref={eventsEndRef} />
      </div>

      {/* Results — takes remaining space */}
      {result && result.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            flex: 1,
            overflow: 'auto',
            padding: 16,
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          <div style={{ marginBottom: 10, color: '#22c55e', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
            Results
          </div>
          {renderMarkdown(result)}
        </motion.div>
      )}

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        style={{
          padding: 16,
          borderTop: '1px solid #1e293b',
          display: 'flex',
          gap: 8,
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter a goal... e.g. 'Research the top AI startups of 2026'"
          disabled={isLoading}
          style={{
            flex: 1,
            padding: '10px 14px',
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 8,
            color: '#f8fafc',
            fontSize: 14,
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          style={{
            padding: '10px 20px',
            background: isLoading ? '#334155' : '#3b82f6',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 600,
            cursor: isLoading ? 'not-allowed' : 'pointer',
          }}
        >
          {isLoading ? 'Running...' : 'Go'}
        </button>
      </form>
    </div>
  );
}
