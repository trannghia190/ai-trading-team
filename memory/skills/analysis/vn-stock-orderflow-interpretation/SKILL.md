---
name: vn-stock-orderflow-interpretation
description: Use when analyzing VN stocks with intraday tape/order-book context and you need to interpret accumulation, markup, distribution, stop-hunt, and buy/sell absorption before suggesting entry, stop-loss action, or execution style.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, orderflow, tick-data, execution, intraday]
    related_skills: [trading-rules-vn-stocks, nn-flow-tracking, vn-stock-market-monitor-routine]
---

# VN Stock Orderflow Interpretation

## Overview

Use this skill to read orderflow / tick data / order book for Vietnam stocks in a battle-tested way, not just by looking at the end-of-day chart.

Objectives:
1. Determine which phase the stock is in: accumulation / markup / distribution / markdown.
2. Distinguish fake stop-hunts from real breakdowns.
3. Use tick data + order book to choose a more precise entry price within a wide technical zone.
4. Connect orderflow with foreign flow, technical context, and execution decisions.

This is not a hyper-short-term scalp skill. It serves swing/concentrated trading, where the intraday tape is used to improve entry/exit quality and to avoid bad decisions caused by looking at charts that are too coarse.

## When to Use

Use when:
- You need to answer "at what price is entry reasonable?" — not just "what zone is reasonable?"
- Price is touching support/resistance and you need to know if there is real supply/demand absorption.
- Price has intraday stop-triggered but it is unclear whether it is a stop-hunt or a real breakdown.
- There is strong foreign flow but price is behaving strangely, and you need more tape reading.
- You are deciding between LO vs. market-style execution.

Do not use for:
- Decisions based on 1-2 individual ticks.
- Continuous intraday scalp-style trading.
- Ignoring larger technical/sector/catalyst context.

## Mandatory Analysis Order

When using this skill, maintain the higher-level analysis order:
1. Price/technical context first
2. Then events/news/catalyst
3. Then foreign flow
4. Only then use orderflow to refine execution

Orderflow is the decision-refinement layer, not a thesis-replacement layer.

## Recommended Inputs

Prefer structured data from MCP/tools:
- Real-time price / bid-ask / intraday trades
- Foreign buy/sell intraday or session net
- Technical context: support/resistance, RSI, volume, breakout level

If any of the following 3 layers are missing, you must state that confidence is reduced:
- price structure
- flow context
- intraday tape/orderbook

## 4 Phase Orderflow

### 1. Accumulation
Signs:
- Price is sideways for 2-3 sessions or multiple intraday waves without breaking the base
- Volume gradually increasing but not exploding chaotically
- Clear bids holding at the lower zone
- Each dip is absorbed relatively quickly
- Foreign or institutional buying is subtle — not necessarily a hot top yet

Meaning:
- This is the best phase to pre-position for a swing if catalyst and technicals are compatible.

Action:
- Split orders into 2-3 parts
- Prefer LO near below the real support zone
- No need to wait for breakout to start a position if R:R is good enough

### 2. Markup
Signs:
- Large burst buys appear in a few seconds/minutes
- Price jumps quickly 1-2% or more
- Sell walls are repeatedly breached
- Market sentiment shifts from doubt to excitement

Meaning:
- The acceleration phase. Without a strong catalyst, retail chasing here usually has poor R:R.

Action:
- For normal swing: avoid chasing, wait for pullback
- For a confirmed catalyst day: binary execution is possible if the thesis is strong enough

### 3. Distribution
Signs:
- Price is at high zone / resistance but not moving further
- Many block sells or many orders at the same second/price on the sell side
- After the excitement wave, price is repeatedly held down
- Foreign flow may still be buying but price is reacting weaker than expected

Meaning:
- Short-term upside probability decreases, especially for new positions.

Action:
- Do not buy new positions unless there is a very special catalyst
- If already holding, consider partial take-profit or tightening the trailing stop

### 4. Markdown / Real Breakdown
Signs:
- Price breaks the support base and does not recover meaningfully
- Sell pressure is sustained, not just a one-wave sweep
- Bid walls are withdrawn or consumed without re-establishing
- Foreign investors stop supporting or flip to net selling

Meaning:
- This is no longer healthy consolidation.

Action:
- Prioritize defense
- Do not catch a falling knife just because the price is a few lines cheaper

## How to Read Tick Data and Order Book

### 1. Find real support zones, not just chart support
Process:
1. Identify the broad technical zone from the chart, e.g. 26.3-26.5
2. Use intraday trades + orderbook to see where there is a real bid wall / absorption
3. Place entry slightly below the support zone instead of charging straight into where absorption is happening

General example:
- If there is a large bid wall at 26.400, a better entry might be 26.350 instead of 26.400
- Reason: reduces bad R:R if the support zone is tested multiple times

### 2. How to identify block orders / smart-money activity
Strong signals:
- Multiple orders at the same second, same price
- Diverse volume but very large cumulative total
- Total volume in 1 second unusually large relative to normal tape

Interpretation:
- Block buy after a shakeout = supply absorption
- Block sell at the top + price cannot advance further = distribution
- A single large order alone is not enough to conclude; need to see the immediate price reaction

### 3. Buy Absorption vs. Sell Sweep
Buy absorption:
- There is heavy selling but price does not break down significantly
- After the sweep, a large/even buy cluster appears and price bounces back
- The sell side gradually thins over time

Sell sweep / real breakdown:
- Price breaks through and keeps going, no meaningful recovery
- Selling volume does not decrease after 15-30 minutes
- Supporting bids disappear or are too weak

## Stop-Hunt Filter

Apply when price intraday-triggered the stop but the larger thesis is not broken.

### Typical stop-hunt signals
- Price hit/passed a common stop level then recovered quickly within the same session
- Foreign investors are still net buying or at least not selling in agreement
- Clear buy absorption after the sweep
- The overall market is not in a systemic crash state

### Process
1. Do not auto-cut on the first tick that crosses the stop
2. Observe for another 15-30 minutes
3. Check:
   - Is foreign flow still buying?
   - Is there a block buy absorbing?
   - Is sell volume thinning?
4. Cut if:
   - Price continues lower without recovery
   - Selling volume remains dominant
   - Foreign flow flips to net selling / thesis is broken
5. Hold if:
   - Clear absorption appears and price recovers quickly
   - Macro context has not suddenly turned bad

### Do not apply this filter when
- New bad fundamental news breaks that same day
- VN-Index / market breadth breaks down hard in a systemic selloff
- The stock has already lost its catalyst or is in a clear markdown phase

## How to Choose a Precise Entry Price

### 5-step framework
1. Identify the thesis and phase
2. Identify support/resistance zones on the chart
3. Read the tape/orderbook to find real bid support or sell wall
4. Calculate R:R from expected entry to stop and target
5. Choose execution style: split LO or market-style

### Principles
- Good entry = below the absorption zone, not right into where absorption is occurring
- Do not sacrifice R:R just to get filled
- If the stop has to be too close because the entry is poor → skip the trade
- Minimum target R:R is roughly 1:2.5, better is 1:3+

## Combining with Foreign Flow

Orderflow must not be read in isolation from foreign flow.

Useful interpretation patterns:
- Foreign net buying + price holding base + block buy support = high-quality accumulation
- Strong foreign net buying but price cannot advance at resistance = may be facing distribution or large supply
- Foreign net selling but price does not break base = domestic/prop absorption is present, not immediately bearish

## Choosing Order Type

### LO (Limit Order) is appropriate when
- The stock is in accumulation/base, not yet in strong breakout
- There is a clear pullback zone and real bid support
- You are comfortable with the possibility of not getting filled
- It is a normal swing trade, not a catalyst explosion day

### Avoid LO when
- A major catalyst just confirmed and the stock is in execution mode
- Breakout/hot stock is clear, thesis is binary
- LO is being used as a half-committed way between "really want in" and "not daring to enter"

## Suggested Output Format

When answering the user, follow this template:
1. Current phase: accumulation / markup / distribution / markdown
2. Main tape signals: block buy/sell, absorption, sweep, wall
3. Combined with foreign flow: agreement or contradiction
4. Viable entry zones and preferred entry price
5. Stop / target / R:R
6. Appropriate order type: split LO or market-style
7. Conditions that invalidate the thesis

## Common Pitfalls

1. Seeing one large order and concluding too early.
Need to watch the immediate price reaction after that order.

2. Using orderflow to fight a thesis that has already broken.
Tape only refines execution — it cannot save a wrong thesis.

3. Confusing stop-hunt with a real breakdown.
Must check absorption, foreign flow, and market context.

4. Raising LO right into the zone being sold into.
Seeing a clear sell wall/supply and still raising the price worsens R:R.

5. Over-trusting intraday noise.
Without price structure and catalyst context, orderflow easily leads to overtrading.

## Verification Checklist

- [ ] Identified the current phase of the stock
- [ ] Cross-checked orderflow against price structure and foreign flow
- [ ] Distinguished accumulation/absorption from distribution/breakdown
- [ ] Calculated stop, target, and R:R before stating entry price
- [ ] Chosen order type suited to the context, not using LO by habit
- [ ] Clearly stated conditions that invalidate the thesis
