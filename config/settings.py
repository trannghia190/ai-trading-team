"""
LangChain Trading Team — Central configuration.

`settings.py` is the committed source of truth for available settings and safe
fallback defaults. For local-only secrets or machine-specific values, create
`config/settings_local.py` (gitignored). Environment variables remain the final
runtime override layer for CI/CD, Docker, and production.
"""
import importlib
import os
from datetime import date


def _load_local_overrides() -> None:
    """Load uppercase overrides from settings_local.py when present."""
    try:
        module = importlib.import_module(f"{__package__}.settings_local")
    except ModuleNotFoundError:
        return

    for name in dir(module):
        if name.isupper():
            globals()[name] = getattr(module, name)


# ==============================================================================
# LLM — global defaults (used by any agent that doesn't override)
# ==============================================================================
API_KEY = ""
MODEL_NAME = "minimax/MiniMax-M2.5"
BASE_URL = "http://localhost:20128/v1"

# ==============================================================================
# TELEGRAM — single bot
# ==============================================================================
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_MAX_LENGTH = 4000
MESSAGE_DELAY = 0.5
ALLOWED_USER_IDS: list[int] = []

# ==============================================================================
# MCP ENDPOINTS
# ==============================================================================
MCP_MEMORY_URL = ""
MCP_RIVAL_SEARCH_URL = "https://RivalSearchMCP.fastmcp.app/mcp"
MCP_STOCK_SCRIPT = "mcp/stock_mcp/stock_mcp_server.py"

# ==============================================================================
# CHANNEL
# Default startup channel: "telegram", "api", "all"
# ==============================================================================
DEFAULT_CHANNEL = "telegram"

# ==============================================================================
# RESPONSE LANGUAGE
# Agents will respond in this language.
# Override via env: TRADING_RESPONSE_LANGUAGE=English
# ==============================================================================
RESPONSE_LANGUAGE = "Vietnamese"

# ==============================================================================
# API CHANNEL (FastAPI / SSE)
# ==============================================================================
API_HOST = "0.0.0.0"
API_PORT = 8000
API_SERVER_KEY = ""  # bearer token; empty = disable auth (local dev)

# ==============================================================================
# LOGGING
# ==============================================================================
LOG_LEVEL = "INFO"

# Optional local file override before deploy/runtime env vars.
_load_local_overrides()

# env override
API_KEY = os.getenv("TRADING_API_KEY", API_KEY)
MODEL_NAME = os.getenv("TRADING_MODEL", MODEL_NAME)
BASE_URL = os.getenv("TRADING_BASE_URL", BASE_URL)
TELEGRAM_BOT_TOKEN = os.getenv("TRADING_TELEGRAM_TOKEN", TELEGRAM_BOT_TOKEN)
MCP_MEMORY_URL = os.getenv("MCP_MEMORY_URL", MCP_MEMORY_URL)
MCP_RIVAL_SEARCH_URL = os.getenv("MCP_RIVAL_SEARCH_URL", MCP_RIVAL_SEARCH_URL)
MCP_STOCK_SCRIPT = os.getenv("MCP_STOCK_SCRIPT", MCP_STOCK_SCRIPT)
DEFAULT_CHANNEL = os.getenv("TRADING_CHANNEL", DEFAULT_CHANNEL)
RESPONSE_LANGUAGE = os.getenv("TRADING_RESPONSE_LANGUAGE", RESPONSE_LANGUAGE)
API_HOST = os.getenv("TRADING_API_HOST", API_HOST)
API_PORT = int(os.getenv("TRADING_API_PORT", str(API_PORT)))
API_SERVER_KEY = os.getenv("TRADING_API_SERVER_KEY", API_SERVER_KEY)
LOG_LEVEL = os.getenv("TRADING_LOG_LEVEL", LOG_LEVEL)

# ==============================================================================
# Per-agent LLM config — each agent inherits global defaults above.
# To use a different model per agent, edit the dicts below.
# Env override: TRADING_MACRO_MODEL, TRADING_MACRO_BASE_URL, TRADING_MACRO_API_KEY
# Agents: LEADER, LEAD_ANALYSIS, MACRO, TECHNICAL, BULL, BEAR
# ==============================================================================

def _agent_cfg(prefix: str, model=None, api_key=None, base_url=None) -> dict[str, str]:
    """Return {model, api_key, base_url} for one agent, inheriting globals."""
    return {
        "model":    os.getenv(f"TRADING_{prefix}_MODEL",    model    or MODEL_NAME),
        "api_key":  os.getenv(f"TRADING_{prefix}_API_KEY",  api_key  or API_KEY),
        "base_url": os.getenv(f"TRADING_{prefix}_BASE_URL", base_url or BASE_URL),
    }

LEADER_LLM_CFG        = _agent_cfg("LEADER")
LEAD_ANALYSIS_LLM_CFG = _agent_cfg("LEAD_ANALYSIS")
LEAD_STRATEGY_LLM_CFG = _agent_cfg("LEAD_STRATEGY")
MACRO_LLM_CFG         = _agent_cfg("MACRO")
TECHNICAL_LLM_CFG     = _agent_cfg("TECHNICAL")
BULL_LLM_CFG          = _agent_cfg("BULL")
BEAR_LLM_CFG          = _agent_cfg("BEAR")

# ==============================================================================
# WORKFLOW
# ==============================================================================
MAX_DEBATE_ROUNDS    = 10
MAX_SYNTHESIS_ROUNDS = 3   # max Leader→Strategy revision loops before accepting draft
NODE_TIMEOUT         = 5 * 60  # seconds — per-agent-call timeout; prevents hung sessions
SESSION_TIMEOUT      = 30 * 60  # seconds

# Retry on transient LLM errors (timeout / connection / rate-limit)
NODE_LLM_RETRIES     = 2        # number of retries after first failure
NODE_LLM_RETRY_DELAY = 15       # seconds to wait between retries

MAX_ANALYSIS_VERIFY_RETRIES = 1  # max re-analysis cycles when data verification fails

# Intake auto-demote: when leader classifies a request as `full` / `analysis_only`
# but the directive text contains no VN ticker (3-5 uppercase letters) AND no
# analysis verb (phân tích / đánh giá / nhận định / chiến lược / so sánh / ...),
# demote to `direct` and skip the analysis/strategy rooms. Safety net against
# leader over-routing simple queries (greetings, definitions, status checks).
# Default OFF: leader prompt already has clear [FLOW:direct] guard, and the
# heuristic over-demotes valid screening/sector questions like
# "có cổ phiếu tiêu biểu nào đã đi vào vùng fair price chưa?" (no ticker, no
# verb in the fixed list, but clearly needs analysis room).
# Set to True to re-enable the heuristic; can also flip via env below.
INTAKE_AUTO_DEMOTE = False
INTAKE_AUTO_DEMOTE = os.getenv("TRADING_INTAKE_AUTO_DEMOTE", str(INTAKE_AUTO_DEMOTE)).lower() in ("1", "true", "yes")

# Directory for user-requested reports ("create report", "save file", ...)
REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # langchain_trading_team/
    "reports",
)

# ==============================================================================
# RESPONSE LANGUAGE
# Agents will respond in this language.
# Override via env: TRADING_RESPONSE_LANGUAGE=English
# ==============================================================================

_LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "Vietnamese": (
        "🚨 RESPOND IN VIETNAMESE ONLY. "
        "Do not use English or any other language in your response."
    ),
    "English": (
        "🚨 RESPOND IN ENGLISH ONLY. "
        "Do not use Vietnamese or any other language in your response."
    ),
}

RESPONSE_LANGUAGE_INSTRUCTION: str = _LANGUAGE_INSTRUCTIONS.get(
    RESPONSE_LANGUAGE,
    f"🚨 RESPOND IN {RESPONSE_LANGUAGE.upper()} ONLY.",
)

LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # langchain_trading_team/
    "logs",
)

# ==============================================================================
# CURRENT DATE
# ==============================================================================
CURRENT_DATE  = date.today().strftime("%d/%m/%Y")
CURRENT_MONTH = date.today().strftime("%m")
CURRENT_YEAR  = date.today().strftime("%Y")

