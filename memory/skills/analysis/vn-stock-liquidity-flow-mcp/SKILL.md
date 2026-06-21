---
name: vn-stock-liquidity-flow-mcp
description: Use when evaluating Vietnam stock liquidity and execution quality with stock_mcp-first data. Reads snapshot, orderbook, intraday trades, and money flow to distinguish strong liquidity, absorption, fragile breakouts, and distribution risk.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, liquidity, orderflow, orderbook, intraday, execution]
    related_skills: [vn-stock-orderflow-interpretation, trading-rules-vn-stocks, vn-stock-trade-setup-mcp]
---

# VN Stock Liquidity & Orderflow via stock_mcp

## Overview

Use this skill to evaluate liquidity and execution quality for Vietnam stocks.

Do not stop at asking whether “volume is large or small.” You must answer:
- whether there is real supply absorption
- whether there are signs of distribution
- whether the breakout is trustworthy
- whether to enter aggressively, stage orders, wait, or avoid

## When to Use

Use when:
- The user asks about the liquidity of ticker X.
- You need to read the orderbook, intraday trades, and absorption/distribution behavior.
- You want to know whether foreign selling is being absorbed.
- You want to refine execution after the higher-level thesis is already formed.

Do not use for:
- Building the full higher-level trade thesis for a stock from scratch; in that case prefer the trade-setup skill.
- Broad market reporting.

## Core Tool Bundle

Required:
- `get_finpath_stock_snapshot(symbol="<ticker>")`
- `get_finpath_orderbook(symbol="<ticker>")`
- `get_intraday_trades(symbol="<ticker>", page_size=200)`
- `get_stock_money_flow_trend(symbol="<ticker>", period="1M")`

Recommended additions:
- `get_price_data(symbols="<ticker>")`
- `get_ohlcv(symbol="<ticker>", days=60, interval="1D")`
- `get_technical_analysis(symbol="<ticker>")`

## Reading Framework

### A. Structural liquidity
Check:
- volume vs avg20
- whether the stock is liquid enough for swing trading
- whether recent participation is expanding or shrinking

### B. Top-of-book quality
Read the orderbook to assess:
- whether bid/ask stack is balanced or skewed
- whether there is a clear sell wall
- whether demand looks sticky or fragile

### C. Tape behavior
Read intraday trades to see:
- whether there are large prints confirming demand
- whether sell pressure is fading or increasing
- whether buy absorption appears after sell sweeps

### D. Flow consistency
Use money flow to see:
- whether foreign flow reinforces the move
- if foreigners are selling, whether price can still hold
- whether this is accumulation, passive support, or distribution

## Execution-Quality States

Choose one state:
- EXECUTION-FRIENDLY
- EXECUTION-FRIENDLY ON PULLBACK
- WATCH FOR ABSORPTION CONFIRMATION
- FRAGILE / SIZE DOWN
- DISTRIBUTION RISK / AVOID

## Interpretation Rules

1. Large volume does not automatically mean accumulation.
- If price cannot extend or keeps getting pressed back at resistance, it may be distribution.

2. Foreign selling is not always bearish.
- If price and tape remain resilient, explicitly state that domestic absorption is present.

3. Orderbook is only a refinement tool.
- Do not recommend a trade just because the book looks good at one moment.

4. Thin book -> lower confidence.
- Do not use aggressive language when execution risk is high.

5. Breakout quality needs tape + context.
- expanding volume
- book not clearly capped by heavy supply
- decent intraday follow-through
- market regime not hostile

## Output Requirements

Every answer must include:
1. Liquidity verdict
2. Orderbook read
3. Tape read
4. Foreign-flow interpretation
5. Execution advice
   - aggressive / normal / staged / wait / avoid
6. Key risk

## Common Pitfalls

1. Confusing high turnover with clean accumulation.
2. Trusting one bid wall as certain support.
3. Ignoring whether price can actually extend after large volume.
4. Calling foreign selling bearish without checking price resilience.
5. Advising aggressive entry in thin liquidity.

## Verification Checklist

- [ ] Read snapshot / historical volume context
- [ ] Read orderbook and intraday trades
- [ ] Interpreted money flow
- [ ] Chosen a clear execution-quality state
- [ ] Distinguished absorption from distribution
