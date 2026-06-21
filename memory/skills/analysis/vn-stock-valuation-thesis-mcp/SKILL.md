---
name: vn-stock-valuation-thesis-mcp
description: Use when evaluating whether a Vietnam stock still has valuation support for a 1-6 month thesis using stock_mcp-first data. Combines valuation sanity, earnings power, growth narrative, and chart location to decide accumulate, hold, no-add, or avoid.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, valuation, thesis, medium-term, earnings-power]
    related_skills: [vn-stock-trade-setup-mcp, vn-stock-signal-synthesis, vn-stock-earnings-preview-mcp, vn-stock-watchlist-ranker-mcp]
---

# VN Stock Valuation Thesis via stock_mcp

## Overview

Use this skill when you need to answer:
- whether the current price is still cheap / fair / expensive relative to earnings power
- whether the 1-6 month medium-term thesis still has room left
- whether to accumulate gradually, only hold, or avoid new buying even if the business is good

This skill is not a full academic DCF model.
The goal is a practical valuation sanity check for the Vietnam market.

Core principles:
- valuation only decides “what is worth owning / holding”
- technicals and catalysts decide “when to buy”
- a cheap stock does not automatically mean buy now
- a good company may still only be a HOLD / NO ADD if price has already reflected too much

## When to Use

Use when:
- The user asks whether this stock is still cheap, still has upside, or still has a margin of safety.
- You need to evaluate the medium-term thesis after you already have a preliminary chart/catalyst read.
- You need to distinguish a good business from a bad entry.
- You want to support watchlist ranking with a valuation-sanity layer.

Do not use for:
- pure short-term technical entry timing.
- academic valuation requiring a detailed DCF with many assumptions beyond tool data.
- stocks lacking reliable fundamental data.

## Core Tool Bundle

Required:
- `get_finpath_stock_snapshot(symbol="<ticker>")`
- `get_company_data_bundle(symbol="<ticker>")` — Full profile, insider, ownership, dividends (vnstock/KBS source).
- `get_price_data(symbols="<ticker>")`
- `get_technical_analysis(symbol="<ticker>")`

Recommended additions:
- `get_unified_macro_data()` — Unified macro context (Asean source).
- `get_asean_stock_bank_ratios(symbol="<ticker>")` — If it is a bank stock.
- `get_company_financial_data(symbol="<ticker>")`
- `get_company_business_results(symbol="<ticker>")`
- `get_stock_events(symbol="<ticker>", days=180)`
- `get_market_hot_news(symbol="<ticker>")`
- `get_stock_news(symbol="<ticker>")`
- `get_finpath_recommendations(symbol="<ticker>", days=365)`
- `get_stock_money_flow_trend(symbol="<ticker>", period="1M")`

## Mandatory Analysis Order

### 1. Price / chart location first
You must determine upfront:
- whether price is in a discount, fair, or stretched zone on the chart
- whether it is below / between / above MA20-MA50 and the 52-week range
- whether valuation is being “broken” by very poor timing

If valuation looks cheap but the chart is still in strong markdown/distribution, do not jump straight to BUY NOW.

### 2. Earnings power / business quality second
You must review:
- EPS, ROE, ROA, profit margins where available
- recent EBIT / earnings growth
- whether the growth story comes from core business or one-off effects
- whether the industry cycle is supporting or hurting earnings power

### 3. Valuation sanity third
You must evaluate at least these angles when data exists:
- current PE relative to earnings growth rate
- PB relative to ROE / asset quality
- market cap / earnings power / growth runway
- price position versus 52-week range and ATH/ATL

Do not pretend to have absolute precision if data is missing.
State clearly that this is a “sanity check,” not an intrinsic-value precision model.

### 4. Catalyst / event path fourth
Valuation alone is not enough.
You must check:
- which catalyst could unlock rerating
- which catalyst could break the thesis
- whether earnings, AGM, policy, commodity, legal, or capacity-expansion paths are supportive

### 5. Flow / market confirmation fifth
You must examine:
- whether foreign flow confirms accumulation
- whether market regime is favorable for rerating
- whether this is cheap for a reason or gradually being repriced by the market

### 6. Final thesis verdict
The valuation conclusion must be tied to a real action state.

## Expectation State Classification

In addition to the valuation bucket, attach an expectation state:
- POSITIVE EXPECTATION GAP: the market is still conservative, and new data/catalysts are better than old expectations
- NEUTRAL / FAIRLY REFLECTED: price and expectations are relatively balanced
- EXPECTATION-RICH: the narrative is already highly priced in and needs very strong follow-through to justify more upside
- NEGATIVE EXPECTATION RESET: the market is lowering expectations due to earnings/cycle/catalyst failure
- UNCLEAR / MIXED EXPECTATIONS: the data is still noisy and rerating direction is unclear

## Growth Quality Tests

Do not assess rerating only through PE/PB. You must test growth quality:
- are revenue and profit growing in the same direction?
- does operating cash flow confirm earnings?
- do ROE/ROA come from core business or leverage/one-offs?
- is recent growth recurring or driven by unusual factors?
- is the current industry cycle supporting or constraining earnings power?

## Rerating Path

A stock is only worth accumulating if there is a path for the market to rerate it. At minimum, state 1 real rerating path:
- earnings beat / margin recovery
- policy or legal unlock
- industry-cycle upturn / commodity tailwind
- new capacity / new orders / market-share improvement
- foreign flow returning after a neglected period

If you cannot find a clear rerating path, low valuation may simply be dead money or a value trap.

## Value Trap Signals

State cheap-for-a-reason signals directly:
- low PE because the earnings cycle is deteriorating
- cash flow weaker than accounting profit for a long period
- vague catalyst or no rerating path
- balance-sheet / governance / legal overhang keeping the market away
- chart still in markdown/distribution even though valuation looks cheap on paper

## Valuation Buckets

Each stock must belong to 1 bucket only:
- DEEP VALUE / WAIT FOR TECHNICAL TURN
- ATTRACTIVE / ACCUMULATE ON WEAKNESS
- FAIR VALUE / BUY ONLY ON TRIGGER
- HOLD / NO ADD
- OVERVALUED / EXPECTATION RICH
- AVOID / VALUE TRAP RISK

## Interpretation Rules

### A. Cheap but no catalyst
- May be a value trap or dead money
- Usually should not rank highly if the rerating path is missing

### B. Fair valuation + strong growth/catalyst
- Can still be actionable if earnings power is rising quickly
- It does not require an absolutely low PE to be worth buying

### C. Expensive but justified
- Acceptable only if growth, market position, and catalyst are strong enough
- If already expectation-rich and the chart is weak -> HOLD / NO ADD or AVOID

### D. Good company, bad entry
- This is a very common case
- The verdict should be HOLD / NO ADD or BUY ONLY ON TRIGGER, not BUY NOW

### E. Cheap for a reason
- If earnings quality is weak, leverage/problem cycle is large, or the catalyst is vague
- Prefer AVOID / VALUE TRAP RISK

## Output Requirements

Every answer must include:
1. Thesis bucket
2. Current price/chart location
3. Earnings power / business quality summary
4. Valuation sanity check
5. Catalyst for rerating or risk that could break the thesis
6. Flow / market confirmation
7. Final action state
   - ACCUMULATE ON WEAKNESS
   - BUY ONLY ON TRIGGER
   - HOLD
   - HOLD / NO ADD
   - AVOID / NO NEW BUY
8. What would make you upgrade or downgrade the thesis

## Hard Rules

1. Do not call a stock cheap just because PE is low.
2. Do not separate valuation from growth quality and catalyst path.
3. Do not use valuation to override very poor chart timing.
4. Do not give fake-precise targets when data is insufficient.
5. State clearly when fundamental/financial data is missing or suspected to be one-off distorted.

## Common Pitfalls

1. Mistaking low PE for real margin of safety.
2. Ignoring growth quality and one-off earnings.
3. Buying a “cheap” stock even though the market has no reason to rerate it yet.
4. Calling a good business an immediate buy even though price is already expectation-rich.
5. Ignoring market regime that makes the medium-term thesis hard to materialize.

## Suggested Workflow

### Step 1: define the valuation question
- Is the user asking whether it is cheap/expensive, still has upside, or is worth accumulating?

### Step 2: get snapshot + price + technicals
- view valuation in the context of chart location

### Step 3: read earnings power
- prioritize growth, ROE, EPS, margin quality, and one-off risk

### Step 4: connect valuation to rerating path
- valuation only matters if there is a catalyst/thesis for market rerating

### Step 5: convert into an action state
- accumulate / buy on trigger / hold / no add / avoid

## Verification Checklist

- [ ] Checked chart location before concluding on valuation
- [ ] Read earnings power instead of only PE/PB
- [ ] Clearly stated rerating catalyst or lack of catalyst
- [ ] Distinguished cheap from value trap
- [ ] Final verdict is tied to a real action state
- [ ] Stated data limitations clearly if any
