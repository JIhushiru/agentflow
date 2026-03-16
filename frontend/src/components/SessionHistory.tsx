import { useEffect, useState } from 'react';
import type { Session } from '../types';

interface Props {
  currentId: string | null;
  onSelect: (id: string) => void;
}

const STATUS_DOT: Record<string, string> = {
  pending: '#64748b',
  running: '#3b82f6',
  complete: '#22c55e',
  failed: '#ef4444',
};

export function SessionHistory({ currentId, onSelect }: Props) {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    fetch('/api/sessions')
      .then((r) => r.json())
      .then(setSessions)
      .catch(() => {});
  }, [currentId]);

  if (sessions.length === 0) return null;

  return (
    <div style={{ padding: 12 }}>
      <div
        style={{
          fontSize: 11,
          textTransform: 'uppercase',
          fontWeight: 700,
          letterSpacing: 1,
          color: '#64748b',
          marginBottom: 8,
        }}
      >
        History
      </div>
      {sessions.map((s) => (
        <button
          key={s.id}
          onClick={() => onSelect(s.id)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            width: '100%',
            padding: '8px 10px',
            background: s.id === currentId ? '#334155' : 'transparent',
            border: 'none',
            borderRadius: 6,
            color: '#e2e8f0',
            fontSize: 12,
            cursor: 'pointer',
            textAlign: 'left',
            marginBottom: 2,
          }}
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: STATUS_DOT[s.status] ?? '#64748b',
              flexShrink: 0,
            }}
          />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {s.goal}
          </span>
        </button>
      ))}
    </div>
  );
}
