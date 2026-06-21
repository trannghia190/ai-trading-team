"""
Self-Improvement Memory Layer
------------------------------
Directory layout under memory/self_improvement/:

  index.json          — master index of all long-term knowledge files
  patterns.md         — recurring bug patterns + root causes (append-only)
  fix_history.md      — log of every attempted fix: branch, outcome, lessons
  pending.json        — current pending fix (if any); absence = no pending fix
  knowledge/
    <topic>.md        — deep-dive notes on specific topics (e.g. timeout_handling.md)

Short-term memory lives only in the SIState dataclass (in-process, discarded after run).

Agents read long-term memory ON DEMAND via the tools in this module,
not by bulk injection into the prompt.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from . import config as cfg

logger = logging.getLogger("trading_team.si.memory")

# ---------------------------------------------------------------------------
# Bootstrap — ensure directory + files exist
# ---------------------------------------------------------------------------

def ensure_memory_dirs() -> None:
    (cfg.MEMORY_DIR / "knowledge").mkdir(parents=True, exist_ok=True)
    _ensure_file(cfg.MEMORY_DIR / "patterns.md",      _PATTERNS_TEMPLATE)
    _ensure_file(cfg.MEMORY_DIR / "fix_history.md",   _HISTORY_TEMPLATE)
    _ensure_file(cfg.MEMORY_DIR / "project_index.md", _PROJECT_INDEX_TEMPLATE)
    _ensure_file(cfg.MEMORY_DIR / "index.json",       "{}")
    _update_index()


def _ensure_file(path: Path, default_content: str) -> None:
    if not path.exists():
        path.write_text(default_content, encoding="utf-8")


_PATTERNS_TEMPLATE = """\
# Recurring Bug Patterns

Each entry: pattern name, root cause, suggested fix approach.

---
"""

_HISTORY_TEMPLATE = """\
# Fix History

Newest first. Each entry: date, branch, problem, outcome, lesson learned.

---
"""

_PROJECT_INDEX_TEMPLATE = """\
# Project Knowledge Index

Shared by the coding agent and review agent. Keep entries concise — point to
files/modules rather than duplicating content.  Update incrementally as you
learn new facts.

## Package layout
- `trading_team_core.py` — entry point, graph compilation
- `workflow/` — LangGraph nodes and routing
- `tool/` — LangChain tools (vnstock, memory, etc.)
- `agent/` — agent definitions (system prompts, model config)
- `channel/` — Telegram / API channel adapters
- `self_improvement/` — this SI subsystem

## Key conventions
- Agent state: TypedDict in `workflow/state.py`
- Tools registered in `tool/` and injected via `create_deep_agent(tools=...)`
- Memory root: `memory/` directory at package root

## Known library quirks
(add entries here as discovered)

---
"""

# ---------------------------------------------------------------------------
# Index management
# ---------------------------------------------------------------------------

def _update_index() -> None:
    """Rebuild index.json by scanning all .md files in memory/self_improvement/."""
    index: dict[str, str] = {}
    for md in sorted(cfg.MEMORY_DIR.rglob("*.md")):
        rel = md.relative_to(cfg.MEMORY_DIR)
        # First non-empty line as summary
        lines = md.read_text(encoding="utf-8").splitlines()
        summary = next((l.lstrip("#").strip() for l in lines if l.strip()), str(rel))
        index[str(rel)] = summary
    (cfg.MEMORY_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Pending fix management
# ---------------------------------------------------------------------------

def get_pending() -> dict | None:
    """Return pending fix dict or None if no pending fix."""
    if not cfg.PENDING_FILE.exists():
        return None
    try:
        data = json.loads(cfg.PENDING_FILE.read_text(encoding="utf-8"))
        return data if data.get("status") == "pending" else None
    except Exception:
        return None


def set_pending(branch: str, summary: str, created_at: str | None = None) -> None:
    cfg.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    cfg.PENDING_FILE.write_text(
        json.dumps({
            "status":     "pending",
            "branch":     branch,
            "summary":    summary,
            "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_pending(outcome: str, lesson: str = "") -> None:
    """Mark pending fix as resolved and append to fix_history.md."""
    pending = get_pending()
    if pending:
        _append_history(
            branch=pending["branch"],
            summary=pending["summary"],
            created_at=pending.get("created_at", "?"),
            outcome=outcome,
            lesson=lesson,
        )
    if cfg.PENDING_FILE.exists():
        cfg.PENDING_FILE.unlink()


def _append_history(branch: str, summary: str, created_at: str, outcome: str, lesson: str) -> None:
    entry = (
        f"\n## {datetime.now(timezone.utc).strftime('%Y-%m-%d')} — `{branch}`\n"
        f"- **Created**: {created_at}\n"
        f"- **Summary**: {summary}\n"
        f"- **Outcome**: {outcome}\n"
        f"- **Lesson**: {lesson or '—'}\n"
    )
    history_path = cfg.MEMORY_DIR / "fix_history.md"
    if history_path.exists():
        existing = history_path.read_text(encoding="utf-8")
        # Insert after header block (before first "---" separator or append)
        sep = "---\n"
        if sep in existing:
            history_path.write_text(
                existing.replace(sep, sep + entry, 1), encoding="utf-8"
            )
        else:
            history_path.write_text(existing + entry, encoding="utf-8")
    _update_index()


def append_pattern(pattern_name: str, root_cause: str, fix_approach: str) -> None:
    """Add a recurring pattern to patterns.md."""
    entry = (
        f"\n## {pattern_name}\n"
        f"- **Root cause**: {root_cause}\n"
        f"- **Fix approach**: {fix_approach}\n"
    )
    p = cfg.MEMORY_DIR / "patterns.md"
    if p.exists():
        p.write_text(p.read_text(encoding="utf-8") + entry, encoding="utf-8")
    _update_index()


def write_knowledge(topic: str, content: str) -> None:
    """Write/overwrite a topic file in knowledge/."""
    path = cfg.MEMORY_DIR / "knowledge" / f"{topic}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _update_index()


# ---------------------------------------------------------------------------
# LangChain tools (given to analyzer agents)
# ---------------------------------------------------------------------------

def make_memory_tools() -> list[StructuredTool]:
    """Return list of LangChain tools for reading long-term SI memory."""

    class _ReadInput(BaseModel):
        path: str = Field(description=(
            "Relative path inside memory/self_improvement/ e.g. 'patterns.md' "
            "or 'knowledge/timeout_handling.md'. Use list_memory_index first to discover files."
        ))

    class _WriteKnowledgeInput(BaseModel):
        topic: str = Field(description="Slug for the knowledge file, e.g. 'timeout_handling'")
        content: str = Field(description="Full markdown content to write")

    class _AppendPatternInput(BaseModel):
        pattern_name: str = Field(description="Short name for the recurring pattern")
        root_cause:   str = Field(description="Root cause description")
        fix_approach: str = Field(description="Suggested fix approach")

    def _read_memory(path: str) -> str:
        full = cfg.MEMORY_DIR / path
        if not full.exists():
            return f"[memory] File not found: {path}"
        return full.read_text(encoding="utf-8")

    def _list_index() -> str:
        idx_path = cfg.MEMORY_DIR / "index.json"
        if not idx_path.exists():
            return "[memory] Index not yet initialised."
        return idx_path.read_text(encoding="utf-8")

    def _write_knowledge(topic: str, content: str) -> str:
        write_knowledge(topic, content)
        return f"[memory] Written knowledge/{topic}.md"

    def _append_pattern(pattern_name: str, root_cause: str, fix_approach: str) -> str:
        append_pattern(pattern_name, root_cause, fix_approach)
        return f"[memory] Pattern '{pattern_name}' appended to patterns.md"

    return [
        StructuredTool.from_function(
            func=_list_index,
            name="list_memory_index",
            description=(
                "List all long-term self-improvement knowledge files with their summaries. "
                "Always call this first to discover what is available before reading."
            ),
        ),
        StructuredTool.from_function(
            func=_read_memory,
            name="read_memory",
            description=(
                "Read a specific long-term memory file. Use list_memory_index first to get valid paths."
            ),
            args_schema=_ReadInput,
        ),
        StructuredTool.from_function(
            func=_write_knowledge,
            name="write_knowledge",
            description=(
                "Write or update a knowledge note about a specific topic "
                "(e.g. 'timeout_handling', 'mcp_patterns'). "
                "Use after discovering a new insight during analysis."
            ),
            args_schema=_WriteKnowledgeInput,
        ),
        StructuredTool.from_function(
            func=_append_pattern,
            name="append_bug_pattern",
            description=(
                "Record a newly discovered recurring bug pattern into long-term memory. "
                "Call this when you identify a pattern that has appeared more than once."
            ),
            args_schema=_AppendPatternInput,
        ),
    ]
