# Standard Action Vocabulary

## Purpose

This reference standardizes action language across the full VN-stock skill stack so different skills do not produce different verdict styles.

## Canonical Actions

### BUY NOW
Use this when the edge is clear enough to open a position immediately.
Requirements:
- the chart and location are still buyable
- the catalyst is still active
- the flow is not strongly opposing the trade
- reward/risk is good enough

### BUY ON TRIGGER
Use this when the thesis is correct but one specific confirmation condition is still needed.
Example triggers:
- a valid breakout close
- a pullback that holds support
- confirming volume
- foreign investors stop selling or return to buying

### WATCH ONLY
Use this when the story makes sense but price, flow, or timing still lacks confirmation.
It is not a hidden buy call.

### HOLD
Use this when you already have a good position and the thesis remains intact.
It does not necessarily mean a fresh entry is still attractive.

### HOLD / NO ADD
Use this when the existing position is fine but a new entry is no longer attractive.
This verdict is very common for extended leader names.

### REDUCE / TAKE PROFIT
Use this when the position is still profitable or the thesis is not fully broken, but risk should be reduced or gains should be locked in.

### SELL / EXIT
Use this when the thesis has failed, the stop has failed, or deterioration is strong enough.

### AVOID / TOO EXTENDED
Use this when:
- the current entry is too far above the base
- the crowd is too hot
- reward/risk has become badly skewed
- the name may still be worth watching, but not worth initiating

### NO TRADE
Use this when there is not enough edge or when the data and structure are too contradictory.

### 0 FOCUS BUY NOW
Use only at the market-board, watchlist, or routine-report level.
Do not use it for a single stock.
Meaning:
- there may be candidates
- but none are strong enough to justify a fresh buy action

## Mapping Notes

### Single-stock skills
Prefer:
- BUY NOW
- BUY ON TRIGGER
- WATCH ONLY
- HOLD
- HOLD / NO ADD
- REDUCE / TAKE PROFIT
- SELL / EXIT
- AVOID / TOO EXTENDED
- NO TRADE

### Watchlist / market-monitor skills
Can also use:
- FOCUS BUY NOW
- FOCUS BUY ON TRIGGER
- 0 FOCUS BUY NOW

But they should still map clearly to the canonical actions to avoid ambiguity.

## Hard Rules

- Do not use vague verdicts such as "fairly okay", "leaning buy", or "worth considering".
- Do not label something WATCH ONLY while sneaking in a buy zone as an implicit recommendation.
- Do not use HOLD instead of HOLD / NO ADD when the fresh entry is already clearly poor.
- Do not use AVOID / TOO EXTENDED if the thesis has actually failed outright; in that case use SELL / EXIT or NO TRADE depending on context.
