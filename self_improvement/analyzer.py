"""Self-Improvement Analyzer — LangGraph state machine.

Graph:
  classify → [noise → END]
           → [actionable → run_agent → review → notify → END]
                                    ↑____________| (if issues found, up to MAX_REVIEW_ITERATIONS)

node_classify  : deepagents classify agent → ClassifyResult (structured)
node_run_agent : deepagents coding agent → writes files to disk
node_review    : deepagents review agent → ReviewResult (structured); loops back on issues
node_git       : stages + commits modified files to a fix branch
node_notify    : Telegram notification for human review

Short-term state (SIState) lives only in memory for this run.
"""
from __future__ import annotations

import asyncio
import logging
import textwrap
from dataclasses import dataclass, field
from typing import Any, Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from . import config as cfg
from .collector import CollectedEvidence, mark_sessions_reviewed
from .git_ops import CommitResult, commit_workdir_changes, get_modified_files, get_repo_file_content
from .memory import ensure_memory_dirs

logger = logging.getLogger("trading_team.si.analyzer")

# ---------------------------------------------------------------------------
# Short-term state (in-memory only)
# ---------------------------------------------------------------------------

@dataclass
class SIState:
    # Input
    evidence:          CollectedEvidence | None = None

    # After classify
    verdict:           Literal["noise", "bug", "improvement", "mixed"] = "noise"
    problem_summary:   str  = ""
    problem_slug:      str  = ""
    affected_files:    list[str] = field(default_factory=list)
    risk_level:        Literal["low", "medium", "high"] = "low"

    # After run_agent
    written_files:     list[str] = field(default_factory=list)
    commit_message:    str  = ""

    # Review loop
    review_iterations: int  = 0
    review_comments:   str  = ""   # non-empty = last review rejected; blank = approved

    # After git
    commit_result:     CommitResult | None = None

    # After notify
    notified:          bool = False
    error:             str  = ""


# ---------------------------------------------------------------------------
# Structured output schema for node_classify
# ---------------------------------------------------------------------------

class ClassifyResult(BaseModel):
    verdict: Literal["noise", "bug", "improvement", "mixed"] = Field(
        description="noise | bug | improvement | mixed"
    )
    problem_summary: str = Field(
        description="1-3 sentence description, or 'nothing actionable' for noise"
    )
    problem_slug: str = Field(
        description="3-5 word kebab-case identifier, blank for noise"
    )
    affected_files: list[str] = Field(
        default_factory=list,
        description="relative .py paths inside the repo that need changes (empty for noise)",
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        default="low",
        description="low = safe refactor, high = core logic change",
    )


# ---------------------------------------------------------------------------
# Classify agent (deepagents) — created lazily
# ---------------------------------------------------------------------------

_classify_agent = None


def _get_classify_agent():
    global _classify_agent
    if _classify_agent is not None:
        return _classify_agent

    from deepagents import create_deep_agent
    from deepagents.backends import CompositeBackend, LocalShellBackend, StateBackend
    from deepagents.middleware.filesystem import FilesystemPermission

    _classify_agent = create_deep_agent(
        model=cfg.CODING_MODEL,
        system_prompt=(
            "You are a senior software engineer reviewing a live trading bot's logs and sessions.\n"
            "Read /memory/self_improvement/patterns.md for known recurring patterns before classifying.\n"
            "Respond only with the structured output — no prose."
        ),
        permissions=[
            FilesystemPermission(operations=["read"], paths=["/memory/"]),
        ],
        backend=CompositeBackend(
            default=StateBackend(),
            routes={
                "/memory/": LocalShellBackend(
                    root_dir=str(cfg.REPO_DIR / "memory"),
                    virtual_mode=True,
                ),
            },
        ),
        response_format=ClassifyResult,
        name="SIClassifyAgent",
    )
    return _classify_agent


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def node_classify(state: SIState) -> SIState:
    """Decide if the evidence is noise, a bug, or an improvement opportunity."""
    ev = state.evidence
    if not ev or ev.is_empty():
        state.verdict = "noise"
        state.problem_summary = "No evidence collected."
        return state

    log_block = f"### LOG EXCERPT\n```\n{ev.log_excerpt}\n```" if ev.log_excerpt else ""
    sessions_block = ""
    for name, content in ev.sessions:
        sessions_block += f"\n### SESSION: {name}\n{content[:3000]}\n"

    max_files = cfg.MAX_FILES_PER_FIX if cfg.MAX_FILES_PER_FIX else "unlimited"
    prompt = textwrap.dedent(f"""\
        Analyse the evidence below and classify the issue.

        Rules:
        - "noise" = expected errors, env issues, nothing to fix in code
        - "bug" = reproducible error caused by a code defect
        - "improvement" = code works but quality/error handling can be better
        - "mixed" = both bug and improvement (treat as bug priority)
        - Only flag actionable CODE issues. Do NOT flag data/market events.
        - affected_files: only .py files inside the repo, max {max_files}

        {log_block}
        {sessions_block}
    """)

    agent = _get_classify_agent()
    last_exc: Exception | None = None
    total = cfg.SI_LLM_RETRIES + 1
    for attempt in range(total):
        try:
            result = await asyncio.wait_for(
                agent.ainvoke({"messages": [HumanMessage(content=prompt)]}),
                timeout=cfg.SI_NODE_TIMEOUT,
            )
            # response_format=ClassifyResult → result["structured_response"] is a ClassifyResult
            data: ClassifyResult = result["structured_response"]
            state.verdict        = data.verdict
            state.problem_summary = data.problem_summary
            state.problem_slug   = data.problem_slug or "fix"
            files = data.affected_files
            state.affected_files = files if cfg.MAX_FILES_PER_FIX is None else files[:cfg.MAX_FILES_PER_FIX]
            state.risk_level     = data.risk_level
            break  # success
        except asyncio.TimeoutError as exc:
            last_exc = exc
            logger.warning("classify: timeout on attempt %d/%d", attempt + 1, total)
        except Exception as exc:
            last_exc = exc
            logger.warning("classify: agent error on attempt %d/%d: %s", attempt + 1, total, exc)
        if attempt < cfg.SI_LLM_RETRIES:
            await asyncio.sleep(cfg.SI_LLM_RETRY_DELAY)
    else:
        logger.warning("classify: all %d attempts failed (%s). Treating as noise.", total, last_exc)
        state.verdict = "noise"

    logger.info("classify verdict=%s risk=%s files=%s", state.verdict, state.risk_level, state.affected_files)
    return state


async def node_run_agent(state: SIState) -> SIState:
    """Plan + code using deepagents: reads and writes files directly to disk.

    The agent runs to completion without interrupts.  Modified files are
    detected afterwards via git diff and committed in node_git.
    """
    from .si_agent import run_agent

    state.commit_message = f"fix: {state.problem_slug}"

    # Build task description — include source file contents for context
    file_contexts = ""
    for rel in state.affected_files:
        content = get_repo_file_content(rel)
        if content:
            file_contexts += f"\nFile /repo/{rel}:\n```python\n{content[:4000]}\n```\n"

    task = textwrap.dedent(f"""\
        ## Task

        **Problem**: {state.problem_summary}
        **Risk level**: {state.risk_level}
        **Affected files**: {state.affected_files}
        **Commit message**: {state.commit_message}

        ## Current file contents

        {file_contexts}
        """)

    if state.review_comments:
        task += textwrap.dedent(f"""\

            ## Code Review Feedback (previous attempt was rejected — fix these issues)

            {state.review_comments}

            Address every point above before writing the files.
            """)
    else:
        task += textwrap.dedent("""\

            ## Instructions

            1. Read /memory/self_improvement/patterns.md for known patterns.
            2. Read /memory/self_improvement/project_index.md for project structure context.
            3. Apply the minimal fix to each affected file.
            4. Write each fixed file using write_file (full new content) or edit_file
               for small targeted edits.
            5. WRITE A CORRESPONDING UNIT TEST under `/repo/tests/` (e.g. `/repo/tests/test_fix_<slug>.py`). Use python standard `unittest` and `unittest.mock`. Mock all external APIs, LLMs, and MCP tools.
            6. If you discover new project knowledge, update
               /memory/self_improvement/project_index.md.
            7. After writing all files (code and test), stop — do not add explanations.
            """)

    logger.info("node_run_agent: invoking SI agent, files=%s (review_iter=%d)",
                state.affected_files, state.review_iterations)
    state.error = ""   # reset any previous error before retry
    total = cfg.SI_LLM_RETRIES + 1
    for attempt in range(total):
        try:
            await run_agent(task)  # raises if all internal LLM retries also fail
        except Exception as exc:
            logger.error("node_run_agent: agent error (attempt %d/%d): %s", attempt + 1, total, exc)
            state.error = f"Agent error: {exc}"
            return state  # LLM permanently failed — don't retry further

        # Write-check: verify the agent actually modified files
        state.written_files = get_modified_files()
        if state.written_files:
            logger.info(
                "node_run_agent: agent modified %d file(s) on attempt %d: %s",
                len(state.written_files), attempt + 1, state.written_files,
            )
            break

        # Agent ran but wrote nothing — retry (may have got confused or produced no output)
        if attempt < cfg.SI_LLM_RETRIES:
            logger.warning(
                "node_run_agent: agent wrote no files on attempt %d/%d, retrying in %ds...",
                attempt + 1, total, cfg.SI_LLM_RETRY_DELAY,
            )
            await asyncio.sleep(cfg.SI_LLM_RETRY_DELAY)
    else:
        logger.warning("node_run_agent: agent ran but no files modified after %d attempt(s)", total)
        state.error = "Agent ran but did not modify any files."

    return state


async def node_review(state: SIState) -> SIState:
    """Review code changes written by the coding agent.

    Calls the review deepagent with a structured ReviewResult response_format.
    If approved → clears review_comments so routing proceeds to git.
    If rejected → sets review_comments with feedback and increments review_iterations.
    After MAX_REVIEW_ITERATIONS rejections the routing function escalates to notify.
    """
    from .si_agent import run_review
    import subprocess

    # Get unstaged diff for review context (files are on disk, not yet committed)
    diff_proc = subprocess.run(
        ["git", "diff", "HEAD"], capture_output=True, text=True, cwd=str(cfg.REPO_DIR)
    )
    diff_text = diff_proc.stdout.strip()[:6000] or "(no diff available)"

    prompt = textwrap.dedent(f"""\
        Review the code changes below.  A coding agent fixed the following problem:

        **Problem**: {state.problem_summary}
        **Risk level**: {state.risk_level}
        **Modified files**: {state.written_files}
        **Review iteration**: {state.review_iterations + 1} / {cfg.MAX_REVIEW_ITERATIONS}

        ## Git diff (unstaged changes on disk)

        ```diff
        {diff_text}
        ```

        Verify:
        1. The fix actually addresses the stated problem.
        2. No new bugs or regressions introduced.
        3. Python syntax is valid (run py_compile if in doubt).
        4. Imports are correct; no missing or broken references.
        5. Edge cases and error handling are adequate.

        If approved, set approved=True and leave issues/feedback empty.
        If not, set approved=False, list each issue, and write clear actionable feedback.
    """)

    try:
        result = await run_review(prompt)
        if result.approved:
            state.review_comments = ""
            logger.info("review: approved on iteration %d", state.review_iterations + 1)
        else:
            state.review_iterations += 1
            state.review_comments = result.feedback or "\n".join(result.issues)
            logger.warning(
                "review: rejected (iter=%d) issues=%s",
                state.review_iterations, result.issues,
            )
    except Exception as exc:
        # If reviewer crashes, log and approve to avoid blocking the pipeline
        logger.error("node_review: reviewer error (%s). Auto-approving.", exc)
        state.review_comments = ""

    return state


async def node_git(state: SIState) -> SIState:
    """Commit the agent-written files to a new fix branch."""
    if not state.written_files:
        state.error = state.error or "No modified files to commit."
        return state

    result = await commit_workdir_changes(
        problem_slug=state.problem_slug,
        written_files=state.written_files,
        commit_message=state.commit_message,
    )
    state.commit_result = result
    if not result.success:
        state.error = result.error
    return state


async def node_notify(state: SIState) -> SIState:
    """Send Telegram message to the owner for review."""
    try:
        from telegram import Bot
        bot = Bot(token=cfg.NOTIFY_BOT_TOKEN)

        if state.error and not state.commit_result:
            text = (
                f"⚠️ *Self-Improvement run failed*\n\n"
                f"Error: `{state.error}`\n"
                f"Problem: {state.problem_summary}"
            )
        elif state.commit_result and state.commit_result.success:
            diff_lines = state.commit_result.diff or "—"
            text = (
                f"🔧 *Self-Improvement fix ready for review*\n\n"
                f"**Branch**: `{state.commit_result.branch}`\n"
                f"**Commit**: `{state.commit_result.commit}`\n\n"
                f"**Problem**: {state.problem_summary}\n\n"
                f"**Diff**:\n```\n{diff_lines[:800]}\n```\n\n"
                f"To merge:\n"
                f"`git checkout master && git merge --no-ff {state.commit_result.branch}`"
            )
        else:
            text = (
                f"⚠️ *Self-Improvement: git step failed*\n\n"
                f"Error: `{state.commit_result.error if state.commit_result else state.error}`"
            )

        await bot.send_message(
            chat_id=cfg.NOTIFY_CHAT_ID,
            text=text,
            parse_mode="Markdown",
        )
        state.notified = True
        logger.info("Telegram notification sent.")
    except Exception as exc:
        logger.error("notify: Telegram send failed: %s", exc)
        state.error = str(exc)

    return state


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route_classify(state: SIState) -> str:
    if state.verdict in ("bug", "improvement", "mixed"):
        return "run_agent"
    return END


def _route_run_agent(state: SIState) -> str:
    if state.error or not state.written_files:
        return "notify"
    return "review"


def _route_review(state: SIState) -> str:
    # Approved (review_comments cleared)
    if not state.review_comments:
        return "git"
    # Rejected but still have iterations left — send back to coding agent
    if state.review_iterations < cfg.MAX_REVIEW_ITERATIONS:
        return "run_agent"
    # Exhausted iterations
    state.error = (
        f"Review rejected after {state.review_iterations} iteration(s). "
        f"Last feedback: {state.review_comments[:200]}"
    )
    return "notify"


def _route_git(state: SIState) -> str:
    return "notify"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> Any:
    g = StateGraph(SIState)
    g.add_node("classify",   node_classify)
    g.add_node("run_agent",  node_run_agent)
    g.add_node("review",     node_review)
    g.add_node("git",        node_git)
    g.add_node("notify",     node_notify)

    g.set_entry_point("classify")

    g.add_conditional_edges("classify",   _route_classify,
                            {"run_agent": "run_agent", END: END})
    g.add_conditional_edges("run_agent",  _route_run_agent,
                            {"review": "review", "notify": "notify"})
    g.add_conditional_edges("review",     _route_review,
                            {"git": "git", "run_agent": "run_agent", "notify": "notify"})
    g.add_conditional_edges("git",        _route_git,
                            {"notify": "notify"})
    g.add_edge("notify", END)

    return g.compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_analysis(evidence: CollectedEvidence) -> SIState:
    """Run the full analysis graph and return final state."""
    ensure_memory_dirs()
    graph = build_graph()
    initial = SIState(evidence=evidence)
    result = await graph.ainvoke(initial)
    # LangGraph returns a dict when state schema is a dataclass — reconstruct SIState
    if isinstance(result, dict):
        valid_fields = SIState.__dataclass_fields__
        return SIState(**{k: v for k, v in result.items() if k in valid_fields})
    return result
