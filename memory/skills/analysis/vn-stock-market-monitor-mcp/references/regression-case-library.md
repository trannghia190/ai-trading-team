# Regression Case Library

## Purpose

This reference is used to quickly test the market-monitor, routine, watchlist, and synthesis skill stack after each patch.

Goals:
- prevent skills from appearing better while actually drifting away from the logic
- test the shortlist filter, regime read, emotion overlay, and action vocabulary
- maintain a reusable set of case archetypes

## How to use

After each important patch, choose 3-5 cases from this library and check:
1. Does the regime verdict match the spirit of the case?
2. Is the emotion verdict too bullish or too bearish?
3. Is the shortlist being pulled around by illiquid noise?
4. Are the action labels consistent?
5. Are there any false-positive buys?

The wording does not need to match 100%.
The decision quality does.

## Case 1 — Broad risk-on with healthy breadth

### Pattern
- A/D is strong at > 1.5
- foreign flow is not strongly opposing
- many sectors are expanding together
- top leaders have high trading value and are not penny noise

### Expected outputs
- Regime: Broad risk-on
- Emotion: warming, sometimes crowded if the run has lasted many sessions
- Shortlist: there can be 2-3 focus names
- Action bias: more `BUY ON TRIGGER` than `WATCH ONLY`

### Failure signs
- the skill stays too defensive and outputs `0 focus buy now`
- it treats every leader as `BUY NOW` even when already extended

## Case 2 — Narrow index-led rally / green index with weak internals

### Pattern
- the index is green, but breadth is weak or negative
- a few large caps are pulling the index
- many small and mid-cap names are red
- leadership is narrow

### Expected outputs
- Regime: Narrow index-led rally
- Emotion: stable or crowded; do not call it broad warming
- Shortlist: few actionable names
- Action bias: `WATCH ONLY`, `HOLD / NO ADD`, or `0 focus buy now`

### Failure signs
- the skill calls broad risk-on just because VN-Index is green
- the shortlist still stuffs in too many buy candidates

## Case 3 — Mixed rotational session

### Pattern
- breadth sits around neutral
- some sectors are strong while others are clearly weak
- foreign flow does not justify an extreme verdict
- the index does not tell the whole story

### Expected outputs
- Regime: Mixed rotational session
- Emotion: stable or mildly warming
- Shortlist: selective, with 0-2 names truly worth tracking
- Action bias: `WATCH ONLY` or `BUY ON TRIGGER` with a clear trigger

### Failure signs
- the report turns into a generic dashboard without a verdict
- or the skill concludes risk-on too easily

## Case 4 — Risk-off / distribution day

### Pattern
- A/D is clearly weak
- foreign selling is heavy
- many sectors weaken together
- leaders break down or fail to follow through

### Expected outputs
- Regime: Risk-off / distribution day
- Emotion: cold
- Shortlist: very few or no fresh buy candidates
- Action bias: `HOLD / NO ADD`, `NO TRADE`, `0 focus buy now`

### Failure signs
- the skill still tries to force 2-3 new buy ideas to fill the report
- the foreign-flow verdict is underweighted

## Case 5 — Speculative froth without breadth support

### Pattern
- top gainers and volume surge lists are full of small caps, UPCOM names, and penny stocks
- breadth is not truly healthy
- large caps do not confirm
- the tape is very hot but low quality

### Expected outputs
- Regime: Speculative froth without breadth support
- Emotion: crowded or euphoric
- Shortlist: remove most illiquid names
- Action bias: `AVOID / TOO EXTENDED`, `NO TRADE`

### Failure signs
- the skill turns top gainers into the main watchlist
- it treats raw volume surge as a positive signal

## Case 6 — Good stock, bad entry

### Pattern
- the company and catalyst are fine
- the medium-term chart is fine or the thesis is still alive
- but price is already far from the base, crowded, or the intraday tape is ugly

### Expected outputs
- Single-name or shortlist verdict: `HOLD / NO ADD` if already owned, or `AVOID / TOO EXTENDED` / `WATCH ONLY` if considering a fresh buy

### Failure signs
- the skill uses `BUY` just because the story is good
- it fails to distinguish between something worth holding and something worth newly buying

## Case 7 — Sector leader but flow conflict

### Pattern
- the sector is the strongest group of the day
- the leading name in the sector has good liquidity
- but foreign flow, money flow, or technical follow-through is still not clean

### Expected outputs
- Action bias: `WATCH ONLY` or at most `BUY ON TRIGGER`
- It must not jump to `BUY NOW` too easily

### Failure signs
- turning automatically bullish just because the sector is leading
- ignoring negative CMF, foreign selling, or weak close structure

## Case 8 — Illiquid false positive

### Pattern
- the stock is limit-up or near limit-up
- trading value is below the floor
- the order book is thin
- the spread is poor or the move is only a one-bar spike

### Expected outputs
- Verdict: `NO TRADE`, `REMOVE / LOW EDGE`, or `AVOID / TOO EXTENDED`
- It must not enter the main action shortlist

### Failure signs
- the skill puts it on the focus list because of a sharp percentage gain or unusual volume surge

## Case 9 — Broad risk-on but already crowded

### Pattern
- breadth is still healthy
- the market is still bullish
- but many leaders have run far and emotion is hot

### Expected outputs
- Regime: Broad risk-on
- Emotion: crowded or euphoric
- Action bias: downgrade from `BUY NOW` toward `BUY ON TRIGGER` or `WATCH ONLY`
- No-chase warnings should increase

### Failure signs
- the skill still recommends widespread chasing

## Case 10 — Thesis intact, market ugly

### Pattern
- the single stock thesis is not broken
- but the market day is ugly, breadth is BEAR, and foreign selling is strong
- intraday tape makes a fresh entry very unattractive

### Expected outputs
- If already held: `HOLD / NO ADD`
- If not yet held: usually `WATCH ONLY` or `NO TRADE`

### Failure signs
- the skill fails to downgrade the verdict for a fresh entry
- or it incorrectly flips to `SELL` even though the thesis is not broken

## Minimum regression pack

If time is limited, at minimum test these 4 cases after each patch:
- Case 2: Narrow index-led rally
- Case 4: Risk-off / distribution day
- Case 5: Speculative froth
- Case 8: Illiquid false positive

## Suggested tagging when storing future examples

When real examples appear later, note them in this format:
- date:
- market regime:
- emotion:
- representative tickers:
- expected verdict:
- what the old skill got wrong:
- what the patched skill should now do:
