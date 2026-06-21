"""
Self-Improvement configuration.

Edit this file directly to change settings.
"""
from __future__ import annotations

from pathlib import Path
from config import settings as _s

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PKG_ROOT    = Path(__file__).parent.parent  # langchain_trading_team/

REPO_DIR     = _PKG_ROOT
MEMORY_DIR   = _PKG_ROOT / "memory" / "self_improvement"
LOG_DIR      = _PKG_ROOT / "logs"
SESSIONS_DIR = _PKG_ROOT / "memory" / "sessions"
REPORTS_DIR  = _PKG_ROOT / "reports"

PENDING_FILE = MEMORY_DIR / "pending.json"

# ---------------------------------------------------------------------------
# LLM — shares model with trading team; change to use a separate model
# ---------------------------------------------------------------------------
CODING_MODEL    = "default-combo"
CODING_API_KEY  = _s.API_KEY
CODING_BASE_URL = _s.BASE_URL

# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
SCHEDULE_HOURS   = 6       # run every N hours
SCHEDULE_ENABLED = True

# ---------------------------------------------------------------------------
# Analysis limits
# ---------------------------------------------------------------------------
LOG_TAIL_LINES    = 500    # number of tail log lines read per run
MAX_SESSIONS      = 5      # number of most recent session files to read per run
MAX_FILES_PER_FIX     = None  # max files to patch per run; None = unlimited
MAX_REVIEW_ITERATIONS = 10     # max review→fix loop iterations before giving up

# ---------------------------------------------------------------------------
# SI timeouts & retries
# ---------------------------------------------------------------------------
SI_NODE_TIMEOUT       = 10 * 60  # 10 min: per agent.ainvoke() call
SI_RUN_TIMEOUT        = 45 * 60  # 45 min: total run_analysis() cap

SI_LLM_RETRIES        = 2        # retries on LLM timeout / transient error
SI_LLM_RETRY_DELAY    = 15       # seconds to wait between LLM retries

# Shell read-only tool (run_shell_readonly): retry with doubled timeout each time
# e.g. 30s → 60s → 120s
SI_SHELL_READ_TIMEOUT = 30       # initial timeout (s)
SI_SHELL_READ_RETRIES = 2        # retries (each doubles the timeout)

# ---------------------------------------------------------------------------
# Telegram notification
# ---------------------------------------------------------------------------
NOTIFY_CHAT_ID   = _s.ALLOWED_USER_IDS[0]
NOTIFY_BOT_TOKEN = _s.TELEGRAM_BOT_TOKEN

# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------
GIT_AUTHOR_NAME  = "SelfImprovement Bot"
GIT_AUTHOR_EMAIL = "bot@trading-team.local"
BRANCH_PREFIX    = "si/fix-"
