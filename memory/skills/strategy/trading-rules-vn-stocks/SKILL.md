---
name: trading-rules-vn-stocks
description: "Ryan's 12 trading rules for VN stocks. 8 core rules plus Rule 9 (Catalyst Day Execution), Rule 10 (T+2 Timing Advantage), Rule 11 (SL Trailing Wick Framework), and Rule 12 (SL Hunt Filter - do not cut too early while foreign investors are still buying, based on MBB 2026-05-05). Includes a mandatory 7-of-7 pre-trade checklist."
category: stock-strategy
published: true
---

## APPLY THIS SKILL BEFORE RECOMMENDING ANY ORDER

### STEP 1: CHECK THE FULL 7-OF-7 CHECKLIST
```
□ 1. Liquidity >= 3M shares per day? (Rule 4)
□ 2. Clear catalyst within 4-8 weeks? (Rule 4)
□ 3. Foreign-investor flow is neutral or net buying for 3 sessions? (Rule 4)
□ 4. Current macro backdrop is stable and not inside a 48h freeze? (Rule 3)
□ 5. The new position does not exceed 25% of NAV? (Rule 2)
□ 6. Stop loss is set at <= -5% for a catalyst swing trade? (Rule 5)
□ 7. No new position is being opened within 7 days of a major event if macro conditions are unstable? (Rule 3 + 5)
```
**If even 1 of 7 is missing, DO NOT RECOMMEND BUYING OR ADDING.**

### STEP 2: CORE RULES

1. **Sunk Cost Deadline Rule**  
   If the position is down more than 20% and there has been no catalyst for 3 months, set a hard exit date. Maximum two extensions.  
   *Example: SSI down 26% -> deadline after FTSE on April 8.*

2. **Position Cap: 25% of NAV**  
   No single name above 25% of total assets. Trim when gains push it above the cap.  
   *Example: HPG at 27% -> sell 4k-5k shares around 28.5k-29k.*

3. **Macro Freeze Protocol (48h)**  
   If a shock event hits, such as tariffs or a Fed surprise, freeze new buying for 48 hours and only manage stops.  
   *Example: Trump shock on April 2 -> no KDH Wave 2 buy.*

4. **Liquidity and Conviction Filter (3-of-3)**  
   Volume >= 3M shares per day, catalyst within 4-8 weeks, and foreign-investor flow neutral or buying.

5. **Minimum Stop Width: -5%**  
   For catalyst swing trades, stop loss must be at least 5% below entry.

6. **ETF Rebalancing Hold-to-Deadline**  
   Hold until the final ETF buying day. Read the flow in three phases: warm-up, short pause, and settlement or ATC deadline. If foreign buying fades for 1-2 sessions mid-cycle, check deadline mechanics before exiting.

7. **Do Not Chase Entry**  
   If you missed it, acknowledge that. Do not invent a weak "wait for pullback" thesis without evidence.

8. **Disciplined Stop Loss**  
   If price hits the stop, execute the exit in that same session.

### STEP 2B: ADDITIONAL RULES FOR CATALYST DAY AND T+2

9. **Catalyst Day Execution: No Hopeful LO on Hot Names**

   **Recognition:** a major catalyst has been confirmed, such as FTSE upgrade, earnings surprise, or a major macro event, and the trade enters execution mode.

   **Three-phase protocol:**
   - **Phase 1 (9:00-10:30):** watch ATO, gather tick data and foreign flow, and identify the best name. Do not rush into blind ATO without data.
   - **Phase 2 (around 10:30-11:00):** tick data confirms conviction, for example aggressive foreign buying with zero meaningful selling.
   - **Phase 3:** act immediately in the next message. The delay between "knowing" and "doing" should be zero.

   **Forbidden on catalyst day:**
   - placing pullback LO orders on a hot winner
   - gradually raising LO and effectively chasing with limit orders
   - asking more questions after the data already confirmed the trade
   - scanning more names instead of executing the chosen winner
   - using LO as a middle-ground compromise

   **Execution clarification:**
   - If the name is already in catalyst-driven markup or breakout and the thesis is strong, prefer ATO, MP, or ATC according to plan rather than a hopeful LO.
   - If the name is still in accumulation or base and has not exploded intraday, LO or pullback buying remains valid.
   - The "no LO" rule applies specifically to catalyst day plus hot stock plus confirmed breakout. It is not a universal ban on LO orders.

   **Binary decision:** sufficient conviction means execute aggressively; insufficient conviction means do not enter. No middle ground.

   *Practical lesson:* On FTSE Day, April 8, tick data confirmed TCB as the top winner around 11:00 with foreign net buying of 2.33M shares and zero meaningful selling. The recommendation only came at 14:10, when TCB was already limit-up. Four LO attempts, zero fills, and about 5.9M VND of missed opportunity.

10. **T+2 Timing Advantage**

   Before comparing ATC today versus ATO tomorrow, always calculate the T+2 unlock date:
   - ATC today -> T+2 = D+2, which is earlier
   - ATO tomorrow -> T+2 = D+3, or D+5 if a weekend intervenes

   **Important nuance:** shares settle near the end of T+2, but they can usually be sold from the afternoon session of T+2 after 13:00. There is no need to wait for the morning of T+3.

   **When T+2 matters most:**
   - a pullback or event risk is likely to hit during T+1 or T+2
   - a short 2-3 day swing trade where lock-up can trap an otherwise good trade
   - entry very close to FTSE, AGM, earnings, or a macro shock window

   **Mandatory sentence near event-driven BUY calls:**
   - "If bought today, the earliest possible sell time is the afternoon of T+2 after 13:00."

   *Example:* ATC on April 8 unlocks on the afternoon of April 10. ATO on April 9 stays locked until April 13. That is a three-day flexibility difference.

### STEP 2C: FRAMEWORK FOR INTRADAY WICKS VERSUS CLOSE BREAKS

11. **Trailing Stop Hit by Intraday Wick -> Evaluate Reward/Risk Before Acting**

   **Situation:** price wicks into or below the trailing stop intraday but has not closed below it.

   Do **not** auto-sell immediately. Evaluate three factors:
   1. **Reward/Risk**
      - If selling now, how much profit is locked?
      - How much upside is missed if price recovers?
      - If waiting for the close, how much extra downside is at risk?
      - How much upside can still be captured if it recovers?
   2. **Live expectation at that moment**
      - RSI/Stoch at extreme overbought can imply higher odds of further decline
      - heavy foreign selling adds pressure
      - order flow may show real support from larger buyers
      - the catalyst may still be intact or may already be fully reflected
   3. **Decision**
      - poor reward/risk plus bearish context -> partial sell immediately
      - good reward/risk plus bullish context -> wait for close confirmation
      - unclear case -> sell 50% and keep optionality

   This is **not** a rigid rule. It is a live evaluation framework.

### STEP 2D: SL HUNT FILTER

12. **SL Hunt Filter: Wait for Volume Confirmation Before Cutting**

   **Backdrop:** market makers or smart money know retail stop zones, force price through them, absorb supply, then push price back up. This pattern is especially relevant when foreign investors keep buying throughout the drop.

   **Signs of a stop-loss hunt:**
   - price breaks the stop trigger but rebounds quickly in the same session
   - foreign investors keep net buying near the low
   - morning sell volume is large, then dries up
   - buy absorption appears after the sell sweep

   **All three conditions must be present to apply the filter:**
   - foreign investors are net buying strongly intraday, for example more than 300k shares
   - the fundamental thesis or catalyst remains intact
   - the broad market is not in a hard breakdown, for example VN-Index not down more than 1.5%

   **Process after the stop trigger breaks:**
   1. Do not cut immediately. Observe for 15-30 minutes.
   2. Check tick data for buy absorption and continued foreign buying.
   3. Exit if price keeps falling at least another 50 VND beyond the trigger without recovery, if sell volume does not dry up after 30 minutes, or if foreign flow flips to net selling.
   4. Hold if absorption appears and foreign buying continues, because it is likely a stop-loss hunt.

   **Do not apply this filter when:**
   - foreign investors are also net selling
   - new bad fundamental news appears the same day
   - VN-Index is down more than 1.5%, indicating systemic stress

### STEP 2E: IDENTIFY THE MONEY-FLOW PHASE BEFORE RECOMMENDING ENTRY

Before answering "is it time to enter yet?", classify the stock into one of four phases:
- **Accumulation:** sideways for 2-3 sessions, volume gradually increasing, supply absorbed at lower levels, foreign investors buying quietly
  Action: pre-positioning or split orders is acceptable, preferably via LO near support.
- **Markup:** large buy orders push price quickly and price rises sharply in a short time
  Action: do not chase if the move is already too strong intraday; only enter if catalyst-day binary execution is already confirmed.
- **Distribution:** price is near highs or resistance, sell blocks appear, and price stops extending
  Action: take partial profit or avoid fresh buys.
- **Markdown / true breakdown:** price loses the base, absorption disappears, sell volume persists, and foreign flow does not support
  Action: prioritize defense and do not catch a falling knife.

**Supporting rules:**
- If price is already up more than 2% intraday without a clear catalyst-execution thesis, do not buy at market.
- Breakout buys are only trustworthy when price closes above resistance and volume is at least 150% of the 20-session average.
- Proactive beats reactive: entering during good accumulation is far better than chasing after markup.

### STEP 3: ISSUE THE ORDER AND RECORD THE PLAN
- Always write a concrete plan: stop, target, deadline, and scenario A/B/C.
- Rules reference: [trading-rules-lessons-learned-2026-04-06.md](strawberry://file/memory/equity-research-analyst-085e05f6/trading-rules-lessons-learned-2026-04-06.md)
- Master plan: [master-trading-plan-updated-2026-04-06.md](strawberry://file/memory/equity-research-analyst-085e05f6/master-trading-plan-updated-2026-04-06.md)

**Original chat:** strawberry://chat/310a73fa-cd1c-4ce7-8f98-37bab70f454e
