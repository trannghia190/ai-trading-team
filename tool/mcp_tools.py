"""
MCP Tool Loader — LangChain StructuredTool wrappers for MCP servers.

Does NOT use langchain_mcp_adapters. Instead uses the `mcp` library directly to:
  1. Enumerate tools at startup (brief connection).
  2. Create LangChain StructuredTools with lazy reconnect per call.

Supports:
  - MCPStreamableHTTP (memory, search)
  - MCPStdio           (stock MCP)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

logger = logging.getLogger("trading_team.tools")

# ---------------------------------------------------------------------------
# Correlation context — set by graph._invoke before each agent call so that
# tool-call log entries can be joined with workflow log entries.
#
# Keys:
#   node     — graph node name (e.g. "macro_analyst")
#   session  — session_key from TradingState (user/conversation scope)
#   run_id   — uuid4 generated per _invoke() call (unique per node execution)
#              Use this to group ALL tool calls of a single node run together.
# ---------------------------------------------------------------------------
_tool_node: ContextVar[str]    = ContextVar("tool_node",    default="unknown")
_tool_session: ContextVar[str] = ContextVar("tool_session", default="-")
_tool_run_id: ContextVar[str]  = ContextVar("tool_run_id",  default="-")


def set_tool_log_context(node: str, session: str = "-", run_id: str = "-") -> None:
    """Call this before agent.ainvoke() to tag all tool calls made within."""
    _tool_node.set(node)
    _tool_session.set(session)
    _tool_run_id.set(run_id)

# ---------------------------------------------------------------------------
# MCP imports
# ---------------------------------------------------------------------------
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters

@asynccontextmanager
async def _connect_http(url: str):
    """Yield (read, write) streams for either SSE or Streamable HTTP based on the URL."""
    is_sse = url.endswith("/sse") or "/sse?" in url
    if is_sse:
        async with sse_client(url) as streams:
            yield streams[0], streams[1]
    else:
        async with streamable_http_client(url) as (read, write, _):
            yield read, write



# =============================================================================
# Helpers — schema & result formatting
# =============================================================================

def _json_type_to_python(json_type: str) -> type:
    return {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }.get(json_type, str)


def _build_args_schema(tool_spec: Any) -> type[BaseModel]:
    """Build a Pydantic v2 model from an MCP tool's inputSchema."""
    schema: dict = getattr(tool_spec, "inputSchema", {}) or {}
    props: dict = schema.get("properties", {})
    required: set = set(schema.get("required", []))

    field_defs: dict[str, Any] = {}
    for prop_name, prop_spec in props.items():
        py_type = _json_type_to_python(prop_spec.get("type", "string"))
        desc = prop_spec.get("description", "")
        if prop_name in required:
            field_defs[prop_name] = (py_type, Field(description=desc))
        else:
            field_defs[prop_name] = (Optional[py_type], Field(default=None, description=desc))

    if not field_defs:
        field_defs["input"] = (Optional[str], Field(default=None, description="Tool input"))

    return create_model(tool_spec.name + "_schema", **field_defs)


def _format_result(result: Any) -> str:
    """Convert MCP CallToolResult to plain string."""
    try:
        content = result.content
        if isinstance(content, list):
            parts = []
            for item in content:
                if hasattr(item, "text"):
                    parts.append(item.text)
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)
    except Exception:
        return str(result)


# =============================================================================
# Low-level callers (lazy connect per call)
# =============================================================================

_MCP_RETRIES           = 2
_MCP_RETRY_WAIT        = 3    # seconds — transient network errors
_RATE_LIMIT_WAIT       = 65   # seconds — vnstock rate limit (20 req/min window)
_TOOL_CALL_TIMEOUT     = 90   # seconds — don't let hung MCP calls consume the whole node timeout
_RATE_LIMIT_EXIT_WAIT  = 65   # seconds — MCP process may exit instead of returning a rate-limit message

# Keywords that indicate vnstock API rate limit exceeded
_RATE_LIMIT_KEYWORDS = (
    "giới hạn api",
    "rate limit exceeded",
    "rate limit",
    "đã đạt giới hạn",
    "requests/phút",
    "requests/minute",
    "chờ",          # "Wait 18 seconds to continue"
)


def _is_rate_limited(msg: str) -> bool:
    """Return True if the result indicates a vnstock API rate limit."""
    low = msg.lower()
    return any(p in low for p in _RATE_LIMIT_KEYWORDS)


def _compact_log(text: str, limit: int) -> str:
    """Collapse all whitespace runs to a single space for compact inline log output."""
    import re as _re
    compact = _re.sub(r'\s+', ' ', text).strip() if text else ""
    return compact[:limit] + ("..." if len(compact) > limit else "")


def _looks_like_rate_limit_exit(exc: Exception) -> bool:
    """Heuristic for MCP stdio exits likely caused by inner-library rate limiting.

    Some stock wrappers terminate the process (sys.exit) instead of returning a
    normal tool error/result. In that case we won't see a rate-limit string in
    the tool result, only a transport/process exception from the stdio session.
    """
    low = str(exc).lower()
    return any(
        p in low
        for p in (
            *_RATE_LIMIT_KEYWORDS,
            "systemexit",
            "exit",
            "eof",
            "endofstream",
            "broken pipe",
            "connection closed",
            "process exited",
            "stream closed",
        )
    )


def _tool_log_context(tool_name: str, transport: str) -> dict[str, Any]:
    return {
        "run_id": _tool_run_id.get(),
        "node": _tool_node.get(),
        "session": _tool_session.get(),
        "tool": tool_name,
        "transport": transport,
    }


def _log_tool_event(event: str, **fields: Any) -> None:
    ordered = " ".join(f"{key}={fields[key]}" for key in fields)
    logger.info("[%s] %s", event, ordered)


async def _call_http(url: str, tool_name: str, arguments: dict) -> tuple[str, dict[str, Any]]:
    """Call an MCP tool over Streamable HTTP.

    Retry policy:
    - Network/protocol exceptions (timeout, connection reset): retry up to
      _MCP_RETRIES times with a short wait — these are transient.
    - Tool responds but content indicates rate-limit: retry with _RATE_LIMIT_WAIT
      — same params will work after the window resets.
    - Tool responds with any other content (error message, wrong format, bad
      params, JS page, etc.): return immediately. Retrying with identical
      params cannot fix a logical error; the LLM must decide what to do next.
    """
    base = _tool_log_context(tool_name, "http")
    total_attempts = _MCP_RETRIES + 1
    started_at = time.perf_counter()
    last: str = ""
    final_status = "error"
    final_reason = "exhausted"
    attempts_used = 0

    for attempt in range(total_attempts):
        attempt_no = attempt + 1
        attempts_used = attempt_no
        attempt_started_at = time.perf_counter()
        try:
            async with _connect_http(url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, arguments),
                        timeout=_TOOL_CALL_TIMEOUT,
                    )
                    text = _format_result(result)
                    elapsed_ms = int((time.perf_counter() - attempt_started_at) * 1000)
                    if _is_rate_limited(text):
                        last = text
                        if attempt < _MCP_RETRIES:
                            final_status = "retry"
                            final_reason = "rate_limit_result"
                            _log_tool_event(
                                "TOOL_ATTEMPT",
                                **base,
                                attempt=attempt_no,
                                max_attempts=total_attempts,
                                elapsed_ms=elapsed_ms,
                                status="retry",
                                retry_reason="rate_limit_result",
                                wait_s=_RATE_LIMIT_WAIT,
                            )
                            await asyncio.sleep(_RATE_LIMIT_WAIT)
                            continue
                        final_status = "rate_limited"
                        final_reason = "rate_limit_result"
                        _log_tool_event(
                            "TOOL_ATTEMPT",
                            **base,
                            attempt=attempt_no,
                            max_attempts=total_attempts,
                            elapsed_ms=elapsed_ms,
                            status="rate_limited",
                            retry_reason="rate_limit_result",
                        )
                        break

                    final_status = "success"
                    final_reason = "none"
                    _log_tool_event(
                        "TOOL_ATTEMPT",
                        **base,
                        attempt=attempt_no,
                        max_attempts=total_attempts,
                        elapsed_ms=elapsed_ms,
                        status="success",
                        retry_reason="none",
                    )
                    total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    return text, {
                        "status": final_status,
                        "retry_reason": final_reason,
                        "attempts_used": attempts_used,
                        "max_attempts": total_attempts,
                        "elapsed_ms": total_elapsed_ms,
                        "transport": "http",
                    }
        except asyncio.TimeoutError as exc:
            last = f"[Tool Error] {tool_name}: {exc}"
            elapsed_ms = int((time.perf_counter() - attempt_started_at) * 1000)
            if attempt < _MCP_RETRIES:
                final_status = "retry"
                final_reason = "timeout"
                _log_tool_event(
                    "TOOL_ATTEMPT",
                    **base,
                    attempt=attempt_no,
                    max_attempts=total_attempts,
                    elapsed_ms=elapsed_ms,
                    status="retry",
                    retry_reason="timeout",
                    wait_s=_MCP_RETRY_WAIT,
                )
                await asyncio.sleep(_MCP_RETRY_WAIT)
                continue
            final_status = "timeout"
            final_reason = "timeout"
            _log_tool_event(
                "TOOL_ATTEMPT",
                **base,
                attempt=attempt_no,
                max_attempts=total_attempts,
                elapsed_ms=elapsed_ms,
                status="timeout",
                retry_reason="timeout",
            )
            break
        except Exception as exc:
            last = f"[Tool Error] {tool_name}: {exc}"
            elapsed_ms = int((time.perf_counter() - attempt_started_at) * 1000)
            if attempt < _MCP_RETRIES:
                final_status = "retry"
                final_reason = "transient_exc"
                _log_tool_event(
                    "TOOL_ATTEMPT",
                    **base,
                    attempt=attempt_no,
                    max_attempts=total_attempts,
                    elapsed_ms=elapsed_ms,
                    status="retry",
                    retry_reason="transient_exc",
                    wait_s=_MCP_RETRY_WAIT,
                    error=_compact_log(str(exc), 300),
                )
                await asyncio.sleep(_MCP_RETRY_WAIT)
                continue
            final_status = "error"
            final_reason = "transient_exc"
            _log_tool_event(
                "TOOL_ATTEMPT",
                **base,
                attempt=attempt_no,
                max_attempts=total_attempts,
                elapsed_ms=elapsed_ms,
                status="error",
                retry_reason="transient_exc",
                error=_compact_log(str(exc), 300),
            )
            break

    total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    return last, {
        "status": final_status,
        "retry_reason": final_reason,
        "attempts_used": attempts_used,
        "max_attempts": total_attempts,
        "elapsed_ms": total_elapsed_ms,
        "transport": "http",
    }


async def _call_stdio(
    command: str,
    args: list[str],
    cwd: str,
    tool_name: str,
    arguments: dict,
) -> tuple[str, dict[str, Any]]:
    """Call an MCP tool over stdio.

    Same retry policy as _call_http: only retry on network exceptions or
    rate-limit responses. Logical errors from the tool are returned immediately.
    """
    base = _tool_log_context(tool_name, "stdio")
    total_attempts = _MCP_RETRIES + 1
    started_at = time.perf_counter()
    last: str = ""
    final_status = "error"
    final_reason = "exhausted"
    attempts_used = 0

    for attempt in range(total_attempts):
        attempt_no = attempt + 1
        attempts_used = attempt_no
        attempt_started_at = time.perf_counter()
        try:
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env={**os.environ, "PYTHONPATH": cwd},
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, arguments),
                        timeout=_TOOL_CALL_TIMEOUT,
                    )
                    text = _format_result(result)
                    elapsed_ms = int((time.perf_counter() - attempt_started_at) * 1000)
                    if _is_rate_limited(text):
                        last = text
                        if attempt < _MCP_RETRIES:
                            final_status = "retry"
                            final_reason = "rate_limit_result"
                            _log_tool_event(
                                "TOOL_ATTEMPT",
                                **base,
                                attempt=attempt_no,
                                max_attempts=total_attempts,
                                elapsed_ms=elapsed_ms,
                                status="retry",
                                retry_reason="rate_limit_result",
                                wait_s=_RATE_LIMIT_WAIT,
                            )
                            await asyncio.sleep(_RATE_LIMIT_WAIT)
                            continue
                        final_status = "rate_limited"
                        final_reason = "rate_limit_result"
                        _log_tool_event(
                            "TOOL_ATTEMPT",
                            **base,
                            attempt=attempt_no,
                            max_attempts=total_attempts,
                            elapsed_ms=elapsed_ms,
                            status="rate_limited",
                            retry_reason="rate_limit_result",
                        )
                        break

                    final_status = "success"
                    final_reason = "none"
                    _log_tool_event(
                        "TOOL_ATTEMPT",
                        **base,
                        attempt=attempt_no,
                        max_attempts=total_attempts,
                        elapsed_ms=elapsed_ms,
                        status="success",
                        retry_reason="none",
                    )
                    total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    return text, {
                        "status": final_status,
                        "retry_reason": final_reason,
                        "attempts_used": attempts_used,
                        "max_attempts": total_attempts,
                        "elapsed_ms": total_elapsed_ms,
                        "transport": "stdio",
                    }
        except asyncio.TimeoutError as exc:
            last = f"[Tool Error] {tool_name}: {exc}"
            elapsed_ms = int((time.perf_counter() - attempt_started_at) * 1000)
            if attempt < _MCP_RETRIES:
                final_status = "retry"
                final_reason = "timeout"
                _log_tool_event(
                    "TOOL_ATTEMPT",
                    **base,
                    attempt=attempt_no,
                    max_attempts=total_attempts,
                    elapsed_ms=elapsed_ms,
                    status="retry",
                    retry_reason="timeout",
                    wait_s=_MCP_RETRY_WAIT,
                )
                await asyncio.sleep(_MCP_RETRY_WAIT)
                continue
            final_status = "timeout"
            final_reason = "timeout"
            _log_tool_event(
                "TOOL_ATTEMPT",
                **base,
                attempt=attempt_no,
                max_attempts=total_attempts,
                elapsed_ms=elapsed_ms,
                status="timeout",
                retry_reason="timeout",
            )
            break
        except Exception as exc:
            last = f"[Tool Error] {tool_name}: {exc}"
            elapsed_ms = int((time.perf_counter() - attempt_started_at) * 1000)
            retry_wait = _RATE_LIMIT_EXIT_WAIT if _looks_like_rate_limit_exit(exc) else _MCP_RETRY_WAIT
            retry_reason = "rate_limit_exit" if retry_wait == _RATE_LIMIT_EXIT_WAIT else "transient_exc"
            if attempt < _MCP_RETRIES:
                final_status = "retry"
                final_reason = retry_reason
                _log_tool_event(
                    "TOOL_ATTEMPT",
                    **base,
                    attempt=attempt_no,
                    max_attempts=total_attempts,
                    elapsed_ms=elapsed_ms,
                    status="retry",
                    retry_reason=retry_reason,
                    wait_s=retry_wait,
                    error=_compact_log(str(exc), 300),
                )
                await asyncio.sleep(retry_wait)
                continue
            final_status = "error"
            final_reason = retry_reason
            _log_tool_event(
                "TOOL_ATTEMPT",
                **base,
                attempt=attempt_no,
                max_attempts=total_attempts,
                elapsed_ms=elapsed_ms,
                status="error",
                retry_reason=retry_reason,
                error=_compact_log(str(exc), 300),
            )
            break

    total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    return last, {
        "status": final_status,
        "retry_reason": final_reason,
        "attempts_used": attempts_used,
        "max_attempts": total_attempts,
        "elapsed_ms": total_elapsed_ms,
        "transport": "stdio",
    }


# =============================================================================
# Tool list discovery (connect once, get list, disconnect)
# =============================================================================

async def _list_http_tools(url: str) -> list:
    async with _connect_http(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools


async def _list_stdio_tools(command: str, args: list[str], cwd: str) -> list:
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env={**os.environ, "PYTHONPATH": cwd},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools


# =============================================================================
# StructuredTool factories
# =============================================================================

def _make_http_tool(tool_spec: Any, url: str) -> StructuredTool:
    schema_cls = _build_args_schema(tool_spec)
    tool_name = tool_spec.name
    tool_desc = (tool_spec.description or "").strip()

    async def _run(**kwargs: Any) -> str:
        _node = _tool_node.get()
        _sess = _tool_session.get()
        _rid  = _tool_run_id.get()
        # Strip None — LLM passes None for optional params meaning "use default";
        # sending None to MCP server causes pydantic validation errors.
        arguments = {k: v for k, v in kwargs.items() if v is not None}
        started_at = time.perf_counter()
        logger.debug("[TOOL_CALL] run_id=%s node=%s session=%s tool=%s args=%s", _rid, _node, _sess, tool_name, arguments)
        result, telemetry = await _call_http(url, tool_name, arguments)
        logger.debug("[TOOL_RESULT] run_id=%s node=%s session=%s tool=%s → %s", _rid, _node, _sess, tool_name, _compact_log(result, 2000))
        wrapper_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _log_tool_event(
            "TOOL_CALL_SUMMARY",
            run_id=_rid,
            node=_node,
            session=_sess,
            tool=tool_name,
            transport=telemetry["transport"],
            elapsed_ms=wrapper_elapsed_ms,
            inner_elapsed_ms=telemetry["elapsed_ms"],
            attempts_used=telemetry["attempts_used"],
            max_attempts=telemetry["max_attempts"],
            status=telemetry["status"],
            retry_reason=telemetry["retry_reason"],
        )
        return result

    return StructuredTool.from_function(
        coroutine=_run,
        name=tool_name,
        description=tool_desc,
        args_schema=schema_cls,
    )


def _make_stdio_tool(
    tool_spec: Any, command: str, args: list[str], cwd: str
) -> StructuredTool:
    schema_cls = _build_args_schema(tool_spec)
    tool_name = tool_spec.name
    tool_desc = (tool_spec.description or "").strip()

    async def _run(**kwargs: Any) -> str:
        _node = _tool_node.get()
        _sess = _tool_session.get()
        _rid  = _tool_run_id.get()
        # Strip None — LLM passes None for optional params meaning "use default";
        # sending None to MCP server causes pydantic validation errors.
        arguments = {k: v for k, v in kwargs.items() if v is not None}
        started_at = time.perf_counter()
        logger.debug("[TOOL_CALL] run_id=%s node=%s session=%s tool=%s args=%s", _rid, _node, _sess, tool_name, arguments)
        result, telemetry = await _call_stdio(command, args, cwd, tool_name, arguments)
        logger.debug("[TOOL_RESULT] run_id=%s node=%s session=%s tool=%s → %s", _rid, _node, _sess, tool_name, _compact_log(result, 2000))
        wrapper_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _log_tool_event(
            "TOOL_CALL_SUMMARY",
            run_id=_rid,
            node=_node,
            session=_sess,
            tool=tool_name,
            transport=telemetry["transport"],
            elapsed_ms=wrapper_elapsed_ms,
            inner_elapsed_ms=telemetry["elapsed_ms"],
            attempts_used=telemetry["attempts_used"],
            max_attempts=telemetry["max_attempts"],
            status=telemetry["status"],
            retry_reason=telemetry["retry_reason"],
        )
        return result

    return StructuredTool.from_function(
        coroutine=_run,
        name=tool_name,
        description=tool_desc,
        args_schema=schema_cls,
    )


def _log_mcp_error(label: str, exc: Exception) -> None:
    """Log MCP error — unwrap ExceptionGroup if needed."""
    if isinstance(exc, BaseExceptionGroup):
        for sub in exc.exceptions:
            logger.error("❌ %s: %s: %s", label, type(sub).__name__, sub)
    else:
        logger.error("❌ %s: %s: %s", label, type(exc).__name__, exc)


# =============================================================================
# ToolRegistry
# =============================================================================

class ToolRegistry:
    """
    Loads and stores LangChain StructuredTools by preset.

    Presets:
      - "analysis"  : stock + search  → MacroAnalyst, TechnicalAnalyst
      - "strategy"  : stock + memory  → BullAnalyst, BearAnalyst
      - "leader"    : memory          → Leader
    """

    def __init__(
        self,
        stock_script_path: str,
        memory_url: str,
        rival_search_url: str,
    ) -> None:
        self._workspace_root = str(Path(__file__).parent.parent.parent.parent)
        self._stock_script = stock_script_path
        self._memory_url = memory_url
        self._search_url = rival_search_url

        self._stock_tools: list[StructuredTool] = []
        self._memory_tools: list[StructuredTool] = []
        self._search_tools: list[StructuredTool] = []

    async def load(self) -> None:
        """Connect to each MCP server, enumerate tools, and create wrappers."""

        # --- Stock MCP (stdio) ---
        if self._stock_script:
            try:
                logger.info("Loading Stock MCP tools (%s)...", self._stock_script)
                raw = await _list_stdio_tools(
                    command="python",
                    args=[self._stock_script],
                    cwd=self._workspace_root,
                )
                self._stock_tools = [
                    _make_stdio_tool(t, "python", [self._stock_script], self._workspace_root)
                    for t in raw
                ]
                logger.info("Stock MCP loaded: %d tools.", len(self._stock_tools))
            except Exception as exc:
                _log_mcp_error("Stock MCP", exc)
                logger.warning("Stock MCP failed to load, but it is optional. Proceeding without stock tools.")
        else:
            logger.info("Stock MCP script not configured; skipping stock tools.")

        # --- Memory MCP (HTTP) ---
        if self._memory_url:
            try:
                logger.info("Loading Memory MCP tools (%s)...", self._memory_url)
                raw = await _list_http_tools(self._memory_url)
                self._memory_tools = [_make_http_tool(t, self._memory_url) for t in raw]
                logger.info("Memory MCP loaded: %d tools.", len(self._memory_tools))
            except Exception as exc:
                _log_mcp_error("Memory MCP", exc)
                logger.warning("Memory MCP failed to load, but it is optional. Proceeding without memory tools.")
        else:
            logger.info("Memory MCP URL not configured; skipping memory tools.")

        # --- Search MCP (HTTP) ---
        if self._search_url:
            try:
                logger.info("Loading Search MCP tools (%s)...", self._search_url)
                raw = await _list_http_tools(self._search_url)
                self._search_tools = [_make_http_tool(t, self._search_url) for t in raw]
                logger.info("Search MCP loaded: %d tools.", len(self._search_tools))
            except Exception as exc:
                _log_mcp_error("Search MCP", exc)
                logger.warning("Search MCP failed to load, but it is optional. Proceeding without search tools.")
        else:
            logger.info("Search MCP URL not configured; skipping search tools.")

    # ---- Preset getters -------------------------------------------------------

    def get_analysis_tools(self) -> list[StructuredTool]:
        """Analysis room: stock data + web search."""
        return self._stock_tools + self._search_tools

    def get_strategy_tools(self) -> list[StructuredTool]:
        """Strategy room (Bull/Bear): stock + search + MCP memory READ-ONLY.

        Writing to memory is handled by the local filesystem layer (memory_layer.py).
        MCP memory is an external read-only knowledge source — do not add write tools.
        """
        readonly_mcp_memory = [
            t for t in self._memory_tools if t.name in ("memory_search", "memory_list")
        ]
        return self._stock_tools + self._search_tools + readonly_mcp_memory

    def get_leader_tools(self) -> list[StructuredTool]:
        """Leader tools: MCP memory read-only (for synthesis and intake)."""
        return [
            t for t in self._memory_tools if t.name in ("memory_search", "memory_list")
        ]
