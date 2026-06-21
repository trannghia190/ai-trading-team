"""
API Channel — LangChain Trading Team
--------------------------------------
FastAPI server with Server-Sent Events (SSE) streaming.
Runs on its own port alongside (or instead of) the Telegram channel.

Usage:
    python -m langgraph.langchain_trading_team.main --channel api
    python -m langgraph.langchain_trading_team.main --channel all   # Telegram + API

Endpoints:
    POST /chat          — submit a message, streams SSE events back
    POST /reset         — reset a session's history
    GET  /status        — server health + active session count
    GET  /sessions      — list known session IDs (non-expired)

Authentication:
    If TRADING_API_SERVER_KEY is set, every request must include:
        Authorization: Bearer <TRADING_API_SERVER_KEY>
    Leave unset to disable auth (local dev / testing).

Quick test with curl:
    curl -N -X POST http://localhost:8000/chat \\
         -H "Content-Type: application/json" \\
         -d '{"message":"Phân tích HPG hôm nay","session_id":"test-1"}'
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from workflow.graph import TradingTeamGraph

logger = logging.getLogger("trading_team.api")

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default="default", max_length=128)


class ResetRequest(BaseModel):
    session_id: str = Field(default="default", max_length=128)


# ---------------------------------------------------------------------------
# Session store (mirrors telegram_channel.SessionStore)
# ---------------------------------------------------------------------------

class SessionStore:
    def __init__(self, timeout: int = settings.SESSION_TIMEOUT) -> None:
        self._sessions: dict[str, dict] = {}
        self._timeout = timeout

    def get(self, session_id: str) -> dict:
        now = time.time()
        s = self._sessions.get(session_id)
        if s is None or (now - s.get("last_active", 0)) > self._timeout:
            s = {"history": [], "last_active": now}
            self._sessions[session_id] = s
        return s

    def touch(self, session_id: str) -> None:
        self._sessions.setdefault(session_id, {"history": [], "last_active": 0})[
            "last_active"
        ] = time.time()

    def append(self, session_id: str, role: str, text: str) -> None:
        s = self.get(session_id)
        s["history"].append({"role": role, "text": text})
        s["history"] = s["history"][-10:]
        self.touch(session_id)

    def format_history(self, session_id: str) -> str:
        s = self.get(session_id)
        lines = [
            ("User" if t["role"] == "user" else "Leader") + ": " + t["text"][:300]
            for t in s["history"]
        ]
        return "\n".join(lines)

    def reset(self, session_id: str) -> None:
        self._sessions[session_id] = {"history": [], "last_active": time.time()}

    def active_ids(self) -> list[str]:
        now = time.time()
        return [
            sid
            for sid, s in self._sessions.items()
            if (now - s.get("last_active", 0)) <= self._timeout
        ]


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

def _check_auth(authorization: str | None = Header(default=None)) -> None:
    expected = settings.API_SERVER_KEY
    if not expected:
        return  # auth disabled
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Use: Bearer <token>",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


# ---------------------------------------------------------------------------
# APIChannel
# ---------------------------------------------------------------------------

class APIChannel:
    """FastAPI channel backed by a LangGraph TradingTeamGraph."""

    _NODE_LABELS: dict[str, str] = {
        "leader_intake":          "Leader",
        "needs_clarification":    "Leader (clarification needed)",
        "lead_analysis":          "Analysis Room (Macro ∥ Technical)",
        "bull_argument":          "BullAnalyst",
        "bear_argument":          "BearAnalyst",
        "arbitration":            "Leader (arbitration)",
        "strategy_synthesis":     "Strategy Room",
        "leader_review":          "Final Answer",
        "leader_review_revision": "Leader (revision request)",
        "synthesis":              "Final Summary",
        "memory_save":            "Memory Save",
        "error":                  "Error",
    }

    def __init__(self, workflow: TradingTeamGraph) -> None:
        self._workflow = workflow
        self._sessions = SessionStore()
        self._active: dict[str, asyncio.Task] = {}

        self.app = FastAPI(
            title="Trading Team API",
            description="LangChain trading team — REST/SSE interface",
            version="1.0.0",
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # tighten in production
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._register_routes()

    # -----------------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------------

    def _register_routes(self) -> None:
        app = self.app

        @app.get("/status", dependencies=[Depends(_check_auth)])
        async def get_status():
            return {
                "status": "ok",
                "active_sessions": len(self._active),
                "known_sessions": len(self._sessions.active_ids()),
            }

        @app.get("/sessions", dependencies=[Depends(_check_auth)])
        async def list_sessions():
            return {"sessions": self._sessions.active_ids()}

        @app.post("/reset", dependencies=[Depends(_check_auth)])
        async def reset_session(body: ResetRequest):
            task = self._active.pop(body.session_id, None)
            if task and not task.done():
                task.cancel()
            self._sessions.reset(body.session_id)
            return {"ok": True, "session_id": body.session_id}

        @app.post("/chat", dependencies=[Depends(_check_auth)])
        async def chat(body: ChatRequest, request: Request):
            return StreamingResponse(
                self._stream_chat(body, request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",  # disable nginx buffering
                },
            )

    # -----------------------------------------------------------------------
    # SSE stream generator
    # -----------------------------------------------------------------------

    async def _stream_chat(
        self, body: ChatRequest, request: Request
    ) -> AsyncIterator[str]:
        session_id = body.session_id
        user_message = body.message

        # Cancel any existing task for this session
        existing = self._active.pop(session_id, None)
        if existing and not existing.done():
            existing.cancel()

        self._sessions.append(session_id, "user", user_message)

        inputs = {
            "question":    user_message,
            "history":     self._sessions.format_history(session_id),
            "session_key": session_id,
        }

        final_text = ""

        def _sse(event: str, data: dict) -> str:
            payload = json.dumps(data, ensure_ascii=False)
            return f"event: {event}\ndata: {payload}\n\n"

        try:
            async for event_type, text in self._workflow.astream(inputs):
                # Respect client disconnect
                if await request.is_disconnected():
                    logger.info("Client disconnected mid-stream (session=%s)", session_id)
                    return

                if not text:
                    continue

                label = self._NODE_LABELS.get(event_type, event_type)
                yield _sse(
                    event_type,
                    {"event": event_type, "label": label, "text": text},
                )

                if event_type in ("synthesis", "leader_review"):
                    final_text = text
                elif event_type == "leader_intake":
                    # For [FLOW:direct] responses, leader_intake IS the final
                    # answer — there are no later nodes. Capture it so the
                    # session history contains both the user question and
                    # the leader's reply; otherwise the next turn's leader
                    # has no context to reference. For full/analysis_only/
                    # strategy_only flows, leader_review will overwrite
                    # final_text later, so this stays correct.
                    final_text = text
                elif event_type == "needs_clarification":
                    self._sessions.append(session_id, "assistant", text[:500])
                    yield _sse("done", {"event": "done", "label": "", "text": ""})
                    return

            # Stream finished normally
            yield _sse("done", {"event": "done", "label": "", "text": ""})

        except asyncio.CancelledError:
            yield _sse("cancelled", {"event": "cancelled", "label": "", "text": "Task cancelled."})
        except Exception as exc:
            logger.exception("Stream error (session=%s): %s", session_id, exc)
            yield _sse("error", {"event": "error", "label": "Error", "text": str(exc)})
        finally:
            self._active.pop(session_id, None)
            if final_text:
                self._sessions.append(session_id, "assistant", final_text[:500])
