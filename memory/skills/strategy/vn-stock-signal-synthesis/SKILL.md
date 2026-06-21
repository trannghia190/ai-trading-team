---
name: vn-stock-signal-synthesis
description: Use when turning VN stock data into a final recommendation. Enforces analysis order (price/technical -> events/news -> foreign flow -> synthesis), one-direction conclusions, watch-only/no-chase discipline, and action tables with triggers, invalidation, and priority.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, synthesis, recommendation, watchlist, risk-management]
    related_skills:
      - trading-rules-vn-stocks
      - vn-stock-catalyst-execution
      - vn-stock-orderflow-interpretation
      - nn-flow-tracking
      - breadth-divergence-framework
---

# VN Stock Signal Synthesis

## Overview

Use this skill when you need to turn multiple layers of Vietnam stock signals into a single actionable final recommendation.

Objectives:
1. Enforce the correct analysis order.
2. Prevent cherry-picking only confirming indicators.
3. Avoid wishy-washy conclusions that say "don't buy" while implying an entry zone.
4. Make one-direction, clear conclusions with trigger, invalidation, and action priority.
5. Clearly separate "analysis," "watch-only," and "execution-ready recommendation."

This skill is the final synthesis layer sitting above specialized skills for technicals, catalyst, foreign flow, breadth, and orderflow.

It does not replace specialized workflow skills like `vn-stock-trade-setup-mcp`, `vn-stock-catalyst-execution`, or `vn-stock-watchlist-ranker-mcp`.
The correct role of this skill is the final decision layer: after sub-analysis layers have formed signals, this skill forces them into a single final verdict — one direction, with clear trigger/invalidation/priority.

## When to Use

Use when:
- The user asks whether to buy / hold / add to / sell a VN stock ticker.
- You need to synthesize chart + news + foreign flow + orderflow into a final conclusion.
- You are writing a market-monitor, watchlist decision, or end-of-day action plan.
- You have multiple names and need to prioritize which ones are most actionable.

Do not use for:
- Pulling raw data without needing a conclusion.
- Analyzing only one isolated layer such as technical-only or news-only.

## Mandatory Analysis Order

Always follow this order — do not skip steps:

### 1. Price / Technical Context first
You must answer:
- Where is price relative to support/resistance, MA20/MA50, and the 52-week range if available?
- Current trend: accumulation / markup / distribution / markdown?
- Momentum: RSI, MACD, breakout status, vol_vs_avg?
- Is the current risk/reward still attractive enough?

If technicals show poor risk/reward or the stock has already run too far, treat that as a strong counter-signal.

### 2. Events / News / Catalyst next
You must check:
- AGM, earnings, dividends, issuance, legal unlocks, commodity prices, policy, ETF/rebalance
- Whether the catalyst is still upcoming, currently playing out, or already mostly priced in
- Whether there is any event risk that could turn the trade into a trap

Rule:
- Without this step, the buy/add recommendation is incomplete
- Beautiful technicals + bad event = potential trap

### 3. Foreign Flow / Money Flow
You must know at minimum:
- How is today's foreign net buy/sell?
- Over the last 3-5 or 5-10 sessions, is this accumulation or distribution?
- Is this active accumulation, passive ETF flow, or just one noisy day?

Note:
- Do not overreact to a single session
- But if your position is already near the stop and foreigners are selling for multiple consecutive sessions, that is a very strong warning signal

### 4. Breadth / Sector Rotation / Macro Overlay when relevant
This is especially important when:
- Making a new entry based on a theme/sector
- The stock is dependent on risk-on / risk-off regime
- The index is up but breadth is poor

Check when relevant:
- Breadth A/D
- Sector leadership / sector weakness
- VN30 vs mid-cap rotation
- Macro freeze window, CPI/Fed/USD, interbank rates, oil/commodity shock

### 5. Orderflow / Order Book to refine execution
Only used after the higher-level thesis is established.
Use it to answer:
- Is there real supply/demand absorption?
- Is the LO reasonable or is it a market-style execution?
- Is a stop-break a stop-hunt or a real breakdown?

## Emotion / Sentiment Overlay

After the price -> event -> flow layers, add one crowd-state read layer, but do not let it override setup discipline:
- COLD: low turnover, contracting volume, few headlines, crowd indifferent
- STABLE: normal trading, no emotional extremes yet
- WARMING: volume/turnover and sector participation gradually rising, market starting to pay attention
- CROWDED: narrative is clearly hot, many participants looking at the same story, price starting to move away from the clean buy point
- EUPHORIC: turnover/volume and headline heat spiking sharply, risk/reward deteriorating quickly, sell-the-news risk is high

Interpretation:
- Good thesis + COLD is not automatically a BUY; there must also be a bottoming or technical turn signal
- Good thesis + CROWDED/EUPHORIC + chart stretched usually leads to HOLD / NO ADD or WATCH ONLY, not BUY NOW
- Weak thesis + COLD just means cold because the reasons are lacking — not a default contrarian edge

## Trade-State Overlay

When synthesizing, attach one action-context state so the user understands the verdict's frame:
- EARLY / ACTIONABLE
- CONFIRMED BUT EXTENDED
- QUALITY THESIS, POOR TIMING
- VULNERABLE TO SELL-THE-NEWS
- LOW-EDGE / SKIP

## Core Synthesis Rules

### Rule 1: Conclusions must be one-directional
After synthesizing, choose only one of:
- BUY NOW
- BUY ON TRIGGER X
- HOLD
- HOLD / NO ADD
- WATCH ONLY
- REDUCE / TAKE PROFIT
- SELL / EXIT
- NO TRADE

Do not write:
- "Not ready to buy yet but you could watch for entry at zone X"
- "It's pretty okay but the risk is there so if you like it you can still enter"

If the conclusion is "not yet," do not include an entry zone as an implied buy suggestion — unless it is a watch-trigger within the watchlist plan.

### Rule 2: Do not cherry-pick indicators
You must state both:
- Confirming signals
- Counter-signals
- Which signals carry more weight

Example:
- RSI oversold cannot override strong ADX downtrend + falling OBV
- One session of foreign buying cannot override 5-session distribution + price failing to break resistance

### Rule 3: Watch-only is a valid conclusion
If a stock just surged for one session or has a catalyst but not yet enough confirmation:
- WATCH ONLY is a valid conclusion
- Wait for 2-3 sessions of confirmation or a pullback/base
- Do not chase just from fear of missing out

### Rule 4: Poor R:R means HOLD/NO ADD or NO TRADE
Even when the longer-term thesis is intact:
- Existing positions can still be HOLD
- But new positions may be a NO ADD
- These are two separate questions — keep them separate

Typical example:
- "Catalyst intact, target intact, but current price R:R is only 1:0.4 -> HOLD existing position, DO NOT ADD new position."

### Rule 5: Actionability beats verbosity
Every conclusion must include at least 3 things:
- Trigger / action zone
- Invalidation / stop / thesis-failure condition
- Priority level

### Rule 6: Data-status disclosure is mandatory
Before every actionable recommendation, briefly confirm the data status:
- Are MCP/structured data OK or degraded?
- Do you have a current/confirmed close price for each ticker?
- If you are using web/news fallback, state clearly that it is a fallback and confidence is reduced

If you lack a confirmed price for a ticker, do not write a recommendation as if data were complete; only a WATCH / NO ACTION verdict is valid until the data is re-confirmed.

## Decision Tree

### Canonical Action Vocabulary
Use one of these labels consistently:
- BUY NOW
- BUY ON TRIGGER
- WATCH ONLY
- HOLD
- HOLD / NO ADD
- REDUCE / TAKE PROFIT
- SELL / EXIT
- AVOID / TOO EXTENDED
- NO TRADE
- 0 FOCUS BUY NOW (use only for watchlist/market boards, not for a single-name deep dive)

### A. BUY NOW
Use only when:
- Technicals still show sufficient R:R
- Catalyst is clear and not yet fully priced in
- Flow provides reasonable confirmation
- No macro freeze
- Execution style is clear

### B. BUY ON TRIGGER
Use when the thesis is good but the entry point has not yet arrived.
Triggers can be:
- Pullback to support zone
- Breakout close above resistance with volume ≥ 150% avg20
- Foreign selling stops and flips to buying
- 2-3 sessions of successful base-holding

### C. HOLD
Use when:
- You already hold a good position
- Thesis is still intact
- No reason to immediately reduce
- It may not be attractive for a new buy, but it is still fine to hold

### D. HOLD / NO ADD
Use when:
- The existing position is still fine
- But the current price for a new position has poor R:R, is too extended, or NAV is already large

### E. WATCH ONLY
Use when:
- The stock just surged for the first session
- Catalyst is present but still needs confirmation
- You don't want to chase
- You need 2-3 more sessions or a pullback/new base

### F. REDUCE / TAKE PROFIT
Use when:
- Near target or strong resistance
- Distribution is appearing
- Position size exceeds cap
- Catalyst is already mostly priced in

### G. SELL / EXIT
Use when:
- Thesis is broken
- Stop has been definitively breached
- An event/macro development invalidates the thesis
- Persistent poor flow while the safety buffer is already gone

### H. AVOID / TOO EXTENDED
Use when:
- The thesis is not necessarily bad, but the current entry is too far from base and is no longer buyable
- The crowd is too hot, distorting reward/risk
- The stock warrants watching or holding if already owned, but is not suitable for a fresh position

### I. NO TRADE
Use when:
- Data is insufficient
- Macro is too uncertain
- Technicals and catalyst strongly contradict each other
- The trade does not have enough edge

## Distinguish Analysis Modes

### 1. Recommendation mode
When the user directly asks whether to buy/sell.
The output must include a clear verdict.
**Critical:** Always state the current price as the anchor for all entry/stop/target zones. If the tool data is failing and you cannot get a confirmed current price, do NOT fabricate a buy scenario — stop and ask to verify the price. A plan without a verified price reference is meaningless and can be wildly wrong if the market gaps.

### 2. Watchlist mode
When a name is not yet actionable.
The output focuses on:
- why it is not yet entered
- what trigger to wait for
- when to remove from the watchlist

### 3. Portfolio defense mode
When the user is already holding the stock.
The output prioritizes:
- buffer to stop-loss
- catalyst status (intact or broken)
- whether NN flow and breadth are accelerating risk
- next-day defensive actions

## Suggested Output Format

### For a single name
1. Verdict: BUY NOW / HOLD / WATCH ONLY / SELL...
2. Price/technical context
3. Catalyst/news summary
4. Foreign flow assessment
5. Breadth/sector/macro context when relevant
6. Execution plan
   - entry or action
   - stop / invalidation
   - target
   - T+2 note if it is a near-event buy
7. Confirming signals vs. counter-signals
8. Why this verdict wins over the other verdicts

### For multiple names / watchlist
Use a table:
- Ticker
- Verdict
- Short thesis
- Action trigger
- Invalidation
- Priority

## End-of-Day / Market-Monitor Action Table

When writing a synthesis report or end-of-session summary, close with an action table:
- Action
- Ticker
- Precise trigger
- Priority

Example action types:
- SL WATCH — ready to cut
- HOLD
- HOLD / NO ADD
- Trail SL if close < X
- Watchlist only, no chase
- Buy on pullback zone X-Y

## Red-Flag Rules

### 1. If there is a reason not to buy, do not sneak in an implied buy entry zone
Only state a watch-trigger in the correct watchlist format.

### 2. If events/news have not been checked, do not conclude buy
This step is mandatory.

### 3. One hot session is not sufficient confirmation
Default to watch-only if there is no base or follow-through yet.

### 4. Do not use ambiguous language
Avoid: maybe, somewhat leaning, pretty okay, consider if you like.
If needed, attach a probability, but the final verdict must still be decisive.

### 5. Do not equate HOLD with ADD
A stock can be worth holding but not worth buying more.

### 6. Do not omit current price when giving an action plan
If the user requests a specific plan/action, anchor every recommendation to the current price or the most recently confirmed close price. When the current price cannot be verified, state the level of uncertainty and downgrade the verdict to NO TRADE / WATCH ONLY temporarily, rather than continuing to present recommendations as if data were complete.

### 7. When MCP/structured tools fail, web fallback is only for minimal price confirmation
If you must use web fallback due to MCP failure, prioritize getting at least a current/close price confirmed before proceeding. Without a confirmed price, the plan must not be presented as execution-ready.

## Recommended Tool/Data Mapping

Prefer structured data:
- Price snapshot / price board / stock snapshot
- Technical analysis
- Stock events
- Hot news / posts / recommendations for catalyst context
- Money flow / foreign trading
- Market breadth / sector overview / market top
- Intraday trades / orderbook for execution refinement

Use web/news extraction only when structured data is insufficient for catalyst/news.

## Verification Checklist

- [ ] Followed the correct order: price -> events -> foreign flow -> synthesis
- [ ] Stated both confirming and counter-signals
- [ ] Final verdict belongs to only one clear group
- [ ] Did not sneak in an entry zone when verdict is no-buy or watch-only
- [ ] Clearly separated HOLD from NO ADD when applicable
- [ ] Included trigger, invalidation, and priority
- [ ] Considered breadth/sector/macro when the thesis depends on regime
- [ ] Added T+2 note for short-term catalyst buys

## Source Patterns

This skill was distilled from valuable patterns in the Analysis archive:
- Mandatory analysis order: price/technical -> events/news -> foreign flow -> synthesis
- Lesson BSR 23/3/2026: avoid contradictory recommendations and cherry-picking indicators
- Watch-only / no-chase discipline in decision memos
- Action table with trigger/priority in end-of-session market monitors
- Separating HOLD vs NO ADD when catalyst is intact but R:R is tight
