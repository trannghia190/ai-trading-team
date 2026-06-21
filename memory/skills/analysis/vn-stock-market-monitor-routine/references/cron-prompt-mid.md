# Cron Prompt — Mid-Session Report

Use this prompt when creating a VN stocks mid-session cron report.

## Self-contained prompt

Produce a Vietnam stock market mid-session report for today using stock_mcp-first data and the monitor framework already defined by this skill family.

Required behavior:
- Focus on intraday health without overreacting to one swing.
- Use structured MCP market data first.
- If runtime portfolio/watchlist state is unavailable, produce a market-only report and say so explicitly.
- Do not treat a green/red price move alone as sufficient evidence for a trade verdict.

Required analysis order:
1. Market overview
2. Breadth and sector rotation
3. Foreign flow
4. Portfolio/watchlist snapshot if runtime state exists
5. News/catalysts only if materially relevant
6. Actions into the close

Required output blocks:
1. Mid-session headline
2. Market summary block
   - Regime verdict
   - Emotion verdict
   - Breadth verdict
   - Foreign-flow verdict
   - Sector-rotation verdict
   - Leadership-quality verdict
3. Headline move vs breadth reality
4. Liquidity pace and sector rotation
5. Portfolio/watchlist snapshot
6. Action table into the close
7. What not to do before ATC

Action-table rules:
- Use canonical actions only.
- Respect liquidity floor + scoring/penalty matrix.
- If breadth is weak and foreign pressure is heavy, downgrade entry-new verdicts by at least one level.
- If no candidate survives validation, say `0 focus buy now`.

Tool fallback rules:
- If one leaderboard tool fails, keep the report alive using breadth, sector overview, foreign flow, price board, and remaining leadership clues.

Style:
- concise, decisive
- emphasize noise control, close confirmation, and no-chase discipline
