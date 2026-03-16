import { ExecutionGraph } from './components/ExecutionGraph';
import { ChatPanel } from './components/ChatPanel';
import { SessionHistory } from './components/SessionHistory';
import { useSession } from './hooks/useSession';

function App() {
  const { session, events, nodes, edges, isLoading, createSession, fetchResult } =
    useSession();

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <div
        style={{
          width: 240,
          background: '#1e293b',
          borderRight: '1px solid #334155',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: '16px 16px 12px',
            borderBottom: '1px solid #334155',
            fontSize: 16,
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span style={{ fontSize: 20 }}>{'\u26A1'}</span>
          AgentFlow
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          <SessionHistory
            currentId={session?.id ?? null}
            onSelect={async (id) => {
              await fetchResult(id);
            }}
          />
        </div>
      </div>

      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Graph */}
        <div
          style={{
            flex: 1,
            borderBottom: '1px solid #334155',
            minHeight: 0,
          }}
        >
          <ExecutionGraph nodes={nodes} edges={edges} />
        </div>

        {/* Chat / Events panel */}
        <div style={{ height: 320, flexShrink: 0 }}>
          <ChatPanel
            events={events}
            isLoading={isLoading}
            result={session?.result ?? null}
            onSubmit={createSession}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
