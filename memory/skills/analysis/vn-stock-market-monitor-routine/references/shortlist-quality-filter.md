# Shortlist Quality Filter

Use this reference when a routine report must decide whether a candidate deserves to move from market color into the action list.

## Default liquidity floors
- HOSE/HNX: `day_value_ty >= 50`
- UPCOM: `day_value_ty >= 100`

If the stock is below the threshold:
- do not include it in the actionable shortlist by default
- keep it only as market color or watchlist noise

## Additional gates
Even if the liquidity floor is passed, the candidate must still pass these gates:
1. Technical state is clean enough
2. It has breadth or sector support
3. Foreign flow or money flow is not strongly against it
4. The move is not too extended or crowded

## Allowed actions by quality
- 4/4 checks pass -> `BUY ON TRIGGER`
- 3/4 -> `WATCH ONLY` or `HOLD / NO ADD`
- <=2/4 -> remove it from the action list

## Practical use
- The candidate list can be long.
- The action list should stay short.
- If no good names remain after the filter, the correct conclusion is `0 focus buy now`.

## Important reminder
Do not use raw `top_gainers`, `top_losers`, or `volume_surge` output to infer market risk appetite if most names are illiquid UPCOM or penny stocks.
