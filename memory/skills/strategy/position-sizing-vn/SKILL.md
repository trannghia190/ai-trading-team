---
name: position-sizing-vn
description: "Calculate optimal position size for the VN market: risk per trade, simple Kelly logic, and NAV limit checks. Use before any buy recommendation."
---

# Position Sizing for the VN Market

## When to use
- Before proposing a BUY, calculate exact shares and percent of NAV
- Check whether the recommendation violates allocation rules in the trading plan

## Pre-checks from the trading plan
- Max single position: 25% NAV
- Max sector concentration: 40% NAV
- Minimum cash: 10% NAV
- Drawdown rule: if NAV is down 15%, cut all positions by 50% and stop initiating new buys

## Calculation process

### Step 1: Define risk per trade
- Default: 1-1.5% of NAV
- Clear setup with confirmed breakout and supportive macro: 2% of NAV
- Blurry or unconfirmed setup: 0.5-1% of NAV

### Step 2: Calculate position size from the stop loss
```
SL distance % = (Entry − SL) / Entry
Position size (cash) = Risk / SL distance %
Position size (% NAV) = Position size / NAV
```
Example:
- NAV = 1 billion VND, Risk = 1.5% = 15 million VND
- Entry = 28,500 | SL = 26,600 → SL distance = 6.67%
- Position = 15 million / 6.67% = 225 million VND = 22.5% NAV ✅

### Step 3: Check sector concentration
- Existing sector exposure plus the new position must stay at or below 40% of NAV

### Step 4: Check the cash buffer
- Remaining cash after the buy = NAV minus total portfolio value minus new position, and it must stay at or above 10% of NAV

## VN-specific notes
- T+2.5 settlement means you cannot sell immediately after buying, so include that in the liquidity buffer
- There is no automatic stop-loss execution, so the stop must be managed manually
- With HOSE's daily +/-7% band, do not place the stop too close to entry or it can get swept in a single session

## Sample output
• NAV: 1,000,000,000 VND
• Entry: 28,500 | SL: 26,600 | SL distance: 6.7%
• Risk 1.5% NAV = 15,000,000 VND -> 7,500 shares ≈ 214 million VND ≈ 21.4% NAV ✅
• Post-buy cash: check the portfolio -> X% >= 10%? [confirm]
• Recommendation: Buy 7,500 shares (~21% NAV)
