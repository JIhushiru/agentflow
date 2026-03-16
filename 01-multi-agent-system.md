# Project 1: Real-Time Multi-Agent Orchestration Platform

## Overview
A platform where specialized AI agents collaborate to solve complex tasks — research, code generation, data analysis, and reporting. Users submit a high-level goal, and the system decomposes it into subtasks, delegates to specialist agents, and synthesizes results. A live execution graph shows agent activity in real time.

---

## Why This Is Impressive
- Agentic AI is the most in-demand skillset in 2025-2026
- Demonstrates orchestration, state management, error recovery, and production AI patterns
- Shows systems thinking — not just "call an API," but managing complex workflows
- Directly relevant to roles at Anthropic, OpenAI, Google DeepMind, and AI-native startups

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI |
| AI/LLM | Claude API (Anthropic SDK), OpenAI API (fallback) |
| Agent Framework | Custom (or LangGraph for comparison) |
| Task Queue | Redis + Celery (or Python asyncio for simpler version) |
| Real-time Comms | WebSockets (FastAPI WebSocket support) |
| Frontend | React 18 + TypeScript, Tailwind CSS |
| Visualization | React Flow (for execution graph), Framer Motion |
| Database | PostgreSQL (task history, logs) |
| Observability | Structured logging with Loguru, optional OpenTelemetry |
| Deployment | Docker Compose, Railway or Fly.io |

---

## Architecture

```
User Request
    │
    ▼
┌──────────────┐
│  Orchestrator │  ← Decomposes goal into subtasks
│  (Planner)    │  ← Assigns agents, manages dependencies
└──────┬───────┘
       │
  ┌────┼────┬────────┐
  ▼    ▼    ▼        ▼
┌────┐┌────┐┌──────┐┌────────┐
│Res.││Code││Data  ││Report  │  ← Specialist Agents
│Agt ││Agt ││Agt   ││Agt     │
└─┬──┘└─┬──┘└──┬───┘└───┬────┘
  │     │      │        │
  ▼     ▼      ▼        ▼
┌─────────────────────────────┐
│     Tool Registry           │  ← Web search, code exec, file I/O, DB query
└─────────────────────────────┘
       │
       ▼
┌──────────────┐
│  Synthesizer │  ← Combines agent outputs into final result
└──────────────┘
       │
       ▼
  User Response + Execution Graph (via WebSocket)
```

---

## Core Components

### 1. Orchestrator / Planner Agent
- Receives user goal as natural language
- Uses an LLM to decompose into a DAG (Directed Acyclic Graph) of subtasks
- Each subtask has: description, assigned agent type, dependencies, expected output format
- Manages execution order based on dependency resolution

**Key file:** `backend/orchestrator/planner.py`

### 2. Specialist Agents
Each agent is a class that:
- Has a system prompt defining its role and capabilities
- Has access to specific tools
- Returns structured output (Pydantic models)

**Agents to build:**

| Agent | Role | Tools |
|-------|------|-------|
| ResearchAgent | Web research, summarization | Web search API, URL fetcher |
| CodeAgent | Write, review, debug code | Code sandbox (E2B or local Docker) |
| DataAgent | Analyze data, generate charts | Python exec, pandas, matplotlib |
| ReportAgent | Synthesize findings into reports | Markdown generator, PDF export |
| CriticAgent | Review other agents' outputs | None (LLM-only) |

**Key file:** `backend/agents/base.py`, `backend/agents/research.py`, etc.

### 3. Tool Registry
- Central registry of tools agents can invoke
- Each tool is a callable with a JSON schema description
- Tools: `web_search`, `fetch_url`, `execute_python`, `read_file`, `write_file`, `query_database`
- Uses Claude's native tool_use feature for structured invocation

**Key file:** `backend/tools/registry.py`, `backend/tools/web_search.py`, etc.

### 4. Execution Engine
- Runs the task DAG with proper dependency resolution
- Handles parallel execution of independent subtasks
- Implements retry logic with exponential backoff
- Streams status updates via WebSocket

**Key file:** `backend/engine/executor.py`

### 5. State Manager
- Tracks: task status, agent outputs, execution history, errors
- Persists to PostgreSQL for history/replay
- In-memory state via Redis for active sessions

**Key file:** `backend/state/manager.py`

### 6. Frontend Dashboard
- Chat interface for submitting goals
- Real-time execution graph (React Flow) showing:
  - Agent nodes with status (pending, running, complete, failed)
  - Data flow edges between agents
  - Expandable nodes to see agent reasoning and tool calls
- Final results panel with formatted output

**Key files:** `frontend/src/components/ExecutionGraph.tsx`, `frontend/src/components/ChatPanel.tsx`

---

## Implementation Plan

### Phase 1: Foundation (Days 1-3)
1. **Project scaffolding**
   - Initialize FastAPI backend with project structure
   - Initialize React + TypeScript frontend with Vite
   - Set up Docker Compose with PostgreSQL and Redis
   - Configure environment variables and API keys

2. **Base agent class**
   ```python
   class BaseAgent:
       name: str
       system_prompt: str
       tools: list[Tool]
       model: str = "claude-opus-4-6"

       async def execute(self, task: Task, context: dict) -> AgentOutput
       async def call_llm(self, messages, tools) -> LLMResponse
   ```

3. **Tool registry**
   - Define Tool protocol/base class with name, description, JSON schema, execute method
   - Implement 2-3 basic tools: `web_search` (via Tavily/Serper API), `execute_python` (subprocess sandbox)

4. **Simple orchestrator**
   - Accept a user goal
   - Use LLM to decompose into subtasks (start with linear chain, not full DAG)
   - Execute subtasks sequentially
   - Return combined result

### Phase 2: Core Intelligence (Days 4-6)
5. **Implement specialist agents**
   - ResearchAgent with web search + summarization
   - CodeAgent with sandboxed code execution
   - DataAgent with pandas/matplotlib in sandbox
   - ReportAgent with markdown synthesis

6. **DAG-based task decomposition**
   - Planner outputs a JSON DAG structure
   - Implement topological sort for execution order
   - Enable parallel execution of independent tasks
   - Handle data passing between dependent tasks

7. **Error handling and recovery**
   - Agent retry with modified prompts on failure
   - Fallback agent assignment (e.g., if CodeAgent fails, try with more context)
   - Timeout handling per agent
   - CriticAgent for output validation

### Phase 3: Real-Time Frontend (Days 7-9)
8. **WebSocket streaming**
   - FastAPI WebSocket endpoint for session updates
   - Stream events: task_started, agent_thinking, tool_called, tool_result, task_complete, error
   - Frontend WebSocket client with reconnection logic

9. **Execution graph visualization**
   - React Flow graph with custom agent nodes
   - Color-coded status: gray (pending), blue (running), green (complete), red (failed)
   - Animated edges showing data flow
   - Click node to expand and see agent's reasoning trace

10. **Chat interface**
    - Message input with goal submission
    - Streaming response display
    - History sidebar with past sessions

### Phase 4: Polish & Deploy (Days 10-12)
11. **Persistence and history**
    - Save execution traces to PostgreSQL
    - Replay past executions
    - Cost tracking (token usage per agent)

12. **Observability**
    - Structured logging for all agent actions
    - Latency tracking per agent and tool
    - Token usage dashboard

13. **Deployment**
    - Dockerize frontend and backend
    - Deploy to Railway/Fly.io
    - Environment-based config
    - Rate limiting and API key management

---

## Data Models

```python
class Task(BaseModel):
    id: str
    description: str
    agent_type: str  # "research", "code", "data", "report"
    dependencies: list[str]  # task IDs
    status: Literal["pending", "running", "complete", "failed"]
    input_data: dict
    output_data: dict | None

class ExecutionPlan(BaseModel):
    goal: str
    tasks: list[Task]  # Forms a DAG

class AgentOutput(BaseModel):
    agent_name: str
    task_id: str
    result: str
    artifacts: list[Artifact]  # files, charts, code blocks
    reasoning_trace: list[str]
    tokens_used: int
    duration_ms: int

class SessionEvent(BaseModel):
    event_type: str
    timestamp: datetime
    data: dict
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sessions` | Create new session with a goal |
| GET | `/api/sessions/{id}` | Get session status and results |
| WS | `/ws/sessions/{id}` | WebSocket for real-time updates |
| GET | `/api/sessions/{id}/graph` | Get execution graph data |
| GET | `/api/sessions` | List past sessions |
| GET | `/api/agents` | List available agent types |

---

## Demo Scenarios to Showcase

1. **"Research the top 5 AI startups of 2026 and create a comparison report"**
   - ResearchAgent searches the web → DataAgent creates comparison table → ReportAgent generates PDF

2. **"Build a Python function that fetches weather data and test it"**
   - CodeAgent writes function → CodeAgent writes tests → CodeAgent runs tests → CriticAgent reviews

3. **"Analyze this CSV of sales data and give me insights with charts"**
   - DataAgent loads and cleans data → DataAgent generates charts → ReportAgent writes summary

---

## Key Differentiators to Highlight in Portfolio
- **Custom orchestration** — not just wrapping LangChain/CrewAI
- **Real-time visibility** — execution graph shows exactly what's happening
- **Production patterns** — retry logic, error recovery, structured outputs, observability
- **Tool use mastery** — proper function calling with Claude's tool_use API
