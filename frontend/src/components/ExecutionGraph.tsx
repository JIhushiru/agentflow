import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AgentNode } from './AgentNode';
import type { GraphNode, GraphEdge } from '../types';

const nodeTypes = { agent: AgentNode };

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function ExecutionGraph({ nodes, edges }: Props) {
  const flowNodes: Node[] = nodes.map((n) => ({
    id: n.id,
    type: n.type,
    position: n.position,
    data: n.data,
  }));

  const flowEdges: Edge[] = edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    animated: e.animated,
    style: { stroke: '#475569', strokeWidth: 2 },
  }));

  if (flowNodes.length === 0) {
    return (
      <div
        style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#64748b',
          fontSize: 14,
        }}
      >
        Submit a goal to see the execution graph
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      fitView
      proOptions={{ hideAttribution: true }}
      style={{ background: '#0f172a' }}
    >
      <Background color="#1e293b" gap={20} />
      <Controls
        style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
      />
    </ReactFlow>
  );
}
