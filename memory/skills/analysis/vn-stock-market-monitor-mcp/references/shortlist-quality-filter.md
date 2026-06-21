# Shortlist Quality Filter

## Purpose

This reference standardizes how to turn a candidate list from breadth, sector, and leaderboard tools into a high-quality actionable shortlist.

Goals:
- reduce false positives from illiquid names
- prevent raw `top_gainers` and `top_volume` output from driving the market verdict
- keep the candidate list clearly separate from the action list

## Two-Layer Filter

### Layer 1 — Liquidity floor

#### HOSE / HNX
- By default, do not place the name on the actionable shortlist if `day_value_ty < 50`
- Exceptions apply only when:
  - the catalyst is a very clear direct-beneficiary story
  - the setup is close to confirmation
  - the move is not a one-bar anomaly

#### UPCOM
- By default, do not place the name on the actionable shortlist if `day_value_ty < 100`
- Even above 100 billion VND of trading value, it still needs:
  - direct catalyst
  - repeatable liquidity rather than a one-session burst
  - price action that is not spike-and-fade

#### Why this matters
- Many `top_gainer`, `top_loser`, and `volume_surge` results are low-quality noise by institutional standards.
- Those names may still be useful for market color, but they are not good enough for the action shortlist.

## Layer 2 — Secondary validation

The candidate must pass four questions:
1. Is the technical state clean?
2. Does it have breadth or sector support?
3. Are foreign flow or money flow not strongly opposing it?
4. Is the move still buyable, or is it already extended or crowded?

### Scoring interpretation
- Pass 4/4
  - it can qualify for `BUY ON TRIGGER`
- Pass 3/4
  - it is usually `WATCH ONLY` or `HOLD / NO ADD`
- Pass <=2/4
  - remove it from the action shortlist

## Red Flags

Downgrade aggressively if one or more of these signs appear:
- unusually low liquidity
- the move depends on only one volume-spike session
- peer names in the sector do not confirm
- market breadth does not support it
- strong foreign selling is pushing against the move
- the chart has already stretched too far from the base
- the catalyst is only a sympathy move rather than a direct-beneficiary story

## Allowed Conclusions

A good shortlist does not always mean there must be a fresh buy.
Valid conclusions include:
- BUY ON TRIGGER
- WATCH ONLY
- HOLD / NO ADD
- AVOID / TOO EXTENDED
- 0 FOCUS BUY NOW

## Reporting Language

Prefer language like:
- "Today's top gainers are distorted by illiquid UPCOM names, so they should not be used as evidence of broad risk appetite."
- "This name has the right story, but it fails secondary validation because sector support is missing and the move is already extended."
- "The candidate list has many names, but an empty action list is the more correct conclusion given current breadth and foreign flow."
