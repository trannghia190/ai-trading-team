# MCP connectivity and rate-limit handling for VN stock setups

## Why this reference exists
Session lesson: a live `stock_mcp` server can be healthy while the current agent session still has stale MCP tool binding. Also, actionable stock recommendations should not proceed when current price/close is unverified.

## Durable handling pattern

### 1. Distinguish three states
- **Server down/unreachable**: MCP CLI/tool test fails.
- **Server up, session stale**: `python stock_mcp_server.py # or check logs <name>` passes, but in-session tool calls still say not connected.
- **Data degraded**: some layers missing (e.g. current price missing, technical timeout, flow unavailable).

### 2. Required user-facing disclosure
Before analysis, state briefly:
- MCP status: OK / degraded / disconnected
- Which layers are missing: price, technical, events, foreign flow
- Whether fallback is being used
- Confidence impact

### 3. Recommendation discipline
- No current/closing price confirmation -> no actionable BUY/SELL wording for that symbol.
- Mark that symbol WATCH / NO ACTION until price is verified.
- Do not present entry/stop/target as if they are live-executable when price is stale.

### 4. Reconnect logic after outage
If MCP was restarted:
1. Test MCP connectivity at the Trading Team/CLI level.
2. Then run one minimal real tool call to verify the current session is actually reconnected.
3. Only after that resume broader analysis.

### 5. Rate-limit discipline
If MCP has tight limits (e.g. 20 req/min):
- Prefer grouped requests (multi-symbol price call)
- Avoid parallel fan-out unless necessary
- Use the minimum viable data bundle first
- Expand only after the first call succeeds

## Example minimal recovery sequence
1. Verify MCP status
2. Run one grouped price request for watchlist symbols
3. If success, run technicals only for highest-priority names
4. Stop and report if the session still shows stale binding
