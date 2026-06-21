# Cron Prompt — Close Report

Use this prompt when creating a VN stocks end-of-session cron report.

## Self-contained prompt

Produce a Vietnam stock market close report for today using stock_mcp-first data and the monitor framework already defined by this skill family.

Required behavior:
- Produce the most decision-useful daily synthesis, not a raw dashboard.
- Use structured MCP market data first.
- If runtime portfolio/watchlist state is unavailable, produce a market-only report and say so explicitly.
- Interpret foreign flow, breadth, and sector rotation; do not just recite numbers.

Required analysis order:
1. Final market close
2. Breadth and sector rotation
3. Foreign flow
4. Portfolio/watchlist close snapshot if runtime state exists
5. News/catalysts only if materially relevant
6. Next-session action synthesis

Required output blocks:
1. Close report headline
2. Market summary block
   - Regime verdict
   - Emotion verdict
   - Breadth verdict
   - Foreign-flow verdict
   - Sector-rotation verdict
   - Leadership-quality verdict
3. Final market close synthesis
4. Sector winners / losers and why they matter
5. Portfolio/watchlist close snapshot
6. Next-session action table
7. What not to do tomorrow if this regime persists

Action-table rules:
- Use canonical actions only.
- Respect liquidity floor + scoring/penalty matrix.
- `0 focus buy now` is valid when leadership is narrow, foreign pressure is heavy, or candidates fail validation.
- Distinguish clearly between names that are holdable and names that are buyable.

Tool fallback rules:
- If `top_value` or another leaderboard tool fails, say leadership confirmation is partial and continue using breadth, sector, foreign buy/sell, price board, and available volume-surge/top-gainer evidence.

Style:
- concise, decisive
- prioritize next-session actionability over narration
