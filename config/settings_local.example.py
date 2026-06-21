"""
Local-only overrides for LangChain Trading Team.

Copy this file to `settings_local.py` and fill in the values you want for
local development. The real `settings_local.py` is gitignored.
"""

# ==============================================================================
# LLM
# ==============================================================================
API_KEY = ""
MODEL_NAME = "minimax/MiniMax-M2.5"
BASE_URL = "http://localhost:20128/v1"

# ==============================================================================
# TELEGRAM
# ==============================================================================
TELEGRAM_BOT_TOKEN = ""
ALLOWED_USER_IDS: list[int] = []

# ==============================================================================
# MCP ENDPOINTS
# ==============================================================================
MCP_MEMORY_URL = ""
MCP_STOCK_SCRIPT = "/absolute/path/to/ag-agentchat/mcp/stock_mcp/stock_mcp_server.py"

# ==============================================================================
# API CHANNEL
# ==============================================================================
API_SERVER_KEY = ""
