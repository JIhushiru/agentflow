from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from backend.models import Session, SessionEvent, TaskStatus


class SessionManager:
    """In-memory session store. Swap for Redis/PostgreSQL in production."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._subscribers: dict[str, list[asyncio.Queue[SessionEvent]]] = {}

    def create_session(self, goal: str) -> Session:
        session = Session(goal=goal)
        self._sessions[session.id] = session
        logger.info(f"Session created: {session.id}")
        return session

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[Session]:
        return sorted(self._sessions.values(), key=lambda s: s.created_at, reverse=True)

    def add_event(self, session_id: str, event: SessionEvent) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.events.append(event)

        # Notify subscribers
        for queue in self._subscribers.get(session_id, []):
            queue.put_nowait(event)

    def update_status(self, session_id: str, status: TaskStatus) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.status = status

    def set_result(self, session_id: str, result: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.result = result

    def subscribe(self, session_id: str) -> asyncio.Queue[SessionEvent]:
        queue: asyncio.Queue[SessionEvent] = asyncio.Queue()
        self._subscribers.setdefault(session_id, []).append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[SessionEvent]) -> None:
        subs = self._subscribers.get(session_id, [])
        if queue in subs:
            subs.remove(queue)


# Global singleton
session_manager = SessionManager()
