---
name: vn-stock-estimate-consensus-mcp
description: Use when evaluating Vietnam-stock recommendation consensus from Finpath expert history. Synthesizes action mix, source breadth, recency, entry clustering, and recommendation persistence into a decision-useful consensus read for pre-trade, watchlist, and thesis review workflows.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, consensus, recommendations, finpath, stock-mcp]
    related_skills:
      - vn-stock-earnings-preview-mcp
      - vn-stock-valuation-thesis-mcp
      - vn-stock-watchlist-ranker-mcp
      - vn-stock-signal-synthesis
---

# VN Stock Estimate / Consensus MCP

## Overview

Use this skill to read Vietnam-stock recommendation consensus from Finpath recommendation history via `stock_mcp`.

This is not a copy of a US-style analyst estimate revision workflow. Current data is not stable enough in `targetPrice`, `upside`, or EPS-revision history. So the correct role of this skill is to:
- read action consensus (buy vs sell)
- read recommendation-source breadth
- read recency / persistence of recommendation flow
- read buy/sell price clusters
- turn those signals into a confirming or rejecting overlay for trade setup / watchlist / thesis review

Use this skill as an "expert-flow / recommendation-consensus overlay," not as a standalone valuation layer.

## When to Use

Use when:
- The user asks whether recommendation consensus for a VN stock is supportive or not.
- You need to know whether a setup is confirmed by multiple sources or is just scattered noise.
- You want an extra validation layer for pre-trade or watchlist ranking.
- You need to check whether the medium-term thesis is still supported by recent recommendation flow.
- You want to review whether fresh recommendations are leaning BUY, SELL, or mixed.

Do not use for:
- replacing price/technical analysis
- replacing event/news review
- assuming a standardized target-price consensus when the data does not support it
- concluding buy just because many people also recommend buying

## Primary Data Source

Use `get_finpath_recommendations(symbol, days=365)` as the main source.

Current observed data quality:
- strong in: `action`, `buyPrices`, `sellPrices`, `source`, `createdAt`, `updatedAt`, `sameCount`
- sometimes available: `reasons`, `risks`, `summaries`
- weak / unstable in: `targetPrice`, `upside`, `expectedReturn`

Therefore this skill must anchor on action mix + price cluster + recency + source breadth.

## Mandatory Analysis Order

Do not change the order:
1. Recommendation dataset quality check
2. Action mix and source breadth
3. Recency and persistence
4. Entry / exit price clustering
5. Qualitative reason/risk scan if available
6. Consensus verdict
7. Hand-off back into synthesis layer

## Step 1: Recommendation Dataset Quality Check

Before interpreting, check:
- total number of records in the `days` window
- number of truly distinct sources
- ratio of records that include `buyPrices`
- ratio of records that include `sellPrices`
- whether `reasons` / `risks` are usable
- how recent the newest record is
- **UNKNOWN source ratio:** If >30% of sources are `UNKNOWN`, you must warn that source-breadth reliability is weaker.

### Minimum interpretation thresholds

| Quality tier | Rule |
|---|---|
| Strong | >= 20 records and >= 5 distinct sources |
| Moderate | 8-19 records and >= 3 distinct sources |
| Weak | < 8 records or < 3 distinct sources |

If dataset = Weak:
- conclusions should remain only a low-confidence overlay
- do not use this skill to upgrade a weak setup into a BUY

## Step 2: Action Mix and Source Breadth

At minimum, separate:
- total `buy`
- total `sell`
- buy ratio = buy / (buy + sell)
- sell ratio = sell / (buy + sell)
- number of distinct recommendation sources
- whether the flow relies too heavily on 1 repeated source

### Interpretation guide

| Pattern | Meaning |
|---|---|
| High buy ratio + many distinct sources | positive supportive consensus |
| High buy ratio but only 1-2 dense repeat sources | likely echo / persistence from a few sources, not real breadth |
| Mixed buy/sell | fragmented consensus, should not be over-trusted |
| Sell rising recently even though longer history leans buy | thesis may be deteriorating or at least confidence is weakening |

### Anti-misread rule

Do not treat 20 posts from the same expert as “20 independent votes.”
You must separate:
- record count
- distinct-source count

## Step 3: Recency and Persistence

You need to read:
- how long ago the latest recommendation was
- what the action mix looks like over the last 30 days
- what the action mix looks like over the last 90 days
- whether recommendation flow is still ongoing or has become stale

### Interpretation guide

| Pattern | Meaning |
|---|---|
| many fresh buys within 30 days | support close to the current moment |
| heavy buy history but concentrated 4-8 months ago | stale consensus, should not be used as a strong signal |
| recent sells appearing after a chain of buys | warning of deterioration / profit-taking / invalidation |
| records spread evenly across many months | thesis persistence is higher than a one-off call |

## Step 4: Entry / Exit Price Clustering

Because target price is unstable, you must lean on `buyPrices` / `sellPrices`.

At minimum extract:
- **Recent Buy Cluster (90d):** median/average of records within the most recent 90 days.
- **Full-Window Buy Cluster:** median/average across the full 365-day history.
- median sell cluster if available.
- where current price sits relative to those buy clusters.

### Outlier Filtering Rules (Robustness)

Before calculating median/cluster, remove noisy values:
- **Bad / wrong-unit prices:** Remove prices < 0.6x or > 1.6x current price.
- **Too-old prices:** If enough fresh data exists, prioritize 90d and 180d clusters; treat clusters >270d as only weak supporting evidence.

### Practical output types

1. `Current price still inside consensus buy cluster`
2. `Current price slightly above consensus buy cluster`
3. `Current price far above consensus buy cluster -> consensus no longer supports chasing`
4. `Current price near historical sell cluster -> upside may already be partly harvested`

### Critical rule

This skill must preserve no-chase discipline:
- if current price is already meaningfully above the buy cluster of most recent recommendations, the verdict must not lean bullish just because buy ratio is high

## Step 5: Qualitative Reason / Risk Scan

If `reasons`, `risks`, `desc`, or `summaries` contain data:
- scan whether the main theses repeat in recognizable clusters
- roughly classify them into:
  - technical breakout / accumulation
  - earnings growth / valuation
  - sector tailwind
  - event/catalyst
  - defensive/trading-only
- scan repeated risks:
  - weak market
  - overbought / extended
  - earnings/event risk
  - liquidity / selling pressure / stop-loss risk

No heavy NLP needed. The goal is simply to identify 2-4 prominent reasoning clusters.

## Consensus Verdict States

Choose only ONE verdict:
- STRONG POSITIVE CONSENSUS
- MODERATE POSITIVE CONSENSUS
- MIXED / FRAGMENTED CONSENSUS
- STALE POSITIVE CONSENSUS
- DETERIORATING CONSENSUS
- INSUFFICIENT CONSENSUS DATA

### Decision rules

#### STRONG POSITIVE CONSENSUS
Use only when:
- dataset quality = Strong
- buy ratio clearly exceeds sell
- source breadth is wide enough
- recency is good
- current price is not too far above the consensus buy cluster

#### MODERATE POSITIVE CONSENSUS
Use when:
- buy ratio leans positive
- but breadth or recency is only moderate
- or price has already drifted somewhat away from the buy cluster

#### MIXED / FRAGMENTED CONSENSUS
Use when:
- buy/sell is not clearly separated
- or many sources exist but the thesis is strongly fragmented

#### STALE POSITIVE CONSENSUS
Use when:
- history clearly leans buy
- but most recommendations are old
- and recent confirmation is thin

#### DETERIORATING CONSENSUS
Use when:
- recent sell / clear / reduce calls are increasing
- or recent buy ratio is clearly worse than the longer history

#### INSUFFICIENT CONSENSUS DATA
Use when:
- data is thin or source count is low
- there is not enough evidence for a meaningful conclusion

## How to Use This Skill with Other VN Skills

### With `vn-stock-trade-setup-mcp`
- the setup tells you R:R, structure, and trigger
- this skill tells you whether recommendation flow supports it
- consensus must not override a bad technical setup

### With `vn-stock-watchlist-ranker-mcp`
- use consensus as a secondary ranking factor
- not as the #1 primary factor

### With `vn-stock-valuation-thesis-mcp`
- valuation/thesis tells you whether upside still exists
- this skill tells you whether expert-flow is still aligned recently

### With `vn-stock-signal-synthesis`
- this skill is a supporting input
- the final verdict must still follow: price -> events -> foreign flow -> synthesis

## Recommended Output Format

### Single stock output
1. Data quality
2. Action mix
3. Source breadth
4. Recency / persistence
5. Buy/sell price cluster
6. Repeating reasons / risks
7. Consensus verdict
8. Implication for current decision

### Example implication lines
- `Consensus supports the setup, but current price is already above the recent buy cluster -> HOLD / NO CHASE.`
- `Consensus remains positive and recent, with multiple distinct sources clustering buys near the current zone -> supportive for BUY ON TRIGGER, not sufficient alone for BUY NOW.`
- `Historical consensus is positive but stale; treat as weak confirmation only.`
- `Recent sell calls and thinning buy flow suggest deteriorating consensus; do not use old bullish calls as validation.`

## Common Pitfalls

1. Confusing record count with source breadth.
2. Using consensus to override technical deterioration.
3. Treating old data as new signal.
4. Assuming target price/upside exists reliably in the dataset.
5. Concluding bullish even though current price is already far above the nearest buy cluster.
6. Counting repeated small updates from the same expert as many independent votes.

## Verification Checklist

- [ ] Checked dataset quality before interpretation
- [ ] Separated record count from distinct-source count
- [ ] Read recency 30d vs 90d, not just the whole history
- [ ] Mapped current price into buy/sell clusters
- [ ] Did not use consensus as a substitute for price/event/flow analysis
- [ ] Final verdict belongs to one clear state only
- [ ] Final implication preserves no-chase discipline
