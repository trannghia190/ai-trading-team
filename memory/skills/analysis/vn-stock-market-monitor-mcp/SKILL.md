---
name: vn-stock-market-monitor-mcp
description: Use when producing Vietnam stock market monitor reports with stock_mcp-first data. Covers open, intraday, close, and weekly views using breadth, sector rotation, foreign flow, VN30F context, and shortlist generation.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, monitoring, breadth, sector-rotation, foreign-flow, vn30f]
    related_skills: [vn-stock-market-monitor-routine, breadth-divergence-framework, nn-flow-tracking]
---

# VN Stock Market Monitor via stock_mcp

## Overview

Use this skill to write Vietnam market-monitor reports using structured data from `stock_mcp`.

Objectives:
- read the market regime
- distinguish broad rallies from narrow rallies
- identify sector rotation
- interpret foreign flow
- generate an actionable shortlist

## When to Use

Use when:
- The user asks for an open / mid-session / close / weekly digest report.
- The user wants to know breadth, money flow, top sectors, VN30F context, and notable stocks.
- You need a shortlist of 2-3 names worth tracking instead of a deep dive on 1 ticker.

Do not use for:
- Very deep analysis of a single stock.
- Pure orderbook/tape reading for one stock.

## Core Tool Bundle

*Note: When called through Trading Team Native MCP, the tool will automatically have the prefix `mcp_stock_mcp_` (e.g. `mcp_stock_mcp_get_price_data`). If you are running in a cron job and cannot see the MCP tools, refer to `references/cron-runtime-pitfalls.md` from the `vn-stock-market-monitor-routine` skill for the in-memory fallback path.*

### Required
- `get_price_data(symbols="VNINDEX,VN30,HNXINDEX,HNXUPCOMINDEX")`
- `get_finpath_market_breadth()`
- `get_finpath_sector_overview()`
- `get_finpath_market_top(criteria="foreign_buy")`
- `get_finpath_market_top(criteria="foreign_sell")`

### Recommended additions
- `get_index_futures_overview(days=5)`
- `get_finpath_market_top(criteria="top_value")`
- `get_finpath_market_top(criteria="top_gainers")`
- `get_finpath_market_top(criteria="top_losers")`
- `get_finpath_market_top(criteria="volume_surge")`
- `get_market_hot_news(symbol="")`

### Tool fallback note
- If `get_finpath_market_top(criteria="top_value")` fails internally or returns abnormal data, do not stop the report.
- If the runtime environment (such as a cron job) is missing the `mcp_stock_mcp_*` tools, use the CLI fallback via terminal: run `python vnstock_wrapper.py <command>` (see the `vn-stock-market-monitor-routine` skill, `references/cron-runtime-pitfalls.md`).
- Valid fallback when broad market data is missing:
  1. use `get_finpath_market_breadth()` + `get_finpath_sector_overview()` to read market/sector-level flow,
  2. use `get_finpath_market_top(criteria="foreign_buy")`, `foreign_sell`, `top_gainers`, `top_losers`, `volume_surge` to reconstruct the leadership picture,
  3. conclude `top value leadership unclear due to tool issue` only if the remaining sources are still insufficient to confirm leaders.
- The goal is to keep market-monitor reporting alive even when one leaderboard tool fails or the MCP transport layer has problems.

## Mandatory Reading Order

1. Index + futures context
2. Breadth + liquidity
3. Sector rotation
4. Foreign flow
5. Catalyst/news only if materially relevant
6. Action shortlist

## Regime Labels

Choose one primary label:
- Broad risk-on
- Narrow index-led rally
- Mixed rotational session
- Risk-off / distribution day
- Speculative froth without breadth support

## Emotion / Sentiment Overlay

After assigning the regime, add a market-emotion state to avoid misreading the quality of the move:
- cold: weak breadth, many names near lows, defensive money flow, cash holders in control
- stable: low volatility, balanced breadth, few signs of excitement or panic
- warming: breadth improving, more names rebounding from base, reasonable liquidity into leaders
- crowded: many hot narratives at once, many stocks moving faster than base quality justifies, easy FOMO
- euphoric: index or leaders are being pulled hard while reward/risk for fresh entries is clearly worsening

Overlay rules:
- Do not let a rising index automatically turn the verdict bullish if breadth or foreign flow does not confirm.
- Narrow rally + crowded/euphoric = prioritize no-chase warnings.
- Mixed rotation + stable/warming = prioritize selective sector picking, not blanket bullishness.
- Risk-off but excessively cold conditions may create a rebound watchlist; however, the market monitor may only say "watch for reversal," not front-run the buy.

## What Must Be Answered

1. Is index direction confirmed by breadth?
2. Which sectors are attracting money, and are they in ignition / expansion / divergence / fade?
3. Is foreign flow supporting the tape or weakening it?
4. Is VN30 leadership genuinely strong or only pulling the index cosmetically?
5. Is the market currently stable / warming / crowded / euphoric?
6. Which names are actionable and which ones must not be chased?

## Report Templates

### Open report
- market setup
- breadth watchpoints
- sector focus
- names to watch
- no-chase warnings

### Mid-session report
- headline move vs breadth reality
- liquidity pace
- sector rotation
- foreign-flow interpretation
- actions into the close

### Close report
- final market verdict
- breadth and liquidity summary
- sector winners / losers
- foreign-flow summary
- actionable shortlist
- next-session action table

### Weekly digest
- weekly regime summary
- breadth and money-cycle read
- sector leadership
- foreign-flow rotation
- key catalysts
- top opportunities / avoid list

## Shortlist Rule

Do not recommend a stock directly from a leaderboard.
After selecting a shortlist from market monitor, run a light check on each name with:
- `get_price_data`
- `get_technical_analysis`
- `get_stock_events`
- `get_stock_money_flow_trend`

## Output Requirements

### Market summary block
- Regime verdict
- Emotion verdict
- Breadth verdict
- Foreign-flow verdict
- Sector-rotation verdict
- Leadership quality verdict

### Action table
- Action
- Symbol
- Why
- Trigger / note
- Priority

Shortlist rules:
- `BUY ON TRIGGER` should be used only when the setup or catalyst is close enough to confirmation.
- `WATCH ONLY` should be used when the story is valid but price/flow confirmation is still missing.
- `AVOID / TOO EXTENDED` should be used when the move is already too far from base or too crowded.
- `0 focus buy now` is a valid conclusion if the shortlist fails secondary validation.

### Liquidity + Quality Filter
Before putting a stock into the action table, it must pass 2 filter layers:

Layer 1 — Liquidity floor
- Prefer HOSE/HNX as the default pool for quality leadership.
- For HOSE/HNX names: by default, do not put them into the actionable shortlist if `day_value_ty < 50` unless there is a very clear tier-1 catalyst and the setup is near confirmation.
- For UPCOM names: by default, do not put them into the actionable shortlist if `day_value_ty < 100`.
- For UPCOM names, even if they exceed the value threshold, only upgrade them to `WATCH ONLY` or better when there is a direct catalyst + repeated liquidity + non-spike behavior.

Layer 2 — Secondary validation
Score candidates using a 5-point base matrix + penalty layer:

Base score (0-5)
1. Technical state
- +1 if structure is clean: above MA20/MA50 or clearly reclaiming, trend not broken, stop logic clear
- 0 if mixed
- no point if below MA20/MA50, clearly SuperTrend down, or visible distribution

2. Breadth / sector support
- +1 if market breadth is not fighting the setup and the sector is in ignition/expansion or at least not in fade
- 0 if mixed
- no point if breadth is weak and the stock is only moving on its own

3. Flow confirmation
- +1 if foreign-flow / money-flow confirms or at least does not materially oppose
- 0 if neutral
- no point if flow is clearly distributive

4. Buyability / extension
- +1 if entry is still close to base, R:R remains reasonable, and the name is not crowded
- 0 if slightly extended but still worth monitoring
- no point if already too stretched/euphoric

5. Catalyst quality
- +1 if there is a direct, near catalyst that is not yet mostly priced in
- 0 if catalyst is vague or already partly reflected
- no point if there is no clear catalyst

Penalty layer
- -1 if intraday foreign pressure is clearly poor in a weak market regime
- -1 if the leader is only the strongest among weak setups, meaning the sector/market backdrop still does not confirm enough
- -1 if the move is a one-bar spike, especially in UPCOM/HNX small caps
- -1 if execution quality is poor: fake-tight spread, empty order book, or day_value only barely above the minimum floor

Interpretation:
- Net score >= 4 with no major red-flag penalty: may qualify for `BUY ON TRIGGER`
- Net score = 3: usually `WATCH ONLY`; only upgrade to `HOLD / NO ADD` if it is a stock the user already owns from a strong prior entry
- Net score = 2: `HOLD / NO ADD` if already owned from strength, otherwise `NO TRADE`
- Net score <= 1: remove from actionable shortlist

Hard override rules:
- If the liquidity floor fails -> reject immediately; do not continue scoring just to force an actionable buy.
- If the thesis is not bad but the entry is too far from base -> prefer `AVOID / TOO EXTENDED` rather than `NO TRADE`.
- If market breadth is BEAR + foreign selling is strong + the candidate is still under intraday foreign pressure, downgrade at least 1 verdict level for fresh entries.

Do not use raw top_gainers/top_volume/volume_surge outputs as proof that the market is healthy if most results are penny or illiquid UPCOM names.

### Shortlist quality rules
- `0 focus buy now` is a valid conclusion if regime is poor, foreign flow is heavy on the sell side, or leadership is too narrow.
- If the action is `BUY ON TRIGGER`, state the trigger via setup or money-flow confirmation, not just “because it is strong.”
- If the action is `WATCH ONLY`, explicitly state what you are waiting for: breakout, reclaim of MA20/MA50, breadth confirmation, or catalyst confirmation.
- If the action is `AVOID / TOO EXTENDED`, explicitly state the reason: crowded theme, euphoric tape, stretched valuation expectation, or narrow index-led rally.

## Common Pitfalls

1. Reading only the index and ignoring breadth.
2. Listing sectors without knowing whether money is actually flowing in.
3. Merely reciting foreign net-buy/net-sell numbers.
4. Mistaking leaderboard momentum for setup quality.
5. Using too much web/news input when structured tools are already sufficient.

## Verification Checklist

- [ ] Used stock_mcp structured data first
- [ ] Checked breadth as a mandatory step
- [ ] Interpreted foreign flow, not just quoted it
- [ ] Clearly identified sector rotation
- [ ] Included an action layer, not just a dashboard
- [ ] Shortlist passed a secondary stock-level check
