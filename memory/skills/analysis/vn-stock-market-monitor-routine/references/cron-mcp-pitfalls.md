# Cronjob MCP Pitfalls

## The `enabled_toolsets` Trap

When configuring a cron job that relies on MCP tools (like `stock_mcp`), **DO NOT** restrict `enabled_toolsets` to `["web"]` or other narrow subsets unless you explicitly want to disable the MCP tools.

**Symptom:**
The cron job runs successfully but produces a degraded report, heavily relying on public web searches (`web_search`) instead of structured MCP data (`get_price_data`, `get_finpath_market_breadth`, etc.), ignoring the primary data source instructions.

**Root Cause:**
MCP tools are not always injected if `enabled_toolsets` strictly filters for other categories. The agent in the cron session cannot see the MCP tools, so it silently falls back to whatever tools are available (e.g., web search) to fulfill the prompt.

**Fix:**
Leave `enabled_toolsets` empty `[]` (allowing default tool loading) to ensure the cron agent has full access to the necessary MCP tools for market data generation.