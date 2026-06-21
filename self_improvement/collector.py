"""
Collector — gather raw evidence for analysis.

Reads:
  - logs/trading_team.log   : last N lines, filtered for ERROR/WARNING
  - memory/sessions/*.md    : newest M session files not yet reviewed
  - reports/*.md            : (optional) newest report titles for context

Returns a CollectedEvidence dataclass — short-term, lives only in memory.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import config as cfg

logger = logging.getLogger("trading_team.si.collector")

# ---------------------------------------------------------------------------
# State tracking — which sessions have already been reviewed
# ---------------------------------------------------------------------------

_REVIEWED_FILE = cfg.MEMORY_DIR / "reviewed_sessions.json"


def _load_reviewed() -> set[str]:
    if not _REVIEWED_FILE.exists():
        return set()
    try:
        return set(json.loads(_REVIEWED_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def mark_sessions_reviewed(names: list[str]) -> None:
    cfg.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    reviewed = _load_reviewed()
    reviewed.update(names)
    _REVIEWED_FILE.write_text(
        json.dumps(sorted(reviewed), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Log bookmark — track last processed log line by timestamp
# ---------------------------------------------------------------------------

_LOG_BOOKMARK_FILE = cfg.MEMORY_DIR / "log_bookmark.json"

_TS_PATTERN = re.compile(r'"ts"\s*:\s*"([^"]+)"')


def _load_log_bookmark() -> str | None:
    """Return ISO timestamp string of last processed log line, or None."""
    if not _LOG_BOOKMARK_FILE.exists():
        return None
    try:
        data = json.loads(_LOG_BOOKMARK_FILE.read_text(encoding="utf-8"))
        return data.get("last_ts")
    except Exception:
        return None


def _save_log_bookmark(last_ts: str) -> None:
    cfg.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    _LOG_BOOKMARK_FILE.write_text(
        json.dumps({"last_ts": last_ts}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Log collection
# ---------------------------------------------------------------------------

_LOG_PATTERN = re.compile(r"\b(ERROR|WARNING|CRITICAL|Exception|Traceback)\b")


def _collect_logs() -> str:
    log_file = cfg.LOG_DIR / "trading_team.log"
    if not log_file.exists():
        return ""
    lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()

    # Filter to only lines after the last processed timestamp
    last_ts = _load_log_bookmark()
    if last_ts:
        new_lines = []
        found_bookmark = False
        for line in lines:
            if not found_bookmark:
                m = _TS_PATTERN.search(line)
                if m and m.group(1) > last_ts:
                    found_bookmark = True
                    new_lines.append(line)
            else:
                new_lines.append(line)
        lines = new_lines if new_lines else []
    else:
        # First run — take last N lines as seed
        lines = lines[-cfg.LOG_TAIL_LINES:]

    # Filter to meaningful lines only
    relevant = [l for l in lines if _LOG_PATTERN.search(l)]
    if not relevant:
        return ""

    # Update bookmark to latest timestamp seen in this batch
    for line in reversed(lines):
        m = _TS_PATTERN.search(line)
        if m:
            _save_log_bookmark(m.group(1))
            break

    return "\n".join(relevant)


# ---------------------------------------------------------------------------
# Session collection
# ---------------------------------------------------------------------------

def _collect_sessions() -> list[tuple[str, str]]:
    """Return list of (filename, content) for newest unreviewed sessions."""
    if not cfg.SESSIONS_DIR.exists():
        return []
    reviewed = _load_reviewed()
    candidates = sorted(
        [p for p in cfg.SESSIONS_DIR.glob("*.md") if p.name not in reviewed],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    result = []
    for path in candidates[: cfg.MAX_SESSIONS]:
        try:
            content = path.read_text(encoding="utf-8")
            result.append((path.name, content))
        except Exception as e:
            logger.warning("Could not read session %s: %s", path.name, e)
    return result


# ---------------------------------------------------------------------------
# Evidence container
# ---------------------------------------------------------------------------

@dataclass
class CollectedEvidence:
    log_excerpt:   str               = ""          # filtered ERROR/WARNING lines
    sessions:      list[tuple[str, str]] = field(default_factory=list)  # (name, content)
    collected_at:  str               = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def is_empty(self) -> bool:
        return not self.log_excerpt and not self.sessions

    def summary(self) -> str:
        parts = []
        if self.log_excerpt:
            line_count = self.log_excerpt.count("\n") + 1
            parts.append(f"{line_count} error/warning log lines")
        if self.sessions:
            names = ", ".join(n for n, _ in self.sessions)
            parts.append(f"{len(self.sessions)} session(s): {names}")
        return "; ".join(parts) if parts else "nothing collected"


def collect() -> CollectedEvidence:
    """Main entry point — gather all evidence for this run."""
    cfg.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    ev = CollectedEvidence(
        log_excerpt=_collect_logs(),
        sessions=_collect_sessions(),
    )
    logger.info("Collector: %s", ev.summary())
    return ev
