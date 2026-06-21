---
name: vn-stock-market-monitor-routine
description: Use when producing recurring VN stock market reports for open, mid-session, close, or weekly digest. Combines macro, breadth, foreign flow, catalyst, and portfolio-risk review without hardcoding stale holdings.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, routine, monitoring, breadth, foreign-flow, catalyst]
    related_skills: [trading-rules-vn-stocks, nn-flow-tracking, breadth-divergence-framework, strawberry-stock-memory-harvest]
---

# VN Stock Market Monitor Routine

## Overview

This skill turns repeated Analysis market-monitor reports into a reusable Trading Team workflow for Vietnamese stocks.

This is the routine/orchestration layer for recurring reports, not the main market-analysis layer replacing `vn-stock-market-monitor-mcp`.
- Use `vn-stock-market-monitor-mcp` when you need actual market-monitor analysis with stock_mcp-first data.
- Use this skill when you need to package recurring reports for open / mid-session / close / weekly digest while keeping the operational format consistent.

Use it for 4 recurring report types:
1. Open
2. Mid-session
3. Close
4. Weekly digest

Core principle: do not produce a report by looking only at index movement or only at holdings. Every report should synthesize:
- market regime
- breadth
- foreign flow
- sector rotation
- emotion / sentiment state
- leadership quality
- macro-liquidity backdrop when materially relevant
- catalyst status
- portfolio risk / action triggers

This routine skill inherits the stricter interpretation contract from `vn-stock-market-monitor-mcp`:
- a green index is not enough; breadth and leadership quality must confirm
- `0 focus buy now` is a valid conclusion
- watchlists/shortlists must be secondary-validated, not copied mechanically from leaderboard data
- illiquid UPCOM spikes are not evidence of healthy market risk appetite

## When to Use

Use when:
- The user asks for a VN stock market monitor report.
- The user wants a structured open/mid/close market briefing.
- The user wants a weekly digest that connects macro + portfolio + sector/catalyst context.
- You need to monitor a live or paper portfolio in a repeatable format.

Do not use for:
- Deep research on one company only.
- Intraday scalping recommendations from raw tick data alone.
- Blind portfolio journaling after a trade; use a portfolio-sync skill/workflow for that.

## Source-of-Truth Rules

Reference:
- `references/report-language-and-format-rules.md` — formatting, language, and report-shape rules learned from live cron feedback.

1. Do not hardcode old holdings, cash, stop losses, or watchlist levels into the skill.
2. Read current state from the user's current source of truth at runtime.
3. Use market-data MCP/tools first; web/news only when the required data is not available from MCP/tooling.
4. Treat dated catalysts, old P/L, and prior reports as context only, not truth.

## Mandatory Analysis Order

For any report, follow this general order:
1. Market overview
2. Breadth and sector rotation
3. Foreign flow
4. Portfolio/watchlist snapshot
5. News/catalysts/events
6. Risk/action synthesis

Within the market-overview layer, always force this sub-order:
1. Index / futures context
2. Breadth verdict
3. Sector lifecycle verdict
4. Foreign-flow verdict
5. Emotion / sentiment verdict
6. Leadership quality verdict
7. Actionability verdict

For single-stock decisions referenced inside a report, preserve this order:
1. Price + technical state
2. Events/news
3. Foreign flow
4. Recommendation

Never let a story/catalyst or a green index headline jump ahead of price/technical reality and breadth quality.

## Data Priority

Default priority:
1. Stock/market MCP tools first
2. Current memory/context files second
3. Web/news extraction third

Do not jump to web first if structured tool data is already available.

**Cronjob configuration warning:** When setting up cron jobs for these reports, ensure `enabled_toolsets: []` (empty array) so the MCP tools are injected correctly. Restricting toolsets (e.g., to `["web"]`) will silently drop the MCP data connection. See `references/cron-mcp-pitfalls.md`.

**Data Integration Hooks:**
Always read these local source-of-truth files before writing any report:
- `/memory/portfolio/AGENTS.md` (live holdings & cash)
- `/memory/trading_plan/AGENTS.md` (active plans)
- `/memory/sessions/<DATE>_market_journal.md` (continuity/yesterday's narrative)
- `/memory/tickers/<TICKER>.md` (intraday watch interests)

**Cron fallback when stock_mcp routing is unavailable but local VNStock runtime exists:**
- If the scheduled run cannot access the expected `stock_mcp` / `mcp_stock_mcp_*` tool path, do not silently switch to web-first analysis.
- First keep the required local-file read path above.
- Then attempt a local structured fallback via installed VNStock Python runtime / local market-data workspace to recover at least:
  - live/near-live price board for indices + portfolio/watchlist names
  - recent daily history for opening-gap / prior-close comparisons
  - structured FX data (e.g. VCB exchange-rate table)
- If this fallback still cannot reproduce market-wide breadth / sector-overview / foreign-top tables, explicitly downgrade confidence and say breadth/sector verdict is unconfirmed rather than inferring it from a few large-cap names.
- If local VNStock/runtime probes also fail partially (for example only ETF/partial symbols resolve, or quote history is inconsistent across names), do **not** synthesize a fake market view from the surviving fragments. Treat the data path as degraded and fall back to a constrained operational note.
- In open/close reports, if `mcp_stock_mcp_*` tools are missing from the environment, do NOT fall back to web search immediately. Instead, use the `vnstock_wrapper.py` CLI via terminal (see `references/cron-runtime-pitfalls.md`) to retrieve price data, indicators, and exchange rates.
- If data retrieval fails even with the CLI fallback (e.g., tool error 127 or empty results), explicitly state the data limitation in the report and focus on the portfolio impact based on the last known prices in `vn_stock_portfolio.json`.
- In that degraded open-report mode, keep the report action-first: cite the data limitation in 1 short bullet, avoid symbol-by-symbol sprawl, and explicitly separate `what is currently known` from `what is still unconfirmed`.

Tie the market regime directly to the user's current holdings and cash. See `references/portfolio-integration-hook.md`.

*Daily Radar Autonomy*: During normal chat sessions, if the user discusses a stock in-depth (e.g., evaluating a setup, asking repeatedly about a ticker, or showing trading intent), proactively and autonomously append it to `vn_stock_daily_radar.txt` with brief context. Do not wait for an explicit "add to radar" command.
*Daily Radar Autonomy*: During normal chat sessions, if the user discusses a stock in-depth (e.g., evaluating a setup or showing intent), proactively and autonomously append it to `vn_stock_daily_radar.txt` with brief context. Do not wait for an explicit "add to radar" command.
*Radar Carry-Forward Rule*: Mid-session reports may append up to 1-3 truly notable non-holding names into `vn_stock_daily_radar.txt` for same-day follow-up, but only when they are genuinely worth monitoring, not already listed, and accompanied by a very short reason. Do not spray-add symbols.
*Market Journal Continuity*: 
- Open, Mid, and Weekly reports READ the journal to maintain narrative continuity. They MUST NOT overwrite the journal.
- The Close report READS the journal for continuity, then OVERWRITES it at the end with a concise summary of today's market to hand off to tomorrow. It also clears the daily radar.


*Balance rule for close reports*:
- Do not over-correct into a portfolio-only report.
- Every close report must balance 3 layers: (1) market-wide regime/breadth/rotation, (2) impact on current portfolio and active plans, and (3) new opportunities / notable movers / radar follow-up outside current holdings.
- If the user discussed a stock during the day (example: VPB), the close report should briefly follow up on that ticker in the radar/opportunity layer even if it is not in the live portfolio.

*Language rule for recurring reports*:
- When the user is operating in Vietnamese, recurring market reports must be written fully in Vietnamese.
- Keep ticker symbols unchanged, but avoid English section headers or mixed-language verdict labels unless the user explicitly asks for bilingual output.
- Prefer concise terminal-friendly English labels such as `Open Headline`, `Market Summary`, `Portfolio Impact`, `New Opportunities & Radar`, and `What Not To Do`.

*Macro-weighting rule by report type*:
- Open report: macro at light-to-medium weight as an overnight risk filter.
- Mid-session report: macro only as a light confirmation/contradiction overlay.
- Close report: macro as explanatory overlay for rotation/regime/cash stance, not the body of the report.
- Weekly digest: heaviest macro block, but explicitly downgrade confidence if only page-level SBV data is available and structured interbank/OMO/bond-yield data is missing.
- Never fabricate a full macro-liquidity verdict from partial SBV page data.

### Market-monitor routing defaults
- Index / close / realtime board: `get_price_data`
- Breadth / foreign net / sector leaders-laggards: `get_finpath_market_breadth`
- Sector structure / deeper rotation context: `get_finpath_sector_overview`
- Foreign buy/sell leaders: `get_finpath_market_top(criteria="foreign_buy")`, `get_finpath_market_top(criteria="foreign_sell")`
- Volume-surge candidates: `get_finpath_market_top(criteria="volume_surge")`
- VN30F overlay: `get_index_futures_overview`
- Hot market news / narrative shifts: `get_market_hot_news("")`

Use leaderboard outputs only as candidate generators.
Always run a secondary quality filter before elevating any symbol/sector into the actionable shortlist.

## Report Type 1: Open Session

### Objective
Prepare the user for the trading day with overnight context, macro pressure points, and current portfolio/watchlist readiness.

### Required Sections
1. Overnight global context
   - US market close
   - key Asia open signals
   - major macro/geopolitical shocks
   - commodity/fx signals relevant to VN (oil, DXY, USD/VND when material)

2. Current market setup
   - VN-Index / VN30 / futures context if available
   - regime label: broad risk-on / narrow rally / mixed rotation / risk-off / speculative froth
   - emotion label: cold / stable / warming / crowded / euphoric
   - leadership quality: broad confirmation vs narrow index-heavy tape

3. Portfolio open snapshot
   - current price vs reference / approximate open
   - stop-loss distance
   - unrealized P/L rough status
   - catalyst status by holding

4. Watchlist readiness
   - whether a symbol is still in entry zone
   - whether it has moved too far and should not be chased

5. Macro/liquidity block
   - SBV / liquidity / rates / FX only if relevant and updated
   - include only decision-relevant details, not raw data dumps

6. Macro-liquidity overlay
   - SBV / OMO / injection-drain context when data is available
   - interbank overnight / short-tenor liquidity pressure when data is available
   - government-bond yield direction when data is available
   - USD/VND / FX pressure when material
   - classify backdrop as supportive / neutral / tightening headwind / stress warning

7. Plan for the session
   - HOLD / WATCH / WAIT PULLBACK / ADD IF X / TRIM IF Y

8. Warning flags
   - event risk
   - macro tightening risk
   - oil / CPI / FX / external shock
   - stock-specific risk close to SL

### Output Style
The open report should answer:
- What changed overnight?
- Is the portfolio entering the day safely?
- Which names require attention today?
- What should not be chased?

Open-report formatting rules learned from live use:
- Keep it short and operational; target roughly 350-600 words.
- Do not dump tool data or review every holding mechanically.
- Prioritize 3-5 symbols that matter most right now.
- Always include a block for notable names outside current holdings.
- The reader should finish in 1-2 minutes and know: market strength is real or not, what in the portfolio needs attention now, what external names are worth watching, and what must not be done at the open.

## Report Type 2: Mid-Session

### Objective
Measure intraday health without overreacting to noise.

### Required Sections
1. Market overview
   - VN-Index / VN30 change
   - liquidity pace vs recent average
   - breadth
   - regime label
   - emotion label
   - whether the move looks like orderly consolidation, broad rally, narrow pillar-led rally, mixed rotation, or broad selloff
   - add one explicit line: "#1 variable for the afternoon session"
   - add one explicit line: "2 names/sectors most worth watching if the market improves"

2. Portfolio real-time snapshot
   - price change
   - P/L state
   - buffer vs SL
   - urgent risk flags

3. Per-name read
   - status
   - foreign flow
   - technical context / catalyst intact or not
   - recommended action

4. Sector rotation snapshot
   - top leading sectors
   - lagging sectors
   - assign leading sectors to ignition / expansion / divergence / fade when evidence is sufficient
   - whether current holdings are aligned with or fighting rotation

5. Foreign flow summary
   - both portfolio names and notable watchlist names
   - distinguish passive selling from active distribution when evidence supports it

6. Actions
   - HOLD all
   - monitor for close confirmation
   - add only if conditions remain strong into close
   - do not chase breakouts already extended intraday

### Mid-Session Discipline
- Avoid using one intraday swing as final truth.
- Do not recommend a trade only because price is green/red.
- If no SL is threatened and catalyst is intact, HOLD is a valid answer.

## Report Type 3: Close

### Objective
Produce the most decision-useful daily synthesis.

### Required Sections
1. Final market close
   - VN-Index, VN30, liquidity, breadth
   - regime verdict
   - emotion verdict
   - leadership-quality verdict
   - note divergence if index strength is narrow

2. Portfolio ATC / close snapshot
   - closing price
   - P/L
   - SL buffer
   - risk flag per name

3. Sector rotation close read
   - which sectors led
   - which weakened
   - whether rotation supports or threatens current holdings

4. Foreign flow close summary
   - top net buy/sell on HOSE if relevant
   - holding-specific interpretation
   - accumulation vs distribution pattern across several sessions when possible

5. Daily synthesis and next-day outlook
   - what kind of session it was
   - what the move implies for tomorrow
   - which regime/framework is active

6. Warning flags
   - breadth divergence
   - tight SL buffers
   - weakening catalyst
   - heavy distribution in watchlist names

7. Next-day action table
   - HOLD / TRAIL / ADD / DEFER / SKIP
   - trigger-based, not vague

### Special Regime Checks
Always explicitly check for:
- narrow breadth rally / "green skin, red heart"
- foreign-flow rotation
- stop-loss hunt context if a name threatened SL intraday
- whether a passive ETF flow explanation is more plausible than active distribution

## Report Type 4: Weekly Digest

### Objective
Zoom out from daily noise and update the medium-term thesis.

### Required Sections
1. Insider / major shareholder / notable ownership changes
2. Fund flow / foreign flow / ETF context
3. Earnings, AGMs, and major company events
4. International macro / Fed / oil / global risk tone
5. Domestic policy / SBV / liquidity / public investment / sector policy
6. Money-cycle interpretation
7. Summary actions by holding/watchlist

### What the weekly digest should answer
- Did the medium-term thesis improve or deteriorate?
- Is foreign flow noise or structural rotation?
- Which catalysts are still alive over the next weeks/months?
- Which positions deserve patience vs active risk management?

## Core Interpretation Frameworks

### 1. Breadth Before Comfort
If index is green but breadth is poor, say so explicitly.
Use breadth divergence to avoid false comfort from headline index gains.

### 2. Foreign Flow Must Be Interpreted, Not Recited
Do not stop at "foreign investors bought/sold X".
Ask:
- Is this multi-session accumulation/distribution?
- Is this passive ETF flow?
- Is price resisting the flow, implying strong domestic demand?
- Is rotation moving from one sector to another?

### 3. Catalyst Integrity Over Short-Term Noise
A position can stay valid despite one weak session if:
- catalyst remains intact
- SL is not violated
- no major negative event has emerged

### 4. No Chase Rule
If a watchlist name has already run too far from the planned zone, explicitly mark it as DO NOT CHASE.

### 5. Technicals Are Mainly for Risk Management
Use technicals to:
- assess extension / overbought / oversold
- monitor support and resistance
- manage trailing SL
Not to override a still-intact catalyst without stronger evidence.

### 6. Shortlist Quality Filter Is Mandatory
Before naming any actionable symbols in a routine report, filter candidates through these questions:
- Is the symbol liquid enough to matter for institutional-quality leadership?
- Is it being supported by breadth/sector context, or only moving alone?
- Is the move already too extended to chase?
- Is the signal from a credible board context, or mainly from illiquid UPCOM/penny noise?

Liquidity floor defaults:
- HOSE/HNX: default exclude from actionable shortlist if `day_value_ty < 50`, unless catalyst is direct and setup is very near confirmation.
- UPCOM: default exclude from actionable shortlist if `day_value_ty < 100`.
- UPCOM names that barely pass the floor still require repeated liquidity + direct catalyst + non-spike behavior before being elevated beyond `WATCH ONLY`.

Secondary validation scoring:
- Use a 5-point base score + penalty model, not a binary yes/no feel.

Base score (0-5)
1. Technical state
- +1 if structure is clean, trend is not broken, and invalidation is clear
2. Breadth / sector support
- +1 if the sector is genuinely supported by the broader market backdrop
3. Flow confirmation
- +1 if foreign-flow / money-flow confirms, or at least does not strongly fight the move
4. Buyability / extension
- +1 if the entry is still buyable, not crowded, and R:R remains reasonable
5. Catalyst quality
- +1 if there is a near enough catalyst that is not yet mostly priced in

Penalty layer
- -1 if intraday foreign pressure is clearly poor in a weak market regime
- -1 if the candidate is only the strongest among weak setups
- -1 if the move is a one-bar spike or low-quality tape
- -1 if execution quality is weak or day_value is only barely above the floor

Interpretation:
- Net score >= 4 with no major red-flag penalty -> may qualify for `BUY ON TRIGGER`
- Net score = 3 -> usually `WATCH ONLY`; sometimes `HOLD / NO ADD` if it is an already well-held position
- Net score = 2 -> `HOLD / NO ADD` if already owned from a strong prior entry, otherwise `NO TRADE`
- Net score <= 1 -> remove from the action shortlist

Hard overrides:
- Fail liquidity floor -> exclude immediately from the actionable shortlist.
- Thesis still alive but entry too far from base -> prefer `AVOID / TOO EXTENDED`.
- Breadth BEAR + strong foreign selling + poor intraday foreign pressure -> downgrade fresh-entry verdicts by at least 1 level.

If the shortlist fails this filter, explicitly say `0 focus buy now`.

## Common Pitfalls

1. Reporting the index but ignoring breadth.
2. Reporting foreign flow but failing to interpret whether it is passive, active, or rotational.
3. Copying stale holdings/cash/SL from old notes.
4. Turning every report into a trade recommendation.
5. Overreacting to midday noise when no trigger actually broke.
6. Omitting news/events from stock analysis.
7. Hardcoding watchlists in prompts instead of reading current state.
8. For cron/MCP-first reports, do not restrict `enabled_toolsets` to something like `['web']` if the goal is to use structured market tools as the primary source. That can easily bias the agent toward web-first fallback and break the required data path. By default, leave toolsets unset; only add restrictions when you fully understand the runtime consequences.

See also:
- `references/cron-runtime-pitfalls.md`

## Verification Checklist

- [ ] Used current runtime portfolio/watchlist state, not stale archived numbers
- [ ] Checked breadth, not just index direction
- [ ] Included foreign-flow interpretation, not just raw net values
- [ ] Checked events/news before making any stock recommendation
- [ ] Flagged extended names as do-not-chase when appropriate
- [ ] Produced trigger-based actions for the next session when relevant
