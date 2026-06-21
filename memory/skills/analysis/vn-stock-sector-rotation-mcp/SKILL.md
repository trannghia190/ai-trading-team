---
name: vn-stock-sector-rotation-mcp
description: Use when selecting Vietnam stock leaders and laggards within sectors using stock_mcp-first data. Combines breadth, sector performance, relative price structure, catalysts, and foreign-flow rotation to rank actionable names without chasing leaderboard noise.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, stock-mcp, sector-rotation, ranking, watchlist, foreign-flow]
    related_skills: [vn-stock-market-monitor-mcp, nn-flow-tracking, breadth-divergence-framework]
---

# VN Stock Sector Rotation via stock_mcp

## Overview

Use this skill when you need to select leader/laggard stocks within one sector or across multiple sectors in the Vietnam market.

Objectives:
- identify which sectors are actually attracting money flow
- select the strongest stock inside the strongest group
- avoid buying weak names just because they are "in the same benefiting sector"
- build a 2-5 name actionable shortlist from market-monitor output or a broad watchlist

## When to Use

Use when:
- The user asks which sector is leading and which stock should be chosen.
- You need to rank 5-20 names and narrow them down to 2-3 high-conviction names.
- You need to distinguish true leaders from laggards merely bouncing technically.
- Market monitor detects sector rotation and needs a stock-picking layer.

Do not use for:
- Doing a very deep analysis of a single stock from scratch.
- Reading only top gainers/volume leaderboards without cross-validation.

## Core Tool Bundle

Required:
- `get_finpath_market_breadth()`
- `get_asean_industry_cashflow()` — Sector money flow (Asean source).
- `get_asean_fear_greed_index()` — Market sentiment.
- `get_finpath_sector_overview()`
- `get_finpath_market_top(criteria="top_value")`
- `get_finpath_market_top(criteria="foreign_buy")`
- `get_finpath_market_top(criteria="foreign_sell")`

Recommended for shortlisted names:
- `get_price_data(symbols="<comma-separated shortlist>")`
- `get_technical_analysis(symbol="<ticker>")`
- `get_stock_events(symbol="<ticker>", days=90)`
- `get_stock_money_flow_trend(symbol="<ticker>", period="1M")`
- `get_finpath_stock_snapshot(symbol="<ticker>")`
- `get_finpath_market_top(criteria="volume_surge")`
- `get_finpath_market_top(criteria="top_gainers")`
- `get_finpath_market_top(criteria="near_52w_high")`

## Mandatory Analysis Order

### 1. Market regime / breadth first
You must know:
- whether the market is broad risk-on or only a narrow rally
- whether breadth supports stock-picking beyond the pillars
- whether the environment favors breakout leaders or only defensive behavior

### 2. Sector rotation second
You must identify:
- which top sectors are genuinely attracting money
- whether a sector is rising because of 1-2 pillars or because participation is broad
- which sectors are seeing capital outflow or distribution

### 3. Relative stock strength within sector
For each shortlisted stock, compare:
- chart location
- breakout/base quality
- volume quality
- proximity to 52-week highs / ability to hold MA20-MA50
- resilience during recent pullbacks

### 4. Catalyst / event check
Do not choose a leader based on price alone.
You must check:
- whether the stock has its own catalyst
- whether the sector catalyst really transmits to that stock
- whether event risk is distorting the setup

### 5. Foreign flow / money flow check
You must know:
- which stock foreigners are prioritizing within the group
- whether money flow confirms relative strength
- whether rising price without flow confirmation may just be a weak bounce

### 6. Ranking / action layer
You must finish with a clear ranking.

## Theme Lifecycle

Before choosing a leader, determine which phase the theme/sector is in:
- IGNITION: new catalyst, only a few names confirming, but leaders are starting to emerge
- EXPANSION: many names in the sector confirming together, internal breadth improving
- BROAD PARTICIPATION: money flow spreading widely, but crowding risk beginning to rise
- DIVERGENCE: only a few leaders still holding price, many secondary names fading
- FADE / RETREAT: narrative cooling, supply increasing, breakouts more likely to fail

## Stock-to-Theme Relevance

Each stock in the theme must be tagged by relevance level:
- DIRECT BENEFICIARY: directly benefits from the policy/order/cycle
- SECOND-ORDER BENEFICIARY: indirectly benefits but still has a real thesis
- WEAK CONCEPT ATTACH: only tagged to the story, lacking fundamental evidence
- SYMPATHY MOVE: moving with sector price action but lacking its own catalyst and durable confirmation

## Leader Validation

A stock should only be called a leader when it has all of the following:
- the sector/theme is genuinely strong, not just cosmetically lifted by 1-2 pillars
- price is stronger than most peers in the group
- liquidity/turnover/volume confirms real attention
- real linkage to the sector catalyst or its own catalyst
- flow does not contradict relative strength

If it is missing 2 or more factors, downgrade it to secondary leader or sympathy move.

## Stock Ranking Buckets

Each stock must belong to only 1 bucket:
- SECTOR LEADER / ACTIONABLE
- THEME BENEFICIARY / BUY ON TRIGGER
- SYMPATHY MOVE / LOW CONVICTION
- HOLD IF OWNED / NO NEW BUY
- LAGGARD BOUNCE / LOW PRIORITY
- AVOID / DISTRIBUTION RISK

## Ranking Rules

1. Prefer a leader in a strong sector over a laggard in a strong sector.
2. Do not buy a laggard just because it “has not gone up much yet.”
3. If market breadth is narrow, downgrade mid-cap breakouts lacking flow confirmation.
4. Stocks with catalyst + flow + strong chart get the highest priority.
5. If quality is similar, prefer the name with better liquidity and easier execution.

## Output Requirements

Every answer must include:
1. Market regime
2. Leading / weak sectors
3. Ranked stock table
   - Symbol
   - Bucket
   - Why
   - Trigger / note
   - Priority
4. The 2-3 best names to focus on
5. The names to avoid or not chase

## Hard Rules

1. Do not stop at a leaderboard-based shortlist.
2. Do not call a stock a leader if chart and flow do not confirm.
3. Do not use “hasn't gone up much yet” as the main laggard thesis.
4. If breadth is poor, warn about false-breakout risk for mid-caps.

## Common Pitfalls

1. Mistaking index-pillar strength for genuine sector-wide participation.
2. Choosing a weak laggard because it feels like there is more upside left.
3. Ignoring stock-specific event risk inside the same sector.
4. Reading one session of top buy/top sell flow and concluding a longer rotation trend.

## Verification Checklist

- [ ] Checked market breadth first
- [ ] Identified real sector rotation
- [ ] Validated each stock by chart + catalyst + flow
- [ ] Ranked each stock into 1 clear bucket
- [ ] Have 2-3 final focus names
- [ ] Included avoid / no-chase warnings
