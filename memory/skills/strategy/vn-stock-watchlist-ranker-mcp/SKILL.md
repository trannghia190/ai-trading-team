---
name: vn-stock-watchlist-ranker-mcp
description: Use when ranking a 5-20 name Vietnam stock watchlist into 2-3 high-conviction actionable focus trades using stock_mcp-first data. Filters out noise, enforces no-chase discipline, and separates BUY-ready names from HOLD-only and watch-only setups.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, watchlist, ranking, prioritization, swing-trading]
    related_skills: [vn-stock-trade-setup-mcp, vn-stock-signal-synthesis, vn-stock-sector-rotation-mcp, trading-rules-vn-stocks]
---

# VN Stock Watchlist Ranker via stock_mcp

## Overview

Use this skill when you have a 5-20 name watchlist and need to narrow it down to the 2-3 names most worth focusing on.

Objectives:
- turn a broad list into an actionable shortlist
- avoid being distracted by top gainers, volume leaders, or FOMO names
- clearly separate names that are buyable now, names that should only be watched, and names that are only worth holding if already owned
- force the final conclusion to include explicit priority order

This skill does not replace deep analysis of each individual stock.
It is the ranking and prioritization layer before execution or sizing.

## When to Use

Use when:
- The user provides a multi-name watchlist and asks which names deserve the most focus.
- You need to cut 10-20 names from market-monitor or sector-rotation output down to 2-3 high-conviction names.
- You need to build a start-of-day or end-of-day action board for swing trading.
- You need to answer: “If I can only choose 2-3 names, which ones should I pick?”

Do not use for:
- Doing a full deep dive on a single stock from scratch.
- Reading only top gainers or top volume leaderboards without cross-validation.
- Making a full portfolio sizing decision for an existing multi-position portfolio.

## Core Tool Bundle

Required at the watchlist level:
- `get_finpath_market_breadth()`
- `get_finpath_sector_overview()`
- `get_price_data(symbols="<comma-separated watchlist>")`

Required for each shortlisted name:
- `get_technical_analysis(symbol="<ticker>")`
- `get_stock_events(symbol="<ticker>", days=90)`
- `get_stock_money_flow_trend(symbol="<ticker>", period="1M")`

Recommended additions:
- `get_finpath_stock_snapshot(symbol="<ticker>")`
- `get_market_hot_news(symbol="<ticker>")`
- `get_stock_news(symbol="<ticker>")`
- `get_finpath_market_top(criteria="foreign_buy")`
- `get_finpath_market_top(criteria="foreign_sell")`
- `get_finpath_market_top(criteria="volume_surge")`

## Mandatory Analysis Order

### 1. Market regime first
You must determine upfront:
- whether the environment is broad risk-on, narrow rally, mixed, or risk-off
- whether breadth supports opening new positions
- whether the current environment favors breakout leaders or calls for defensive / watch-only behavior

If breadth is weak or the market is risk-off, you should downgrade nearly all mid-cap breakout names.

### 2. Sector / theme context second
You must know:
- which names belong to sectors currently favored by money flow
- which names are only rising individually inside weak sectors
- whether the catalyst is stock-specific or merely piggybacks on a sector headline

### 3. Price / technical quality third
For each stock, you must answer:
- whether chart location is attractive
- whether it is in accumulation / breakout / extended / distribution
- whether the current risk/reward is still attractive
- whether it is already too far above MA20 or the nearest resistance

### 4. Event / news check fourth
You must check:
- whether there is a real catalyst
- whether that catalyst is still ahead, near-term, or already mostly priced in
- whether there is event risk that distorts the setup

### 5. Foreign flow / money flow fifth
You must know:
- whether foreign flow confirms relative strength
- whether 1M accumulation / distribution supports the setup
- whether strong price without flow confirmation should force a downgrade

### 6. Final ranking / action layer
End with an explicit ranking so the user does not have to infer the conclusion.

## Ranking Buckets

Each stock must be placed into only 1 bucket:
- FOCUS BUY NOW
- FOCUS BUY ON TRIGGER
- WATCH ONLY
- HOLD / NO ADD IF OWNED
- AVOID / TOO EXTENDED
- REMOVE / LOW EDGE

Mapping to canonical action vocabulary:
- FOCUS BUY NOW -> BUY NOW
- FOCUS BUY ON TRIGGER -> BUY ON TRIGGER
- WATCH ONLY -> WATCH ONLY
- HOLD / NO ADD IF OWNED -> HOLD / NO ADD
- AVOID / TOO EXTENDED -> AVOID / TOO EXTENDED
- REMOVE / LOW EDGE -> NO TRADE / remove from shortlist context

## Theme / Expectation / Emotion Overlays

When ranking a watchlist, add 3 supporting layers:
- THEME LIFECYCLE: ignition / expansion / divergence / fade
- EXPECTATION STATE: positive gap / fairly reflected / expectation-rich / negative reset
- EMOTION STATE: cold / stable / warming / crowded / euphoric

Meaning:
- even if a stock is strong, if the theme is already diverging and emotion is already crowded, it should be downgraded to BUY ON TRIGGER or WATCH ONLY
- expectation-rich plus an extended chart must not be ranked FOCUS BUY NOW
- a risk-off or overheated market can validly lead to the conclusion of “0 focus buy now”

## Ranking Rules

1. Prioritize stocks that have all 3 layers of confirmation:
- good chart location
- valid catalyst / news
- confirming flow

2. Do not choose a laggard just because it “has not gone up much yet.”

3. If 2 stocks are similar in quality, prefer the one with:
- better liquidity
- easier execution
- clearer catalyst
- less foreign distribution

4. A stock that is too extended must not be ranked FOCUS BUY NOW.
At most, it can be FOCUS BUY ON TRIGGER or SECONDARY / WATCH ONLY.

5. If market regime is poor:
- the number of focus names must shrink
- it can be perfectly valid if the final shortlist has only 0-1 actionable names

6. Clearly separate:
- stocks that are good to hold
- stocks that are good to buy fresh
These are not the same thing.

## Output Requirements

Every answer must include:
1. The market regime
2. The sectors/themes supporting or blocking the watchlist
3. A ranking table for all names
   - Symbol
   - Bucket
   - Why
   - Trigger / note
   - Priority
4. The final top 2-3 focus names
5. The names that must be no-chase
6. The names that should be removed from the shortlist

## Hard Rules

1. Do not rank only by intuition or by same-day price gain.
2. Do not pick a leader that is already too extended without a no-chase note.
3. Do not end with vague conclusions like “any of these could work.”
4. If no stock has enough edge, explicitly say “no focus buy now.”
5. Do not let one session of foreign net buying override clear chart distribution.

## Common Pitfalls

1. Keeping too many “pretty okay” names instead of forcing elimination.
2. Picking a laggard in a strong sector just because it seems to have more upside left.
3. Putting a stock into top focus even though it is already far past the buy point.
4. Ignoring event risk for each stock inside the same watchlist.
5. Failing to distinguish watchlist ranking from a single-stock deep dive.

## Suggested Workflow

### Step 1: read the broad watchlist
- Run breadth and sector context
- Pull price snapshots for the full list

### Step 2: quickly eliminate low-edge names
Remove or downgrade names that are:
- illiquid
- clearly in distribution
- backed by vague catalysts
- fighting the sector or market regime
- already too extended

### Step 3: deeply analyze the remaining 3-7 names
For each remaining name, review:
- technicals
- events/news
- money flow

### Step 4: force the shortlist down to 2-3 focus names
Keep only the names with the best remaining edge.
If you cannot compress it to 2-3 names, the ranking is not yet strict enough.

## Preferred Final Language

Prefer clear final states:
- Focus buy now
- Focus buy on trigger
- Watch only
- Hold if owned / no new buy
- Remove from shortlist

## Verification Checklist

- [ ] Checked market regime before ranking
- [ ] Used sector/theme context to avoid mechanical ranking
- [ ] Properly validated the final 3-7 names with technicals + event + flow
- [ ] Forced the shortlist down to 2-3 focus names or clearly said no stock has enough edge
- [ ] Added no-chase warnings for extended names
- [ ] Clearly separated stocks worth holding from stocks worth buying fresh
