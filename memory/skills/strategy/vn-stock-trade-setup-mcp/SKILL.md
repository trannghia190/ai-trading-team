---
name: vn-stock-trade-setup-mcp
description: Use when analyzing a Vietnam stock for swing-trade readiness with stock_mcp-first data. Enforces analysis order price/technical -> events/news -> foreign flow -> synthesis, classifies setup type, and outputs one-direction verdicts with trigger, invalidation, and priority.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, setup, swing-trading, technicals, catalyst, foreign-flow]
    related_skills: [vn-stock-signal-synthesis, trading-rules-vn-stocks, vn-stock-market-monitor-routine]
---

# VN Stock Trade Setup via stock_mcp

## Overview

Use this skill when you need to turn Vietnam stock data into an actionable swing-trade decision.

Core principles:
1. Use `stock_mcp` as the primary source.
2. Follow the correct order: price/technical -> events/news -> foreign flow -> synthesis.
3. Do not produce contradictory conclusions. The final verdict must point in one direction only.
4. If `stock_mcp` is failing, timing out, not yet reconnected, or serving degraded data, you must state the outage or stale-session risk immediately before the analysis; do not write recommendations as if the data were still fully reliable.
5. Respect MCP request limits; prefer bundled, sequential calls and avoid unnecessary burst or parallel fan-out.

## When to Use

Use when:
- The user asks whether ticker X is buyable, where the entry should be, whether the breakout is clean, or whether the pullback is buyable.
- You need to rank several names in a watchlist by how actionable they are.
- You need to distinguish HOLD from NO ADD.

Do not use for:
- Broad session-wide market reporting.
- Pure orderbook or intraday tape reading; in that case, prefer the liquidity/orderflow skill.

## Mandatory Tool Bundle

Minimum required:
- `get_price_data(symbols="<ticker>")`
- `get_technical_analysis(symbol="<ticker>")`
- `get_stock_events(symbol="<ticker>", days=90)`
- `get_stock_money_flow_trend(symbol="<ticker>", period="1M")`
- `get_asean_interbank_interest()` — Check overnight interbank rates to confirm system liquidity.
- `get_asean_fear_greed_index()` — Check overall market sentiment.

Recommended if deeper context is needed:
- `get_finpath_stock_snapshot(symbol="<ticker>")`
- `get_ohlcv(symbol="<ticker>", days=250, interval="1D")`
- `get_market_hot_news(symbol="<ticker>")`
- `get_stock_news(symbol="<ticker>")`
- `get_finpath_recommendations(symbol="<ticker>", days=365)`
- `get_finpath_market_breadth()`
- `get_finpath_sector_overview()`

Use web/news fallback only if structured tools are not sufficient.

## Mandatory Analysis Order

### 1. Price / technical context first
You must answer:
- Where is price relative to support/resistance, MA20/MA50, and the 52-week range?
- Is the trend accumulation / markup / distribution / markdown?
- What do RSI, MACD, volume, and breakout status say?
- Is the current risk/reward still attractive?

If the risk/reward is poor or the stock has already run too far, do not conclude BUY NOW.

### 2. Events / news / catalyst next
You must check:
- Is there a real catalyst?
- Is the catalyst still upcoming, currently playing out, or already mostly priced in?
- Is there event risk that could turn the setup into a trap?

Without this step, the buy recommendation is incomplete.

### 3. Foreign flow / money flow
You must know:
- What is the foreign net buy/sell pattern?
- Is this a multi-session pattern or just one noisy day?
- Is domestic supply being absorbed?

### 4. Breadth / sector regime when relevant
Check this when the setup depends on market regime:
- Is breadth strong or weak?
- Is the sector leading or lagging?
- Do VN30 / futures confirm?

### 5. Execution refinement if needed
Only when better entry timing is needed, add:
- `get_finpath_orderbook`
- `get_intraday_trades`

## Setup Classification

Assign the stock to one main setup group, and add a secondary archetype only if needed:
- Accumulation pullback
- Shrink-volume pullback
- Base breakout
- Box support buy
- Box breakout conversion
- Bottom-volume reversal
- Catalyst-day markup
- Extended trend
- Distribution risk
- Breakdown

## Setup Archetype Playbook

### 1. Shrink-volume pullback
Use when:
- the main trend is still accumulation or markup
- price is pulling back toward MA5, MA10, MA20, or nearby support
- volume contracts clearly during the pullback

Trigger:
- support holds and the rebound candle or close is constructive
- best when the catalyst is still intact and flow is not strongly opposing

Invalidation:
- key support or MA breaks on poor volume behavior
- the pullback turns into distribution instead of a healthy pause

### 2. Base breakout
Use when:
- price has accumulated long enough and resistance is clearly defined
- the breakout comes with expanding volume and a strong enough close

Trigger:
- close is clearly above resistance or the base
- volume and momentum confirm

Invalidation:
- the breakout fails and closes back below resistance
- price becomes too extended immediately after the breakout without forming a new base

### 3. Box support buy / box breakout conversion
Use when:
- the stock is moving sideways inside a clearly defined range

Rules:
- only consider `BUY ON TRIGGER` near the bottom of the box
- middle of the box = `WATCH ONLY` or `NO TRADE`
- near the top of the box = do not chase
- once a valid breakout occurs, switch to trend-following logic

### 4. Bottom-volume reversal
Use when:
- after a deep decline, volume surges and price stabilizes
- there is additional catalyst or flow confirmation; do not bottom-fish just because of one strong green session

Trigger:
- the recent low holds and there is follow-through or strong supply absorption

Invalidation:
- the recent low is lost again quickly
- volume is large but only reflects blow-off action or exit liquidity

## Supporting Pattern Notes

- MA cross is only a secondary signal and is not enough to override poor chart location or weak catalyst/flow.
- Micro-patterns such as "one strong candle followed by 2-3 tight sessions" only matter when they sit inside a larger setup such as a pullback or breakout base.
- Do not use a narrow pattern as a standalone verdict.

## Verdict Menu

Choose only ONE final verdict:
- BUY NOW
- BUY ON TRIGGER
- HOLD
- HOLD / NO ADD
- WATCH ONLY
- REDUCE / TAKE PROFIT
- SELL / EXIT
- AVOID / TOO EXTENDED
- NO TRADE

Interpretation:
- `BUY ON TRIGGER` is used when the thesis is correct but a specific confirmation condition is still required.
- `AVOID / TOO EXTENDED` is used when the current entry is poor because price is far from the base, crowded, or reward/risk is no longer sufficient, even if the company or story is not broken.
- `NO TRADE` is used when the data or structure is too contradictory to create edge.

## Output Requirements

Each answer must include:
1. Verdict
2. Price / technical context
3. Catalyst / event summary
4. Foreign flow interpretation
5. Market or sector context if relevant
6. Trade plan
   - entry / trigger
   - invalidation
   - target / next resistance
   - priority
7. Supporting versus conflicting signals

## Hard Rules

1. Do not chase.
- If the stock is already extended -> `WATCH ONLY`, `HOLD / NO ADD`, or `BUY ON PULLBACK/TRIGGER`.

2. HOLD is different from ADD.
- A stock can be worth holding without being worth a fresh buy.

3. One green session is not enough confirmation.
- If volume, flow, or event confirmation is missing, prefer `WATCH ONLY`.

4. Do not write double-sided conclusions.
- Do not say "not ready to buy yet" and then sneak in a buy zone as an implicit suggestion.

5. Technicals are mainly for timing and invalidation.
- Do not use one indicator to override obvious deterioration in catalyst or flow.

6. Do not recommend action if current price or closing-price confirmation is still missing from MCP or a reliable fallback.
- If confirmed price is missing for a stock, state clearly that it remains in `WATCH / NOT YET FINALIZED` status instead of inferring the recommendation.

7. When MCP has just come back after an outage, distinguish `server up` from `agent session reconnected`.
- If the CLI test passes but tool calls inside the session still fail, treat it as `stale session / stale tool binding` until a real tool call succeeds.

8. When MCP has tight rate limits, prefer the minimum sufficient request scope.
- Group multiple tickers into one call when appropriate.
- Avoid large parallel fan-out just to retrieve the same data layer.
- If close to the limit, reduce scope and state the remaining confidence level explicitly.

## Common Pitfalls

1. Starting from the news story instead of chart location.
2. Ignoring event or news context while still recommending a buy.
3. Overreacting to one session of foreign buying.
4. Confusing HOLD with NO ADD.
5. Failing to provide a concrete invalidation.
6. Assuming the current session has reconnected just because MCP test or CLI passed.
7. Writing an actionable recommendation even though current price confirmation is missing.
8. Calling MCP too aggressively in parallel, self-triggering rate limits and degrading analysis quality.

See also: `references/mcp-connectivity-and-rate-limit.md` for the recovery pattern and request-discipline checklist.

## Verification Checklist

- [ ] stock_mcp tools used first
- [ ] followed the order price -> events -> foreign flow -> synthesis
- [ ] setup type assigned clearly
- [ ] final verdict is one-directional
- [ ] includes trigger, invalidation, and priority
- [ ] does not chase an already extended name
