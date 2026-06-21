---
name: vn-stock-portfolio-rebalance-mcp
description: Use when a VN stock portfolio changes and you need to rebalance live positions using stock_mcp-first data. Decides what to add, trim, hold, exit, or replace based on thesis quality, chart location, catalyst path, flow confirmation, and concentration risk.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, portfolio, rebalance, risk-management, concentration]
    related_skills: [vn-stock-watchlist-ranker-mcp, vn-stock-valuation-thesis-mcp, vn-stock-trade-setup-mcp, vn-stock-signal-synthesis]
---

# VN Stock Portfolio Rebalance via stock_mcp

## Overview

Use this skill when a live Vietnam stock portfolio needs a rebalance decision:
- which names should be increased
- which names should be kept unchanged
- which names should be held but not added to
- which names should be trimmed
- which names should be exited and replaced with better opportunities

Goals:
- protect capital first
- concentrate more into the best 2-3 ideas when conditions allow
- avoid carrying too many names that are not bad enough to sell and not good enough to add
- force every portfolio change to be justified by thesis, chart, catalyst, flow, and risk budget

This skill does not only judge each stock separately.
It optimizes at the portfolio level.

## When to Use

Use when:
- the user provides the current portfolio and asks how it should be restructured
- trimming or adding is needed after a strong rally or a regime change
- lower-edge names should be replaced by higher-edge names
- you need to distinguish between holding a winner and trimming it because of concentration or risk

Do not use for:
- single-stock analysis without portfolio context
- ultra-short-term tape-only decisions
- complex quantitative portfolio optimization beyond available data

## Required Inputs from User

Try to have:
- the list of current holdings
- position weights, or at least relative size
- approximate gain or loss if the user provides it
- whether there is cash available for rotation
- the user objective: defense, trend-holding, or higher concentration

Prioritize data sources in this order:
1. the user's current portfolio source-of-truth file if it exists
2. internal state files or active plan files used by routines
3. direct user input in chat

If a reliable source-of-truth already exists, do not mechanically ask the user to re-enter the whole portfolio. Only ask for missing fields such as weights, time horizon, or whether the stored state is still current.

If exact weights are missing, rebalancing can still be done in relative buckets:
- core position
- medium position
- small probe

## Core Tool Bundle

Mandatory at the portfolio level:
- `get_finpath_market_breadth()`
- `get_finpath_sector_overview()`
- `get_price_data(symbols="<comma-separated holdings>")`

Mandatory at the single-name level:
- `get_technical_analysis(symbol="<ticker>")`
- `get_stock_events(symbol="<ticker>", days=120)`
- `get_stock_money_flow_trend(symbol="<ticker>", period="1M")`
- `get_finpath_stock_snapshot(symbol="<ticker>")`

Recommended additions:
- `get_market_hot_news(symbol="<ticker>")`
- `get_stock_news(symbol="<ticker>")`
- `get_finpath_orderbook(symbol="<ticker>")`
- `get_intraday_trades(symbol="<ticker>", page_size=200)`
- `get_index_futures_overview(days=5)`

## Mandatory Analysis Order

### 1. Portfolio regime first
Answer these first:
- does the current market support high concentration?
- does breadth support offensive holding, or is a more defensive stance needed?
- should cash be increased, beta reduced, or capital rotated into stronger groups?

### 2. Cross-position ranking second
Do not stop after judging each name independently.
Cross-rank the book:
- which holdings have the highest edge
- which ones clearly have weakening edge
- which ones are simply occupying capital
- which ones create excessive concentration risk

### 3. Single-name thesis check third
For each stock, review:
- chart location
- catalyst path
- foreign flow or money flow
- valuation sanity if relevant
- whether the setup is still valid or has degraded

### 4. Position-role decision fourth
Each name must be assigned one role:
- CORE ADD
- CORE HOLD
- HOLD / NO ADD
- TRIM INTO STRENGTH
- REDUCE RISK
- EXIT / REPLACE

### 5. Portfolio action layer fifth
Finish with the portfolio-level decision:
- whether to raise cash
- whether to concentrate more or diversify slightly
- which weak groups should be rotated into which stronger groups
- whether the total number of names should be reduced

## Rebalance Buckets

Each stock belongs to only one bucket:
- ADD / INCREASE
- HOLD CORE
- HOLD / NO ADD
- TRIM
- REDUCE / DE-RISK
- EXIT / REPLACE

## Decision Rules

1. A good stock that is too extended:
- usually belongs in HOLD / NO ADD or light TRIM
- do not auto-ADD just because it is winning

2. A stock whose thesis is still fine but has lower edge than another name:
- may be TRIMMED to fund the better idea

3. A losing stock does not automatically need to be sold, but:
- if the thesis is broken, chart is broken, and flow is bad -> EXIT

4. Do not keep too many meaningless small positions.
If a position lacks enough conviction to be added to or held as core, consider reducing or removing it.

5. Concentration should only be increased when:
- the market regime permits it
- the best 1-3 names truly have superior edge
- catalyst and flow are sufficiently confirming

6. If breadth is weak or the market is risk-off:
- prioritize REDUCE / DE-RISK rather than hunting for new adds

## Output Requirements

Every answer should include:
1. portfolio or market regime
2. a table for each stock
   - Symbol
   - Current role or bucket
   - Why
   - Action
   - Priority
3. a list of names to increase, hold, trim, reduce, or exit
4. the portfolio-level decision
   - raise cash / keep cash low / rotate sector / increase concentration
5. the top 2-3 positions that should remain focus core after rebalance
6. risk notes
   - concentration risk
   - event risk
   - no-add warnings

## Hard Rules

1. Do not add to a stock just because it is profitable.
2. Do not keep a low-edge stock just because the loss is still small or because of emotional attachment.
3. Do not treat HOLD and ADD as the same thing.
4. Do not increase concentration in a weak market regime without confirmation.
5. If a stock should be sold to make room for a better one, say EXIT / REPLACE directly.

## Common Pitfalls

1. The portfolio holds too many average names.
2. Book profit is confused with current edge.
3. Extended names become overweight because open profit feels safe.
4. Risk is not reduced when breadth deteriorates.
5. Opportunities are not compared directly against one another.

## Suggested Workflow

### Step 1: read the whole portfolio
- identify market regime
- list holdings and current roles

### Step 2: rank relative edge
- which names are strongest
- which names are weakest
- which ones occupy capital without deserving it

### Step 3: decide each stock
- add / hold / no add / trim / exit

### Step 4: decide at the portfolio level
- raise cash?
- reduce the number of names?
- rotate into 1-2 stronger ideas?

## Verification Checklist

- [ ] Market regime checked before rebalancing
- [ ] Positions compared against each other, not only analyzed independently
- [ ] Each stock assigned exactly one action bucket
- [ ] ADD clearly separated from HOLD / NO ADD
- [ ] Portfolio-level decision included, not only stock-level decisions
- [ ] Focus core positions identified after rebalance
