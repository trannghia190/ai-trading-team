# Cron Master Prompt Pack

## Purpose

This file bundles the full prompt pack for running the routine market monitor through cron in a consistent and maintainable way.

It helps by:
- removing the need to remember each standalone prompt
- providing suggested schedules
- providing suggested `enabled_toolsets`
- including an operational checklist before enabling live cron jobs

## Recommended skills to attach

When creating a cron job for routine reports, attach the skills in this order:
1. `vn-stock-market-monitor-routine`
2. `vn-stock-market-monitor-mcp`

Why:
- the routine skill owns the output contract and orchestration
- the market-monitor skill owns regime, breadth, and shortlist analysis logic

## Recommended toolsets

Suggested default:
- `enabled_toolsets: []` if you want the system default tool access

More optimized for routine market reports:
- `enabled_toolsets: ["web"]`

Notes:
- most market data is available at the MCP tool layer, so terminal and file access are usually unnecessary for reporting only
- add `file` only if the routine should later read local state files
- add `terminal` only if there is a dedicated script or pre-processor

## Suggested schedules

### Open report
- Suggestion: `0 8 * * 1-5`
- Meaning: 08:00 on working days
- You can move it earlier or later depending on how the report is used

### Mid-session report
- Suggestion: `0 11 * * 1-5`
- Meaning: late morning, with enough data to read breadth and tape without being too close to lunch break

### Close report
- Suggestion: `10 15 * * 1-5`
- Meaning: shortly after ATC so close data is more stable

### Weekly digest
- Suggestion: `0 9 * * 6`
- Meaning: Saturday morning to summarize the trading week

## Delivery suggestion

If the user has not asked for another destination:
- leave `deliver` at its default and send back to the origin or current chat

If the result should only be saved locally:
- use `deliver: local`

## Operational checklist before creating cron

- [ ] Confirmed that the report does not need to ask the user questions at runtime
- [ ] Prompt is self-contained
- [ ] Market-only mode is acceptable if runtime portfolio state is unavailable
- [ ] There is a fallback if a leaderboard tool fails
- [ ] `0 focus buy now` is accepted as a valid conclusion
- [ ] The routine is not forced to produce buy ideas every session

## Prompt 1 - Open report

Source file:
- `references/cron-prompt-open.md`

Recommended cron create parameters:
- name: `vn-stock-open-report`
- schedule: `0 8 * * 1-5`
- skills:
  - `vn-stock-market-monitor-routine`
  - `vn-stock-market-monitor-mcp`
- enabled_toolsets:
  - `web`

Prompt body:

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

## Prompt 2 - Mid-session report

Source file:
- `references/cron-prompt-mid.md`

Recommended cron create parameters:
- name: `vn-stock-mid-report`
- schedule: `0 11 * * 1-5`
- skills:
  - `vn-stock-market-monitor-routine`
  - `vn-stock-market-monitor-mcp`
- enabled_toolsets:
  - `web`

Prompt body:

Produce a Vietnam stock market mid-session report for today using stock_mcp-first data and the monitor framework already defined by this skill family.

Required behavior:
- Focus on intraday health without overreacting to one swing.
- Use structured MCP market data first.
- If runtime portfolio/watchlist state is unavailable, produce a market-only report and say so explicitly.
- Do not treat a green/red move alone as sufficient evidence for a trade verdict.

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
- If breadth is weak and foreign pressure is heavy, downgrade fresh-entry verdicts by at least one level.
- If no candidate survives validation, say `0 focus buy now`.

Tool fallback rules:
- If one leaderboard tool fails, keep the report alive using breadth, sector overview, foreign flow, price board, and remaining leadership clues.

Style:
- concise, decisive
- emphasize noise control, close confirmation, and no-chase discipline

## Prompt 3 - Close report

Source file:
- `references/cron-prompt-close.md`

Recommended cron create parameters:
- name: `vn-stock-close-report`
- schedule: `10 15 * * 1-5`
- skills:
  - `vn-stock-market-monitor-routine`
  - `vn-stock-market-monitor-mcp`
- enabled_toolsets:
  - `web`

Prompt body:

Produce a Vietnam stock market close report for today using stock_mcp-first data and the monitor framework already defined by this skill family.

Required behavior:
- Produce the most decision-useful daily synthesis, not a raw dashboard.
- Use structured MCP market data first.
- If runtime portfolio/watchlist state is unavailable, produce a market-only report and say so explicitly.
- Interpret foreign flow, breadth, and sector rotation rather than simply reciting numbers.

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

## Prompt 4 - Weekly digest

Source file:
- `references/cron-prompt-weekly.md`

Recommended cron create parameters:
- name: `vn-stock-weekly-digest`
- schedule: `0 9 * * 6`
- skills:
  - `vn-stock-market-monitor-routine`
  - `vn-stock-market-monitor-mcp`
- enabled_toolsets:
  - `web`

Prompt body:

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

## Suggested next step

When ready to operate live:
1. start with one report, usually the close report
2. create a test cron job that delivers back to the origin
3. run it for 1-2 sessions to verify quality
4. only then enable the full open/mid/close/weekly set
