# Cron Prompt — Open Report

Use this prompt when creating a VN stocks open-session cron report.

## Self-contained prompt

Produce a Vietnam stock market open report for today using stock_mcp-first data and the monitor framework already defined by this skill family.

Required behavior:
- Use structured MCP market data first.
- Do not rely on stale portfolio assumptions.
- If runtime portfolio/watchlist state is unavailable, produce a market-only report and explicitly say portfolio state was not provided.
- Do not force buy ideas if market quality does not support them.
- `0 focus buy now` is a valid conclusion.

Required analysis order:
1. Market setup
2. Breadth and sector rotation
3. Foreign flow
4. Portfolio/watchlist readiness if runtime state exists
5. News/catalysts only if materially relevant
6. Risk/action synthesis

Required output blocks:
1. Open report headline
2. Market summary block
   - Regime verdict
   - Emotion verdict
   - Breadth verdict
   - Foreign-flow verdict
   - Sector-rotation verdict
   - Leadership-quality verdict
3. Overnight / pre-open context
4. Watchpoints for the session
5. Portfolio/watchlist readiness
6. Action table
7. What not to do today

Action-table rules:
- Use only canonical actions.
- Respect liquidity floor + scoring/penalty matrix.
- Illiquid UPCOM/penny spikes are not valid leadership.
- If no name passes validation, say `0 focus buy now`.

Tool fallback rules:
- If one leaderboard tool fails, continue with breadth + sector + foreign buy/sell + any remaining leadership evidence.
- If top-value leadership is unclear because of tool failure, say so explicitly instead of hallucinating.

Style:
- concise, decisive, no filler
- emphasize readiness, no-chase discipline, and key risk flags
