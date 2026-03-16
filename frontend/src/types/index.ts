export type TaskStatus = 'pending' | 'running' | 'complete' | 'failed';
export type AgentType = 'research' | 'code' | 'data' | 'report' | 'critic';

export interface Task {
  id: string;
  description: string;
  agent_type: AgentType;
  dependencies: string[];
  status: TaskStatus;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
}

export interface ExecutionPlan {
  goal: string;
  tasks: Task[];
}

export interface SessionEvent {
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface Session {
  id: string;
  goal: string;
  status: TaskStatus;
  result: string | null;
  plan: ExecutionPlan | null;
  events: SessionEvent[];
}

export interface GraphNode {
  id: string;
  type: string;
  data: {
    label: string;
    agentType: AgentType;
    status: TaskStatus;
    output: Record<string, unknown> | null;
  };
  position: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  animated: boolean;
}
