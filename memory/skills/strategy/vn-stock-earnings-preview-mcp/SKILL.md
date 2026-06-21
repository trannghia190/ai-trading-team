---
name: vn-stock-earnings-preview-mcp
description: Use when preparing a Vietnam stock ahead of earnings, AGM, or a scheduled catalyst window with stock_mcp-first data. Focuses on pre-event chart location, expectation risk, foreign-flow setup, and whether to pre-position, wait for trigger, or avoid.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, earnings, catalyst, pre-event, setup]
    related_skills: [vn-stock-catalyst-execution, vn-stock-trade-setup-mcp, vn-stock-signal-synthesis]
---

# VN Stock Earnings / Event Preview via stock_mcp

## Overview

Use this skill when preparing a plan ahead of a time-known event such as:
- quarterly earnings
- AGM / shareholder meeting
- ex-rights / dividend / issuance dates
- ETF / rebalance windows
- policy or event windows with a reasonably clear schedule

The goal is not to guess emotionally whether the news will be “good or bad,” but to answer:
- where the chart is positioned before the event
- how much expectation is already priced in
- whether foreign flow is pre-positioning
- whether to take a small pre-position, wait for a post-event trigger, or avoid it entirely

## When to Use

Use when:
- The user asks whether to enter before earnings, an AGM, or another scheduled event.
- A stock has a clear upcoming catalyst and needs a pre-event plan.
- You need to separate a strong medium-term thesis from whether a pre-event entry is actually worthwhile.

Do not use for:
- Reviewing the stock after the event is out and price has already fully reacted.
- Normal technical trades without a clear event window.

## Mandatory Tool Bundle

Minimum required:
- `get_price_data(symbols="<ticker>")`
- `get_technical_analysis(symbol="<ticker>")`
- `get_stock_events(symbol="<ticker>", days=120)`
- `get_stock_money_flow_trend(symbol="<ticker>", period="1M")`

Recommended additions:
- `get_finpath_stock_snapshot(symbol="<ticker>")`
- `get_ohlcv(symbol="<ticker>", days=250, interval="1D")`
- `get_market_hot_news(symbol="<ticker>")`
- `get_stock_news(symbol="<ticker>")`
- `get_stock_social_posts(symbol="<ticker>")`
- `search_stock_social_posts(symbol="<ticker>")`
- `get_finpath_recommendations(symbol="<ticker>", days=365)`
- `get_finpath_market_breadth()`
- `get_finpath_sector_overview()`

### Event-source rule
- Always call `get_stock_events` first to find structured or scheduled events.
- If `get_stock_events` returns empty but newsflow or posts still show a clear catalyst, do NOT jump to the conclusion that there is “no event.”
- In that case, fall back to `get_market_hot_news`, `get_stock_news`, `get_stock_social_posts`, or `search_stock_social_posts` to build the expectation window.
- Interpret the result as one of 3 categories:
  - `SCHEDULED EVENT`: there is an event calendar or a reasonably clear time confirmation
  - `SOFT CATALYST WINDOW`: there is no structured schedule, but the catalyst cluster / newsflow is clear enough for the market to pre-position
  - `NO VERIFIED EVENT`: neither a scheduled event nor a trustworthy catalyst window can be confirmed

## Mandatory Analysis Order

### 1. Price / technical context first
You must determine:
- whether the stock is in a base, early breakout, extended move, or distribution
- how much room remains to the nearest resistance or target
- whether the risk/reward is still good enough for a pre-event entry
- whether volume and momentum are improving or this is just a technical bounce

If the chart is already extended or the risk/reward is too tight, do not pre-position just because the event looks attractive.

### 2. Event / expectation map
You must answer:
- what the specific event is and when it occurs
- whether this is a `SCHEDULED EVENT`, `SOFT CATALYST WINDOW`, or `NO VERIFIED EVENT`
- what the market is currently expecting
- whether the catalyst is mainly short-term or medium-term
- whether the main risk is underwhelming results, delay, or sell-the-news behavior

If `get_stock_events` has no data:
- do not automatically assume there is “no catalyst”
- check newsflow and posts to see whether an expectation window is forming
- clearly state whether the catalyst is a hard event or only a soft expectation narrative

### 3. Foreign flow / money flow
You must examine:
- whether foreign investors are pre-positioning over the last 3-10 sessions
- whether this is real accumulation or just a one-session spike
- if foreigners are selling, whether price is still being absorbed well

### 4. Market / sector regime
If the event is tied to a sector theme, check:
- whether current breadth supports risk-on behavior
- whether the sector is being favored or distributed
- whether the market is entering a freeze or risk-off window

### 5. Execution choice
Choose only one of these states:
- PRE-POSITION SMALL
- WAIT FOR POST-EVENT TRIGGER
- WATCH ONLY
- NO TRADE

## Pre-Event Decision Framework

### A. PRE-POSITION SMALL
Use only when:
- the chart still has a clean base or healthy pullback
- the event is not yet fully priced in
- flow offers reasonable confirmation
- there is still a sensible stop even if the event fails

### B. WAIT FOR POST-EVENT TRIGGER
Use when:
- the thesis is good but price is already near resistance or has already moved ahead of the event
- you do not want to take binary risk before the event
- you want to wait for breakout or base-hold confirmation after the event

### C. WATCH ONLY
Use when:
- the event is notable but the signals are still mixed
- the chart does not yet show a clear edge
- foreign flow has not confirmed

### D. NO TRADE
Use when:
- event risk is larger than the remaining upside
- the chart or risk/reward is poor
- the market regime is not supportive
- the catalyst is already too crowded

## Output Requirements

Every answer must include:
1. The specific event window
2. Event classification: SCHEDULED EVENT / SOFT CATALYST WINDOW / NO VERIFIED EVENT
3. Pre-event chart location
4. Expectation risk
5. Foreign-flow read
6. Action mode: PRE-POSITION SMALL / WAIT FOR POST-EVENT TRIGGER / WATCH ONLY / NO TRADE
7. Entry / trigger / invalidation
8. Conditions that would invalidate the pre-event thesis

## Hard Rules

1. Do not use the event to justify a bad entry.
2. Do not call for PRE-POSITION if the stop logic is unclear.
3. If price has already run too far ahead of the event, default toward WAIT or WATCH.
4. Clearly separate the long-term thesis from pre-event execution.

## Common Pitfalls

1. Looking only at the event calendar and ignoring chart location.
2. Mistaking one session of foreign buying for durable pre-positioning.
3. Buying before the event even though very little upside remains.
4. Failing to state the sell-the-news risk clearly.

## Verification Checklist

- [ ] Checked chart location before the event
- [ ] Identified expectation risk
- [ ] Read foreign flow over the last 3-10 sessions
- [ ] Considered market/sector regime when relevant
- [ ] Chosen exactly 1 action mode
- [ ] Provided clear trigger and invalidation
