import { Handle, Position, type NodeProps } from '@xyflow/react';
import { motion } from 'framer-motion';
import type { TaskStatus, AgentType } from '../types';

interface AgentNodeData {
  label: string;
  agentType: AgentType;
  status: TaskStatus;
  output: Record<string, unknown> | null;
  [key: string]: unknown;
}

const STATUS_COLORS: Record<TaskStatus, string> = {
  pending: '#64748b',
  running: '#3b82f6',
  complete: '#22c55e',
  failed: '#ef4444',
};

const AGENT_ICONS: Record<AgentType, string> = {
  research: '\u{1F50D}',
  code: '\u{1F4BB}',
  data: '\u{1F4CA}',
  report: '\u{1F4DD}',
  critic: '\u{1F9D0}',
};

export function AgentNode({ data }: NodeProps) {
  const nodeData = data as unknown as AgentNodeData;
  const color = STATUS_COLORS[nodeData.status];
  const icon = AGENT_ICONS[nodeData.agentType];

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      style={{
        background: '#1e293b',
        border: `2px solid ${color}`,
        borderRadius: 12,
        padding: '12px 16px',
        minWidth: 180,
        color: '#f8fafc',
        fontSize: 13,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <span
          style={{
            textTransform: 'uppercase',
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: 1,
            color,
          }}
        >
          {nodeData.agentType}
        </span>
        {nodeData.status === 'running' && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
            style={{
              width: 12,
              height: 12,
              border: `2px solid ${color}`,
              borderTopColor: 'transparent',
              borderRadius: '50%',
              marginLeft: 'auto',
            }}
          />
        )}
      </div>

      <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.4 }}>
        {nodeData.label}
      </div>

      <div
        style={{
          marginTop: 8,
          fontSize: 10,
          padding: '2px 8px',
          borderRadius: 99,
          background: `${color}22`,
          color,
          display: 'inline-block',
          fontWeight: 600,
        }}
      >
        {nodeData.status}
      </div>

      <Handle type="source" position={Position.Bottom} style={{ background: color }} />
    </motion.div>
  );
}
