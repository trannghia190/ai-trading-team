"""
Git operations for self-improvement fixes.

Responsibilities:
- Create a feature branch (si/fix-<slug>)
- Apply file patches provided by the coder agent
- Commit with a descriptive message
- Return a diff summary for the Telegram notification

All git commands are run in cfg.REPO_DIR (the langchain_trading_team repo).
"""
from __future__ import annotations

import asyncio
import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from . import config as cfg

logger = logging.getLogger("trading_team.si.git")


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class CommitResult:
    branch:   str
    commit:   str        # short SHA
    diff:     str        # git diff --stat output
    success:  bool
    error:    str = ""


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _run(args: Sequence[str], cwd: Path | None = None) -> str:
    """Run a git command synchronously, return stdout. Raises on error."""
    result = subprocess.run(
        args,
        cwd=str(cwd or cfg.REPO_DIR),
        capture_output=True,
        text=True,
        env={
            **__import__("os").environ,
            "GIT_AUTHOR_NAME":     cfg.GIT_AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL":    cfg.GIT_AUTHOR_EMAIL,
            "GIT_COMMITTER_NAME":  cfg.GIT_AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": cfg.GIT_AUTHOR_EMAIL,
        },
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(str(a) for a in args[1:3])} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _slugify(text: str, max_len: int = 30) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len]


def current_branch() -> str:
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def branch_exists(name: str) -> bool:
    result = subprocess.run(
        ["git", "branch", "--list", name],
        cwd=str(cfg.REPO_DIR),
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def get_repo_file_content(relative_path: str) -> str:
    """Read a file from the repo (current working tree)."""
    full = cfg.REPO_DIR / relative_path
    if not full.exists():
        return ""
    return full.read_text(encoding="utf-8")


def get_modified_files() -> list[str]:
    """Return relative paths of files modified (but not yet committed) in the working tree."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=str(cfg.REPO_DIR),
        capture_output=True,
        text=True,
    )
    files = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    # Also include untracked new files (in case agent created new files)
    result2 = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=str(cfg.REPO_DIR),
        capture_output=True,
        text=True,
    )
    new_files = [l.strip() for l in result2.stdout.splitlines() if l.strip()]
    return files + new_files


def list_source_files(extensions: tuple[str, ...] = (".py",)) -> list[str]:
    """List all source files in the repo (relative paths)."""
    result = []
    for ext in extensions:
        for p in cfg.REPO_DIR.rglob(f"*{ext}"):
            # exclude __pycache__, .git, venv
            parts = p.parts
            if any(x in parts for x in ("__pycache__", ".git", ".venv", "venv")):
                continue
            result.append(str(p.relative_to(cfg.REPO_DIR)))
    return sorted(result)


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

@dataclass
class FilePatch:
    """A single file modification to apply."""
    relative_path: str   # e.g. "workflow/graph.py"
    new_content:   str   # full new file content


async def create_fix_branch_and_commit(
    problem_slug: str,
    patches:      list[FilePatch],
    commit_message: str,
) -> CommitResult:
    """
    1. Checkout master (or current default branch), pull if clean
    2. Create branch si/fix-<slug>-<date>
    3. Apply patches
    4. git add + commit
    5. Return CommitResult with diff summary

    This is async-friendly: the subprocess calls are run in an executor.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_create_fix_branch_and_commit,
                                      problem_slug, patches, commit_message)


async def commit_workdir_changes(
    problem_slug: str,
    written_files: list[str],
    commit_message: str,
) -> CommitResult:
    """Create a branch and commit files already written to the working tree.

    Used after the HITL agent approves all writes — the files are already on
    disk (written by LocalShellBackend), so we just need to branch + stage + commit.

    Args:
        problem_slug:    kebab-case slug for the branch name
        written_files:   relative paths of files to stage (e.g. ["workflow/graph.py"])
        commit_message:  git commit message
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _sync_commit_workdir_changes, problem_slug, written_files, commit_message
    )


def _sync_commit_workdir_changes(
    problem_slug: str,
    written_files: list[str],
    commit_message: str,
) -> CommitResult:
    date_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
    slug     = _slugify(problem_slug)
    branch   = f"{cfg.BRANCH_PREFIX}{slug}-{date_tag}"

    try:
        current = current_branch()
        if current != "master":
            logger.warning("Not on master (on %s), creating branch from here.", current)

        if branch_exists(branch):
            branch = f"{branch}-2"

        # Create branch (working tree changes are preserved)
        _run(["git", "checkout", "-b", branch])

        # Stage only the files the agent wrote
        if written_files:
            _run(["git", "add", "--"] + written_files)
        else:
            _run(["git", "add", "-A"])

        # Commit
        _run(["git", "commit", "-m", commit_message])
        short_sha = _run(["git", "rev-parse", "--short", "HEAD"])

        diff_stat = _run(["git", "diff", "--stat", f"master...{branch}"])

        _run(["git", "checkout", "master"])

        return CommitResult(branch=branch, commit=short_sha, diff=diff_stat, success=True)

    except Exception as exc:
        logger.error("git_ops.commit_workdir_changes error: %s", exc)
        try:
            _run(["git", "checkout", "master"])
        except Exception:
            pass
        return CommitResult(branch=branch, commit="", diff="", success=False, error=str(exc))


def _sync_create_fix_branch_and_commit(
    problem_slug: str,
    patches:      list[FilePatch],
    commit_message: str,
) -> CommitResult:
    date_tag  = datetime.now(timezone.utc).strftime("%Y%m%d")
    slug      = _slugify(problem_slug)
    branch    = f"{cfg.BRANCH_PREFIX}{slug}-{date_tag}"

    try:
        # Safety: make sure we're on master and working tree is clean
        current = current_branch()
        if current != "master":
            # Don't force-switch — just warn and proceed from current
            logger.warning("Not on master (on %s), creating branch from here.", current)

        # Create branch
        if branch_exists(branch):
            # Append a suffix to avoid collision
            branch = f"{branch}-2"
        _run(["git", "checkout", "-b", branch])

        # Apply patches
        for patch in patches:
            full_path = cfg.REPO_DIR / patch.relative_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(patch.new_content, encoding="utf-8")
            logger.info("Patched: %s", patch.relative_path)

        # Stage changed files only
        _run(["git", "add", "--"] + [p.relative_path for p in patches])

        # Commit
        _run(["git", "commit", "-m", commit_message])
        short_sha = _run(["git", "rev-parse", "--short", "HEAD"])

        # Diff stat for notification
        diff_stat = _run(["git", "diff", "--stat", f"master...{branch}"])

        # Go back to master
        _run(["git", "checkout", "master"])

        return CommitResult(
            branch=branch,
            commit=short_sha,
            diff=diff_stat,
            success=True,
        )

    except Exception as exc:
        logger.error("git_ops error: %s", exc)
        # Try to go back to master on failure
        try:
            _run(["git", "checkout", "master"])
        except Exception:
            pass
        return CommitResult(
            branch=branch,
            commit="",
            diff="",
            success=False,
            error=str(exc),
        )
