import { useCallback, useRef, useState } from 'react';
import type { Session, SessionEvent, GraphNode, GraphEdge } from '../types';

const API_BASE = '/api';

export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const createSession = useCallback(async (goal: string) => {
    setIsLoading(true);
    setEvents([]);
    setNodes([]);
    setEdges([]);

    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal }),
    });
    const data: Session = await res.json();
    setSession(data);

    // Connect WebSocket for real-time updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/sessions/${data.id}`);
    wsRef.current = ws;

    ws.onmessage = (msg) => {
      const event: SessionEvent = JSON.parse(msg.data);
      setEvents((prev) => [...prev, event]);

      // Update session status based on events
      if (event.event_type === 'session_complete') {
        setSession((prev) =>
          prev ? { ...prev, status: 'complete', result: String(event.data.result_preview ?? '') } : prev
        );
        setIsLoading(false);
      } else if (event.event_type === 'session_failed') {
        setSession((prev) => (prev ? { ...prev, status: 'failed' } : prev));
        setIsLoading(false);
      } else if (event.event_type === 'planning_complete') {
        // Fetch the graph
        fetchGraph(data.id);
      } else if (
        event.event_type === 'task_started' ||
        event.event_type === 'task_complete' ||
        event.event_type === 'task_failed'
      ) {
        // Refresh graph to update node statuses
        fetchGraph(data.id);
      }
    };

    ws.onerror = () => setIsLoading(false);
    ws.onclose = () => setIsLoading(false);
  }, []);

  const fetchGraph = useCallback(async (sessionId: string) => {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/graph`);
    const data = await res.json();
    setNodes(data.nodes);
    setEdges(data.edges);
  }, []);

  const fetchResult = useCallback(async (sessionId: string) => {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
    const data: Session = await res.json();
    setSession(data);
    return data;
  }, []);

  return {
    session,
    events,
    nodes,
    edges,
    isLoading,
    createSession,
    fetchResult,
  };
}
