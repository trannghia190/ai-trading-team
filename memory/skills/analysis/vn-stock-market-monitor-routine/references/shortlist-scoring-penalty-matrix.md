# Shortlist Scoring + Penalty Matrix

Use this reference when a routine report must turn a candidate list into a consistent action board.

## Core rule
Passing the liquidity filter is only an entry gate.
It is not a positive score strong enough by itself to make something a buy candidate.

## Base score (0-5)
- Technical state
- Breadth / sector support
- Flow confirmation
- Buyability / extension
- Catalyst quality

For each category:
- +1 if confirmation is good
- 0 if it is mixed or fails

## Penalties
- -1 for poor intraday foreign pressure in a weak backdrop
- -1 strongest among weak setups
- -1 one-bar spike / low-quality tape
- -1 for poor execution quality or for barely passing the liquidity floor

## Verdict map
- Net >= 4 -> can be `BUY ON TRIGGER`
- Net = 3 -> `WATCH ONLY` or `HOLD / NO ADD`
- Net = 2 -> `HOLD / NO ADD` if already owned; otherwise `NO TRADE`
- Net <= 1 -> remove from shortlist

## Hard overrides
- Liquidity fail -> remove immediately
- Thesis intact but too extended -> `AVOID / TOO EXTENDED`
- Breadth BEAR + strong foreign selling + intraday foreign pressure -> downgrade fresh-entry verdict by at least one notch

## Reporting note
When using this matrix in a report, there is no need to show detailed scores unless the user asks.
But the reasoning in each action line must reflect the score and penalty logic.
