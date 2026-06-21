"""
SI Coding Agent — deepagents-powered code writer.

The agent uses LocalShellBackend to give the LLM read/write access to the
source repo (/repo/) and read access to SI memory (/memory/).  It runs to
completion — no interrupts.  After the agent finishes, the caller uses
git_ops.commit_workdir_changes() to snapshot the modified files into a branch
and notify the user.  Merge / discard is the user's decision via /si_approve
or /si_reject.
"""
from __future__ import annotations

import asyncio
import logging
import subprocess

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from . import config as cfg

logger = logging.getLogger("trading_team.si.agent")

# ---------------------------------------------------------------------------
# Transient error detection (used by retry logic)
# ---------------------------------------------------------------------------

_TRANSIENT_PATTERNS = ("timeout", "connection", "rate limit", "overloaded", "503", "502", "429")


def _is_transient(exc: Exception) -> bool:
    """Return True if the exception looks like a temporary network/rate-limit issue."""
    return any(p in str(exc).lower() for p in _TRANSIENT_PATTERNS)


# ---------------------------------------------------------------------------
# Async LLM invoke with timeout + retry
# ---------------------------------------------------------------------------

async def _invoke_with_retry(agent, messages: dict, label: str):
    """Invoke agent.ainvoke with per-call timeout and retry on transient errors.

    Retries up to cfg.SI_LLM_RETRIES times, waiting cfg.SI_LLM_RETRY_DELAY
    seconds between attempts.  Raises the last exception if all attempts fail.
    """
    last_exc: Exception | None = None
    total = cfg.SI_LLM_RETRIES + 1
    for attempt in range(total):
        try:
            return await asyncio.wait_for(
                agent.ainvoke(messages),
                timeout=cfg.SI_NODE_TIMEOUT,
            )
        except asyncio.TimeoutError as exc:
            last_exc = exc
            logger.warning(
                "[%s] LLM timeout on attempt %d/%d (timeout=%ds)",
                label, attempt + 1, total, cfg.SI_NODE_TIMEOUT,
            )
        except Exception as exc:
            if _is_transient(exc):
                last_exc = exc
                logger.warning(
                    "[%s] Transient LLM error on attempt %d/%d: %s",
                    label, attempt + 1, total, exc,
                )
            else:
                raise  # non-transient — propagate immediately
        if attempt < cfg.SI_LLM_RETRIES:
            await asyncio.sleep(cfg.SI_LLM_RETRY_DELAY)
    assert last_exc is not None
    raise last_exc

# ---------------------------------------------------------------------------
# Shared Pydantic schemas
# ---------------------------------------------------------------------------

class ReviewResult(BaseModel):
    approved: bool = Field(description="True if code changes are correct and complete")
    issues: list[str] = Field(
        default_factory=list,
        description="Specific issues found (empty if approved)",
    )
    feedback: str = Field(
        default="",
        description="Actionable feedback for the coding agent to address (empty if approved)",
    )


# ---------------------------------------------------------------------------
# Read-only shell tool for the review agent
# ---------------------------------------------------------------------------

_BLOCKED_SHELL = (
    "rm ", "mv ", "cp ", "git commit", "git push", "git add", "git reset",
    "git checkout", "pip install", "pip uninstall", "chmod", "chown",
    "touch ", "mkdir", "rmdir", "write_file", "edit_file",
)


@tool
def run_shell_readonly(command: str) -> str:
    """Run a read-only shell command inside the repo directory.

    Use for: git diff, python -m py_compile, grep, find, cat, head, wc.
    Cannot run destructive commands (rm, git commit/push, pip install, etc.).
    On timeout, retries with doubled timeout (e.g. 30s → 60s → 120s).
    """
    cmd_lower = command.strip().lower()
    for blocked in _BLOCKED_SHELL:
        if blocked in cmd_lower:
            return f"[blocked] '{blocked.strip()}' is not permitted in review mode."

    timeout = cfg.SI_SHELL_READ_TIMEOUT
    total = cfg.SI_SHELL_READ_RETRIES + 1
    for attempt in range(total):
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=str(cfg.REPO_DIR),
            )
            out = (result.stdout + result.stderr).strip()
            return out[:5000] if out else "(no output)"
        except subprocess.TimeoutExpired:
            if attempt < cfg.SI_SHELL_READ_RETRIES:
                timeout *= 2
                logger.warning(
                    "run_shell_readonly: timeout on attempt %d/%d, retrying with %ds",
                    attempt + 1, total, timeout,
                )
                continue
            return f"[timeout] Command exceeded {timeout}s after {total} attempt(s)."
        except Exception as exc:
            return f"[error] {exc}"


# ---------------------------------------------------------------------------
# Singleton deepagents graphs
# ---------------------------------------------------------------------------

_si_agent = None  # created once on first call to get_si_agent()


def get_si_agent():
    """Return (and lazily create) the singleton SI coding agent."""
    global _si_agent
    if _si_agent is not None:
        return _si_agent

    from deepagents import create_deep_agent
    from deepagents.backends import CompositeBackend, LocalShellBackend, StateBackend
    from deepagents.middleware.filesystem import FilesystemPermission

    _si_agent = create_deep_agent(
        model=cfg.CODING_MODEL,
        system_prompt=(
            "You are a senior Python engineer fixing bugs in a live trading bot and writing corresponding tests.\n\n"
            "File path conventions:\n"
            "  /repo/<relative-path>  — source/test files (e.g. /repo/workflow/graph.py)\n"
            "  /memory/self_improvement/patterns.md  — known bug patterns\n"
            "  /memory/self_improvement/fix_history.md  — past fix outcomes\n\n"
            "Workflow:\n"
            "1. Read /memory/self_improvement/patterns.md first for context.\n"
            "2. Read every affected source file with read_file BEFORE modifying it.\n"
            "3. Apply MINIMAL changes — only fix what is described in the task.\n"
            "4. Write/modify the source code file.\n"
            "5. WRITE A UNIT TEST to cover your change and verify the fix. Tests must be placed under "
            "   `/repo/tests/` (e.g. `/repo/tests/test_fix_<slug>.py`). Use `__init__.py` if creating new test directories.\n"
            "6. The unit test MUST be built using Python's standard `unittest` and `unittest.mock` library. "
            "   You MUST mock all external API calls, LLM models, and MCP tools (e.g., vnstock, telegram, or database calls) "
            "   so that the test runs entirely locally, instantly, and without internet access or side-effects.\n"
            "7. Verify both successful cases and failure edge-cases in the tests.\n"
            "8. Preserve all imports, docstrings, and surrounding code structure.\n"
            "9. Python 3.11 compatible.\n\n"
            "Do NOT add explanations after writing files — just write them."
        ),
        permissions=[
            FilesystemPermission(operations=["read", "write"], paths=["/memory/"]),
            FilesystemPermission(operations=["read", "write"], paths=["/repo/"]),
        ],
        backend=CompositeBackend(
            default=StateBackend(),
            routes={
                "/memory/": LocalShellBackend(
                    root_dir=str(cfg.REPO_DIR / "memory"),
                    virtual_mode=True,
                ),
                "/repo/": LocalShellBackend(
                    root_dir=str(cfg.REPO_DIR),
                    virtual_mode=True,
                ),
            },
        ),
        name="SICodeAgent",
    )
    logger.info("SI coding agent created (model=%s)", cfg.CODING_MODEL)
    return _si_agent


# ---------------------------------------------------------------------------
# Review agent — read-only on /repo/, read-write on /memory/
# ---------------------------------------------------------------------------

_si_review_agent = None


def get_si_review_agent():
    """Return (and lazily create) the singleton SI review agent."""
    global _si_review_agent
    if _si_review_agent is not None:
        return _si_review_agent

    from deepagents import create_deep_agent
    from deepagents.backends import CompositeBackend, LocalShellBackend, StateBackend
    from deepagents.middleware.filesystem import FilesystemPermission

    _si_review_agent = create_deep_agent(
        model=cfg.CODING_MODEL,
        tools=[run_shell_readonly],
        system_prompt=(
            "You are a senior code reviewer for a live Python trading bot.\n\n"
            "File path conventions:\n"
            "  /repo/<relative-path>  — source/test files (read-only for you)\n"
            "  /memory/self_improvement/project_index.md  — shared project knowledge index\n"
            "  /memory/self_improvement/patterns.md  — known bug patterns\n\n"
            "Workflow:\n"
            "1. Read /memory/self_improvement/project_index.md for project context.\n"
            "2. Read each modified source file and its new/updated unit test via its /repo/ path.\n"
            "3. Verify that the coder wrote corresponding unit tests in `/repo/tests/` to reproduce and patch the issue.\n"
            "4. Use `run_shell_readonly` to run the test suite and verify they pass. "
            "   Run `PYTHONPATH=../.. python -m unittest discover -s tests -t ../..` from the repository root. "
            "   Also run `python -m py_compile` to check syntax of changed files.\n"
            "5. Verify the fix actually solves the stated problem and does not cause regressions.\n"
            "6. Rejects (approved=False) if the unit test is missing, incomplete, does not mock API calls/LLMs (yielding network hits), or if tests fail.\n"
            "7. If you discover new project knowledge (structure, library quirks, conventions), "
            "append a concise entry to /memory/self_improvement/project_index.md.\n\n"
            "You CANNOT modify source files — /repo/ is read-only for you.\n"
            "Respond only with structured output."
        ),
        permissions=[
            FilesystemPermission(operations=["read"], paths=["/repo/"]),
            FilesystemPermission(operations=["read", "write"], paths=["/memory/"]),
        ],
        backend=CompositeBackend(
            default=StateBackend(),
            routes={
                "/memory/": LocalShellBackend(
                    root_dir=str(cfg.REPO_DIR / "memory"),
                    virtual_mode=True,
                ),
                "/repo/": LocalShellBackend(
                    root_dir=str(cfg.REPO_DIR),
                    virtual_mode=True,
                ),
            },
        ),
        response_format=ReviewResult,
        name="SIReviewAgent",
    )
    logger.info("SI review agent created (model=%s)", cfg.CODING_MODEL)
    return _si_review_agent


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_agent(task: str) -> dict:
    """Run the SI coding agent with timeout + retry on transient LLM errors."""
    agent = get_si_agent()
    return await _invoke_with_retry(
        agent,
        {"messages": [HumanMessage(content=task)]},
        label="run_agent",
    )


async def run_review(prompt: str) -> ReviewResult:
    """Run the SI review agent with timeout + retry; return structured ReviewResult."""
    agent = get_si_review_agent()
    result = await _invoke_with_retry(
        agent,
        {"messages": [HumanMessage(content=prompt)]},
        label="run_review",
    )
    return result["structured_response"]
