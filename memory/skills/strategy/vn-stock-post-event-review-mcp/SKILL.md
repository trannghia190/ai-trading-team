---
name: vn-stock-post-event-review-mcp
description: Use when reviewing a Vietnam stock after earnings, AGM, dividend, policy, or other scheduled catalyst with stock_mcp-first data. Compares price reaction, expectation gap, and foreign-flow confirmation to decide follow-through, hold, reduce, or exit.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, post-event, earnings, review, follow-through]
    related_skills: [vn-stock-catalyst-execution, vn-stock-signal-synthesis, vn-stock-trade-setup-mcp]
---

# VN Stock Post-Event Review via stock_mcp

## Overview

Use this skill after an event has occurred or the market has had its initial reaction.

Objectives:
- compare pre-event expectations with the actual post-event price reaction
- determine whether this is follow-through or sell-the-news
- decide whether to hold, add on confirmation, reduce, or exit

## When to Use

Use when:
- Earnings, AGM, policy news, ETF rebalance, or another catalyst has occurred.
- The user asks whether to still buy, hold, or take profit after the event.
- You need to distinguish “good news but price reacted poorly” from “neutral news but price confirmed strongly.”

Do not use for:
- Pre-event preparation.
- Trades that have no event or catalyst as an evaluation benchmark.

## Mandatory Tool Bundle

Minimum required:
- `get_price_data(symbols="<ticker>")`
- `get_technical_analysis(symbol="<ticker>")`
- `get_stock_events(symbol="<ticker>", days=120)`
- `get_stock_money_flow_trend(symbol="<ticker>", period="1M")`

Recommended additions:
- `get_finpath_stock_snapshot(symbol="<ticker>")`
- `get_ohlcv(symbol="<ticker>", days=120, interval="1D")`
- `get_market_hot_news(symbol="<ticker>")`
- `get_stock_news(symbol="<ticker>")`
- `get_finpath_orderbook(symbol="<ticker>")`
- `get_intraday_trades(symbol="<ticker>", page_size=200)`

## Mandatory Analysis Order

### 1. Price / technical reaction first
You must answer:
- whether the post-event price reaction is gap up, hold, fade, breakdown, or sideways absorption
- whether that reaction is strong or weak relative to the pre-event chart position
- whether volume confirms follow-through or is just churn / distribution

### 2. Event outcome / expectation gap
You must state:
- whether the actual event outcome is better or worse than expected and by how much
- whether the market is currently “selling the news”
- whether the catalyst has more legs left or is close to fully priced in

### 3. Foreign flow / money flow confirmation
You must examine:
- whether foreign investors followed price after the event
- whether flow confirms the breakout or is distributing into strength
- if foreigners are selling but price is still holding, whether it indicates good absorption

### 4. Execution conclusion
Choose only one final verdict:
- ADD ON CONFIRMATION
- HOLD
- HOLD / NO ADD
- REDUCE / TAKE PROFIT
- SELL / EXIT
- WATCH FOR RE-ENTRY

## Reaction Framework

### A. Good event + good price reaction
- There is follow-through with volume confirmation, and price holds above the breakout zone
- If not yet too extended -> ADD ON CONFIRMATION is possible

### B. Good event + weak price reaction
- The news was good but price did not go far or got pushed down
- Likely sell-the-news / large supply
- Usually leans toward HOLD / NO ADD or REDUCE if distribution is clear

### C. Neutral event + strong price reaction
- The market is looking beyond the headline
- May still be actionable if chart/flow confirms

### D. Bad event + resilient price reaction
- Price may have already priced it in or there is strong absorption
- Not automatically bearish, but do not be overly optimistic too early

### E. Bad event + bad price reaction
- The thesis is broken or at least the timing is broken
- Prefer SELL / EXIT or WATCH FOR RE-ENTRY after a new base forms

## Output Requirements

Every answer must include:
1. What event actually happened
2. The post-event price reaction
3. Outcome vs. expectation comparison
4. Foreign-flow confirmation
5. The final verdict
6. If holding / adding: the confirmation trigger
7. If reducing / exiting: the invalidation or failure condition

## Hard Rules

1. Do not evaluate events by headline alone; look at the price reaction.
2. Good news with a poor price reaction is a strong warning signal.
3. Do not ADD just because “the fundamentals are good” if there is no follow-through.
4. If price breaks down after an event, do not cling to the old narrative.

## Common Pitfalls

1. Reading the event content but forgetting how the market had priced it.
2. Mistaking churn volume for breakout confirmation.
3. Seeing good news and staying bullish even though price has not confirmed.
4. Selling too early when it is only a light stop-hunt and flow is still fine.

## Verification Checklist

- [ ] Read the post-event price reaction
- [ ] Compared outcome with expectation
- [ ] Checked foreign-flow confirmation
- [ ] Distinguished follow-through from sell-the-news
- [ ] Final verdict points in one direction only
- [ ] Has clear trigger / invalidation
