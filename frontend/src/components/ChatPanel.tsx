import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { SessionEvent } from '../types';

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
      {/* Events feed */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
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

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              marginTop: 16,
              padding: 16,
              background: '#1e293b',
              borderRadius: 8,
              border: '1px solid #334155',
              fontSize: 13,
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
              color: '#e2e8f0',
              maxHeight: 400,
              overflow: 'auto',
            }}
          >
            {result}
          </motion.div>
        )}

        <div ref={eventsEndRef} />
      </div>

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
