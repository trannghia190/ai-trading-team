# Cron Prompt — Weekly Digest

Use this prompt when creating a weekly digest cron job for VN stocks.

## Self-contained prompt

Produce a Vietnam stock market weekly digest using stock_mcp-first data and the monitor framework already defined by this skill family.

Required behavior:
- Zoom out from daily noise and update the medium-term thesis.
- Use structured MCP market data first.
- If runtime portfolio/watchlist state is unavailable, produce a market-only digest and say so explicitly.
- Focus on what changed materially over the week.

Required analysis order:
1. Weekly market regime and breadth
2. Sector rotation and money-cycle
3. Foreign flow / ETF / ownership context if available
4. Portfolio/watchlist implications if runtime state exists
5. Key catalysts for next 1-4 weeks
6. Weekly action synthesis

Required output blocks:
1. Weekly digest headline
2. Weekly market summary block
   - Regime verdict
   - Emotion verdict
   - Breadth verdict
   - Foreign-flow verdict
   - Sector-rotation verdict
   - Leadership-quality verdict
3. What improved this week
4. What deteriorated this week
5. Key catalysts ahead
6. Portfolio/watchlist implications
7. Weekly action table
8. What not to do next week

Action-table rules:
- Use canonical actions only.
- Respect liquidity floor + scoring/penalty matrix when naming focus candidates.
- Do not confuse a one-week bounce in illiquid names with medium-term opportunity.
- `0 focus buy now` is valid if the weekly evidence is too weak or too crowded.

Tool fallback rules:
- If some leaderboard/history tools fail, continue with the best available breadth, sector, foreign-flow, and news/event evidence, and state where evidence is partial.

Style:
- concise, high-signal, medium-term oriented
- prioritize thesis changes, rotation, and next-week actionability
