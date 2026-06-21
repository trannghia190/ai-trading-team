# Shortlist Scoring + Penalty Matrix

## Purpose

This reference turns shortlist filtering from discretionary judgment into repeatable logic.

It does not replace the market-regime read.
It is the final decision layer for deciding which candidates can move from market color into action.

## Step 1: Liquidity gate

### Default floors
- HOSE/HNX: `day_value_ty >= 50`
- UPCOM: `day_value_ty >= 100`

If the candidate fails this gate:
- it must not be upgraded into an actionable buy
- it can still be mentioned in market color if the narrative is notable
- the verdict is usually `NO TRADE` or `REMOVE / LOW EDGE`

## Step 2: Base score (0-5)

### 1. Technical state
+1 if:
- it is above MA20/MA50 or reclaiming them cleanly
- SuperTrend is not clearly down
- stop or invalidation logic is clear

0 if:
- the structure is mixed or not confirmed yet

### 2. Breadth / sector support
+1 if:
- the market backdrop is not fighting the name
- the sector is in ignition/expansion, or at least not fading

0 if:
- the name is a lone strong stock inside a weak backdrop

### 3. Flow confirmation
+1 if:
- foreign flow or money flow confirms the trade
- or at least does not clearly oppose it

0 if:
- flow looks distributive, passive support is weak, or there is major conflict

### 4. Buyability / extension
+1 if:
- the entry is still close to the base
- reward/risk is still sufficient
- the name is not yet crowded or euphoric

0 if:
- it is already somewhat extended or only suitable for watching

### 5. Catalyst quality
+1 if:
- the catalyst is direct
- the timing is close enough
- most of the move is not priced in yet

0 if:
- the catalyst is vague, generic, or already heavily priced in

## Step 3: Penalties

Subtract 1 point for each case:
- clearly poor intraday foreign pressure inside a weak market regime
- strongest among weak setups, meaning relatively strong-looking but not a truly clean leader
- one-bar spike, low-quality tape, or breakout without follow-through
- poor execution quality: empty spread, fake-thin order book, or trading value barely above the floor

## Step 4: Interpretation

- Net >= 4:
  - can qualify for `BUY ON TRIGGER`
  - upgrade to `BUY NOW` only if a single-stock deep dive gives extra confirmation and the market regime is not hostile

- Net = 3:
  - default to `WATCH ONLY`
  - if it was already owned from a good lower entry, it can be `HOLD / NO ADD`

- Net = 2:
  - if there is an existing lower-base position: `HOLD / NO ADD`
  - if it would be a fresh position: `NO TRADE`

- Net <= 1:
  - remove from action shortlist
  - usually `NO TRADE`

## Hard overrides

### Override A: Too extended but thesis still alive
Use:
- `AVOID / TOO EXTENDED`
Do not use:
- `NO TRADE`

### Override B: Liquidity fail
Remove immediately. Do not rescue it with narrative.

### Override C: Bear backdrop + strong foreign sell + intraday foreign pressure
Downgrade the fresh-entry verdict by at least one notch.
Example:
- from `BUY ON TRIGGER` to `WATCH ONLY`
- from `WATCH ONLY` to `NO TRADE`

## Good examples

- Strong blue-chip, healthy trend, but poor fresh entry -> `HOLD / NO ADD`
- Day leader in the sector, but flow still looks bad -> `WATCH ONLY`
- UPCOM spikes hard on low liquidity -> `NO TRADE`
- The name has a clear catalyst but is already far above the base -> `AVOID / TOO EXTENDED`

## Anti-patterns

- letting one session of foreign buying override everything
- adding names to the shortlist just because they show up in top volume or top gainers
- treating a liquidity pass as sufficient evidence to buy
- failing to distinguish a true leader from the strongest among weak setups
