from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import BaseModel

from backend.agents import AGENT_REGISTRY
from backend.engine.executor import ExecutionEngine
from backend.models import SessionEvent, TaskStatus
from backend.orchestrator.planner import Planner
from backend.state.manager import session_manager

router = APIRouter()


class CreateSessionRequest(BaseModel):
    goal: str


class SessionResponse(BaseModel):
    id: str
    goal: str
    status: str
    result: str | None = None
    plan: dict[str, Any] | None = None
    events: list[dict[str, Any]] = []


def _session_to_response(session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        goal=session.goal,
        status=session.status.value,
        result=session.result,
        plan=session.plan.model_dump() if session.plan else None,
        events=[e.model_dump(mode="json") for e in session.events],
    )


@router.post("/api/sessions", response_model=SessionResponse)
async def create_session(req: CreateSessionRequest):
    session = session_manager.create_session(req.goal)

    # Run planning and execution in background
    asyncio.create_task(_run_session(session.id, req.goal))

    return _session_to_response(session)


@router.get("/api/sessions", response_model=list[SessionResponse])
async def list_sessions():
    return [_session_to_response(s) for s in session_manager.list_sessions()]


@router.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session)


@router.get("/api/sessions/{session_id}/graph")
async def get_session_graph(session_id: str):
    """Return the execution graph data for visualization."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.plan is None:
        return {"nodes": [], "edges": []}

    nodes = []
    edges = []
    for i, task in enumerate(session.plan.tasks):
        nodes.append({
            "id": task.id,
            "type": "agent",
            "data": {
                "label": task.description[:50],
                "agentType": task.agent_type.value,
                "status": task.status.value,
                "output": task.output_data,
            },
            "position": {"x": 250 * (i % 3), "y": 150 * (i // 3)},
        })
        for dep in task.dependencies:
            edges.append({
                "id": f"{dep}-{task.id}",
                "source": dep,
                "target": task.id,
                "animated": task.status == TaskStatus.RUNNING,
            })

    return {"nodes": nodes, "edges": edges}


@router.get("/api/agents")
async def list_agents():
    return [
        {"type": agent_type.value, "name": agent_cls.name}
        for agent_type, agent_cls in AGENT_REGISTRY.items()
    ]


@router.websocket("/ws/sessions/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    session = session_manager.get_session(session_id)
    if session is None:
        await websocket.close(code=4004, reason="Session not found")
        return

    # Send existing events as replay
    for event in session.events:
        await websocket.send_text(event.model_dump_json())

    # Subscribe to new events
    queue = session_manager.subscribe(session_id)
    try:
        while True:
            event = await queue.get()
            await websocket.send_text(event.model_dump_json())
            if event.event_type in ("session_complete", "session_failed"):
                break
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    finally:
        session_manager.unsubscribe(session_id, queue)


async def _run_session(session_id: str, goal: str) -> None:
    """Background coroutine: plan and execute a session."""
    session = session_manager.get_session(session_id)
    if session is None:
        return

    session_manager.update_status(session_id, TaskStatus.RUNNING)
    session_manager.add_event(session_id, SessionEvent(
        event_type="session_started",
        data={"goal": goal},
    ))

    try:
        # Phase 1: Plan
        session_manager.add_event(session_id, SessionEvent(
            event_type="planning_started",
            data={},
        ))
        planner = Planner()
        plan = await planner.create_plan(goal)
        session.plan = plan

        session_manager.add_event(session_id, SessionEvent(
            event_type="planning_complete",
            data={"num_tasks": len(plan.tasks), "tasks": [t.model_dump(mode="json") for t in plan.tasks]},
        ))

        # Phase 2: Execute
        async def on_event(event: SessionEvent) -> None:
            session_manager.add_event(session_id, event)

        engine = ExecutionEngine(on_event=on_event)
        outputs = await engine.execute(plan)

        # Synthesize final result
        result_parts = []
        for task in plan.tasks:
            if task.id in outputs:
                result_parts.append(f"## {task.description}\n{outputs[task.id].result}")

        final_result = "\n\n---\n\n".join(result_parts)
        session_manager.set_result(session_id, final_result)
        session_manager.update_status(session_id, TaskStatus.COMPLETE)
        session_manager.add_event(session_id, SessionEvent(
            event_type="session_complete",
            data={"result_preview": final_result[:500]},
        ))

    except Exception as e:
        logger.error(f"Session {session_id} failed: {e}")
        session_manager.update_status(session_id, TaskStatus.FAILED)
        session_manager.add_event(session_id, SessionEvent(
            event_type="session_failed",
            data={"error": str(e)},
        ))
