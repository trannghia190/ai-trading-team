# LangChain Trading Team

A multi-agent Vietnamese-stock trading advisor built with **LangGraph**, **LangChain**, and **deepagents**. The team orchestrates a Leader, a bull/bear debate room, and dedicated analyst agents over a routed MCP tool layer (stock data, memory, web search) to produce structured analyses, debate-driven strategy briefs, and on-demand reports.

The package is one node in a larger workspace (`ag-agentchat`) and is invoked as a module from the workspace root.

---

## Features

- **Multi-agent LangGraph workflow** with strict node sequencing and bounded retry/recursion loops
- **Vietnamese-stock focus** via a local `vnstock`-backed MCP server (`mcp/stock_mcp`)
- **Three-stage memory** — auto-injected `AGENTS.md`, on-demand skills, ticker/session notes, plus an external read-only memory MCP
- **Pluggable channels** — Telegram bot and a FastAPI/SSE HTTP server share one graph instance
- **Tool-trace data-quality audit** — `analysis_verify` catches missing macro/technical data before debate
- **Bull ↔ bear debate loop** with arbitration, plus a leader revision loop over strategy synthesis
- **Self-improvement subsystem** — a background scheduler that proposes and applies code/skill fixes, gated by user approval
- **Commit-safe config** — three-tier precedence: safe defaults → local-only `settings_local.py` → env vars

---

## Requirements

- Python 3.11+
- A reachable LLM endpoint compatible with the LangChain `ChatOpenAI` interface
- A running `mcp/stock_mcp/stock_mcp_server.py` (or equivalent — see `config/settings_local.example.py`)
- Optional: a Telegram bot token if you want the Telegram channel
- Optional: an MCP memory server URL for the `memory_search` / `memory_list` tools

---

## Installation

The package is meant to be cloned alongside its siblings in the `ag-agentchat` workspace; relative imports and the default `MCP_STOCK_SCRIPT` path assume that structure.

```bash
# from the workspace root, e.g. /Users/trannghia/workspace/ag-agentchat
git clone <your-fork-url> langgraph/langchain_trading_team
cd langgraph/langchain_trading_team

# create and activate a virtualenv
python -m venv .venv
source .venv/bin/activate

# install dependencies (add the toolchain you actually use)
pip install -U langgraph langchain langchain-openai deepagents python-telegram-bot fastapi uvicorn httpx python-dotenv
```

---

## Configuration

Config is loaded with this precedence (last wins):

1. safe defaults committed in `config/settings.py`
2. local-only overrides from `config/settings_local.py` (auto-loaded when present, **gitignored**)
3. environment variables (`TRADING_*`, `MCP_*`) for CI/CD, Docker, and production

### First-time local setup

```bash
cp config/settings_local.example.py config/settings_local.py
# then edit config/settings_local.py and fill in:
#   API_KEY, TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS,
#   MCP_MEMORY_URL, MCP_STOCK_SCRIPT, etc.
```

`settings.py` must never contain real secrets. The example file ships with empty placeholders so it is safe to commit.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `TRADING_API_KEY` | _empty_ | LLM API key |
| `TRADING_MODEL` | _set in `config/settings_local.py`_ | Model name |
| `TRADING_BASE_URL` | `http://localhost:20128/v1` | OpenAI-compatible base URL |
| `TRADING_TELEGRAM_TOKEN` | _empty_ | Telegram bot token |
| `TRADING_ALLOWED_USER_IDS` | _empty_ | Comma-separated Telegram user IDs |
| `TRADING_CHANNEL` | `telegram` | One of `telegram`, `api`, `all` |
| `TRADING_RESPONSE_LANGUAGE` | `Vietnamese` | `Vietnamese` or `English` |
| `TRADING_API_HOST` / `TRADING_API_PORT` | `0.0.0.0` / `8000` | FastAPI bind |
| `TRADING_API_SERVER_KEY` | _empty_ | Bearer token; empty = auth disabled |
| `TRADING_LOG_LEVEL` | `INFO` | Standard log level |
| `MCP_MEMORY_URL` | _empty_ | Memory MCP streamable-HTTP URL |
| `MCP_RIVAL_SEARCH_URL` | `https://RivalSearchMCP.fastmcp.app/mcp` | Web search MCP |
| `MCP_STOCK_SCRIPT` | `mcp/stock_mcp/stock_mcp_server.py` | Stock MCP stdio script |
| `TRADING_<AGENT>_MODEL` / `_API_KEY` / `_BASE_URL` | inherits global | Per-agent LLM override (agents: `LEADER`, `LEAD_ANALYSIS`, `LEAD_STRATEGY`, `MACRO`, `TECHNICAL`, `BULL`, `BEAR`) |

### Choosing an LLM

Any OpenAI-compatible chat model that supports tool calling and a context window of roughly 32k+ tokens works. The workflow expects the model to:

- follow structured-output instructions (the leader uses `[FLOW:...]` / `[VOTE:...]` tags that the router parses)
- handle multi-step tool calling reliably (each analyst issues several sequential tool calls per turn)
- respond well to long system prompts with bilingual instructions (Vietnamese + English metadata)

The per-agent override pattern (`TRADING_<AGENT>_*`) lets you route cheap/fast models to simpler roles (e.g. macro/technical analysts) and a stronger model to the leader or strategy synthesis.

---

## Running

The package must be invoked **from the workspace root** so its relative imports and the default `MCP_STOCK_SCRIPT` path resolve correctly.

```bash
# from /Users/trannghia/workspace/ag-agentchat
python -m langgraph.langchain_trading_team.main                 # default channel (settings.DEFAULT_CHANNEL)
python -m langgraph.langchain_trading_team.main --channel api   # FastAPI + SSE only
python -m langgraph.langchain_trading_team.main --channel telegram
python -m langgraph.langchain_trading_team.main --channel all
```

Smoke-test the API channel:

```bash
curl -N -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"Phân tích HPG hôm nay","session_id":"test-1"}'
```

---

## Architecture

### Workflow (workflow/graph.py)

`TradingTeamGraph` is a `StateGraph` over `TradingState`. One graph instance is shared across all sessions and channels.

```
START → leader_intake
      → lead_analysis → analysis_verify ⇄ lead_analysis
      → bull_argument ⇄ bear_argument → arbitration       (debate loop ≤ MAX_DEBATE_ROUNDS)
      → strategy_synthesis → leader_review                 (revision loop ≤ MAX_SYNTHESIS_ROUNDS)
      → memory_save → END
```

Key invariants:

- `flow_type` (`full` | `analysis_only` | `strategy_only` | `direct`) is decided at intake from the leader's `[FLOW:...]` tag.
- `analysis_verify` audits captured tool traces; on `[DATA_ISSUES]` it loops back to `lead_analysis`. After `MAX_ANALYSIS_VERIFY_RETRIES` it injects a warning header and proceeds.
- Inside `lead_analysis`, `MacroAnalyst` and `TechnicalAnalyst` run concurrently via `asyncio.gather`. The same node then performs routing, optional gap-fill, and final synthesis brief.
- `_invoke` / `_invoke_with_trace` apply `asyncio.wait_for(NODE_TIMEOUT)` plus a transient-error retry policy. Per-call `run_id`s are stamped into a `ContextVar` so tool-call logs can be joined back to the node invocation.

### Memory (tool/memory_layer.py)

All agents run inside `deepagents.create_deep_agent` with a `CompositeBackend` that mounts `/memory/` to `memory/`. There are four tiers, and they are not interchangeable:

1. **Auto-injected AGENTS.md files** — bounded per-agent allowlist.
2. **Skills** — `memory/skills/{shared,analysis,strategy}/<name>/SKILL.md`; injected as `name + description`, full instructions pulled on demand.
3. **On-demand files** — `memory/tickers/<TICKER>.md`, `memory/sessions/<DATE>_<slug>.md`.
4. **External MCP memory** — `memory_search` / `memory_list` only. All writes go to local files; never add MCP write tools to any preset.

### MCP tool layer (tool/mcp_tools.py)

`ToolRegistry.load()` connects once to each MCP server, enumerates tools, and exposes them as lazily reconnecting `StructuredTool` wrappers. Three presets are consumed by the graph factories:

- `get_analysis_tools()` → stock + search
- `get_strategy_tools()` → stock + search + read-only memory
- `get_leader_tools()` → memory only

### Channels

- `channel/telegram_channel.py` — long-polling Telegram bot with `/reset`, `/status`, and self-improvement commands (`/si_status`, `/si_approve`, `/si_reject`, `/si_run`, `/si_compress_skills`). Allowed users are gated by `ALLOWED_USER_IDS`.
- `channel/api_channel.py` — FastAPI + SSE; routes `/chat`, `/reset`, `/status`, `/sessions`. Bearer-token auth via `TRADING_API_SERVER_KEY` (empty = auth disabled).

### Self-improvement subsystem (self_improvement/)

Started by `main.py` via `start_scheduler_async()`. APScheduler fires `run_once()` every `SCHEDULE_HOURS` (default 6h):

1. Skip if `memory/self_improvement/pending.json` exists (a previous fix is awaiting approval).
2. `collector.collect()` reads recent log tails + new session reviews.
3. `analyzer.run_analysis()` may produce a fix branch (prefix `si/fix-`) committed by `git_ops`.
4. If a branch was created, `set_pending` records it; the user must approve/reject via Telegram before the next run is allowed.

---

## Project Layout

```
langchain_trading_team/
├── main.py                      # entry point
├── config/
│   ├── settings.py              # commit-safe defaults + loader
│   ├── settings_local.py        # gitignored, auto-loaded
│   ├── settings_local.example.py
│   └── logging_config.py
├── agent/                       # Markdown system prompts + loader
├── workflow/graph.py            # LangGraph state machine
├── tool/                        # MCP registry, memory layer
├── channel/                     # telegram + api entrypoints
├── memory/                      # AGENTS.md, skills, runtime artifacts
├── self_improvement/            # background scheduler + analyzer
├── reports/                     # generated reports (gitignored)
└── logs/                        # runtime logs (gitignored)
```

---

## Logging

- `logs/trading_team.log` — workflow events
- `logs/tools_debug.log` — tool calls, joined back to node invocations via `run_id`

---

## Troubleshooting

- **`MCP_STOCK_SCRIPT` not found** — the default is repo-relative (`mcp/stock_mcp/stock_mcp_server.py`). The package must be run from the workspace root, or set `MCP_STOCK_SCRIPT` to an absolute path in `settings_local.py` / env.
- **No response from Telegram** — confirm `TELEGRAM_BOT_TOKEN` is set and `ALLOWED_USER_IDS` includes your numeric ID.
- **Empty debate / synthesis** — usually means the analysis room produced no data; check `analysis_verify` warnings in `logs/trading_team.log`.
- **Self-improvement skip-loop** — delete `memory/self_improvement/pending.json` only if you intentionally want to discard a queued fix.

---

## License

See [`LICENSE`](./LICENSE).