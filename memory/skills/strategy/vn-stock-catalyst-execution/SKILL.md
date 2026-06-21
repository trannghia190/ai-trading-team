---
name: vn-stock-catalyst-execution
description: Use when a VN stock trade is driven by a clear catalyst or event window and you need to choose between pre-positioning, binary execution, pullback LO, or no-trade while accounting for T+2 lock-up, foreign flow, and event-day opportunity cost.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, catalyst, execution, ftse, t-plus-2, risk-management]
    related_skills: [trading-rules-vn-stocks, nn-flow-tracking, vn-stock-orderflow-interpretation]
---

# VN Stock Catalyst Execution

## Overview

Use this skill for trades or events with a clear catalyst, such as FTSE or MSCI changes, earnings, AGM, HRC or tariff policy, legal unlocks, ETF rebalancing, or macro milestones that can shift the short- to medium-term narrative.

The focus is not simply "which stock is good." The focus is:
- when to pre-position before the event
- when binary execution is justified
- when LO pullback buying is the right approach
- when the trade should be skipped entirely
- how to account for T+2 lock-up risk and the opportunity cost of hesitation

## When to Use

Use when:
- the catalyst is identifiable in both timing and transmission mechanism
- the user asks whether to enter before or after an event
- a stock gaps hard on catalyst news and an immediate same-session execution decision is needed
- the trade must choose between ATO, ATC, MP, LO, or no-trade

Do not use for:
- ordinary technical swing trades without a clear catalyst
- chasing a move that is already too far extended with limited upside left
- short 2-3 day trades where T+2 is being ignored

## Mandatory Analysis Order

Always keep this sequence:
1. Price and technical context
2. Event, news, and catalyst specifics
3. Foreign-flow or money-flow confirmation
4. Execution choice

A catalyst does not fully override chart and flow. It only raises probability if the other layers are not strongly opposing the trade.

## Catalyst Categories

### 1. Scheduled catalysts
Examples:
- FTSE or MSCI decision dates
- earnings, AGM, dividend, legal effective dates
- ETF rebalance windows

Strength:
- can be prepared for in advance
- easier to separate pre-positioning from execution phase

### 2. Policy or macro catalysts
Examples:
- HRC tariff changes
- legal resolutions for real estate
- Fed shocks, tariff shocks, oil shocks

Strength:
- impact can spread across an entire sector or theme

Risk:
- easy to overreact intraday
- may trigger freeze protocol if the shock is too large

### 3. Stock-specific surprise catalysts
Examples:
- strong earnings beat or miss
- insider or strategic action
- surprise legal approval

Risk:
- price may enter execution mode very quickly
- a clean pullback entry may never return

## Four Action Modes

### A. Pre-position
Use when:
- the catalyst is still several sessions or weeks away
- price remains in base or accumulation
- foreign flow is starting to improve, but the crowd is not yet in FOMO mode
- reward/risk is still favorable

Action:
- split into one or two small waves
- use LO around support
- maintain stop discipline from the start

### B. Binary execution
Use when:
- the catalyst has just confirmed or intraday evidence is already overwhelming
- the stock is clearly in execution mode or hot breakout mode
- further delay mostly worsens price or loses the position

Action:
- either execute decisively according to plan
- or skip the trade entirely
- do not use LO as a half-committed compromise

### C. Pullback-LO plan
Use when:
- the catalyst is good but price already gapped or marked up early
- a technically reasonable pullback is still possible
- the stock is not yet in full runaway mode

Action:
- define a clear pullback zone
- accept that the order may never fill
- do not keep raising the LO emotionally

### D. No-trade / freeze
Use when:
- the catalyst is unclear or already excessively priced in
- a fresh macro shock severely distorts expected outcomes
- T+2 lock-up creates risk not worth accepting
- foreign flow and price action are fighting the thesis

## Pre-Position Framework

Before the event, ask five questions:
1. Is the catalyst transmission mechanism clear?
2. Is the remaining event window long enough for pre-positioning?
3. Is price still near a reasonable base, or has it already moved too far ahead?
4. Is foreign flow starting to confirm?
5. If the event fails or the market turns ugly, where is the stop?

If four of the five answers are favorable, a small pre-position can be justified.

## Binary Execution Framework

Use only when all three conditions are true:
1. the catalyst is confirmed or intraday evidence is already strong enough
2. this stock is the clear winner relative to the alternatives
3. not acting quickly will likely mean missing the trade or paying much worse prices

Rule:
- enough conviction -> execute
- not enough conviction -> do not enter
- no middle ground

### Signs that the stock is in execution mode
- foreign buying becomes highly one-sided
- it is the hot winner among direct beneficiaries
- the tape shows supply being absorbed with little meaningful pullback
- the catalyst is large enough for retail, ETFs, and active funds to chase together

## When LO Is Right and When LO Is Wrong

### LO is right when
- the trade is a pre-position or pullback trade
- the stock is not yet in runaway catalyst mode
- there is a clear technical support zone with order-flow backing
- a non-fill outcome is acceptable

### LO is wrong when
- the catalyst day is exploding and the stock is the hot winner
- you want the trade badly but do not want to pay the market price
- you keep raising LO repeatedly because you fear missing it

Practical rule:
- "LO on the explosion day of a hot winner is hope, not strategy."
- If a hot winner pulls back deep enough to fill an ideal LO, ask whether that means the stock has a problem.

## T+2 Lock-Up Framework

In Vietnam, every short-term catalyst trade must account for T+2.

### Core rule
- if bought on day T, the earliest realistic sell time is the afternoon of T+2 after 13:00
- no need to wait for the morning of T+3, but the position is still locked for two trading days

### Three mandatory questions before entry
1. If the market turns ugly on T+1 or T+2, will the trade be trapped?
2. Does the expected pullback or event risk fall inside the locked window?
3. Does ATC today unlock earlier and better than ATO tomorrow?

### When T+2 matters most
- 2-3 day trades
- entry very close to a major event
- Thursday or Friday entries, or pre-holiday setups
- trades where the buy reason is mainly a short-lived catalyst

## Opportunity Cost Versus Risk Cost

Do not look only at the risk of buying. Also look at the risk of waiting.

### High risk of delay when
- the catalyst just confirmed
- the winner is obvious
- the tape shows no good pullback
- the market is repricing very quickly

### High risk of buying when
- price already gapped far from support without a new base
- large supply is still hanging above
- the catalyst has high sell-the-news probability
- T+2 lock-up leaves little upside while freezing downside exposure

## Sell-the-News and Post-Catalyst Handling

After the catalyst, think in three scenarios:
1. confirm plus follow-through -> hold, trail, or add on a controlled pullback
2. confirm but overextended -> take partial profit or avoid fresh buys
3. fail or underwhelm -> exit according to plan and do not cling to the narrative

If the event confirms and the gap is too strong:
- do not automatically chase
- choose clearly between very early binary execution or standing aside for a new base

## Event Classification Matrix

Before choosing execution, classify the catalyst correctly:
- earnings, AGM, dividend, issuance, ETF rebalance, or scheduled event windows
- policy, macro, commodity, or legal unlock catalysts that spill into the group
- order, product, contract, capacity, or corporate actions that are stock-specific
- regulatory, lawsuit, governance, or sanction risks that are negative or two-sided

For each group, answer:
- does the main impact hit revenue, margin, valuation multiple, legal certainty, or only sentiment?
- is the time horizon intraday, a few sessions, a few weeks, or a few months?
- is this catalyst specific to the stock, or shared by the sector or theme?

## Catalyst State: Unpriced or Crowded?

It is not enough to say the catalyst is good or bad. Classify the state:
- `UNPRICED / EARLY RECOGNITION`: the market is just starting to notice and price remains close to base
- `PARTIALLY PRICED`: some upside is already reflected, but more remains if follow-through is strong
- `CROWDED / EXPECTATION-RICH`: narrative is hot, price and turnover already ran quickly, and reward/risk is deteriorating
- `STALE / EXPIRED`: the catalyst window has passed and only narrative residue remains

Signs of crowded or priced-in conditions:
- price has already broken out for many consecutive sessions and is far from nearest support
- turnover, volume, and headline heat are surging while follow-through begins to weaken
- the main winner is already crowded while flow is no longer improving proportionally

## Impact-Path Checklist

Before recommending a catalyst trade, check:
- what is the catalyst and how does it transmit?
- does it mainly affect revenue, margin, multiple, legal certainty, financing ability, or just sentiment?
- is the horizon intraday, a few sessions, or a few months?
- is price at base, breakout, or overextended?
- is foreign flow confirming?
- when is the T+2 unlock date?
- what order type should be used?
- if wrong, what is the exit condition?
- does the thesis fail because the event was weaker than expected, the timeline was delayed, or the market had already over-priced it?

## Event-Day Checklist

Before recommending a same-day catalyst order, check:
- what is the catalyst and how does it transmit?
- what is the time horizon?
- is price at base, breakout, or overextended?
- is foreign flow confirming?
- when is T+2 unlock?
- what order type fits?
- what is the exit condition?
- is the catalyst currently unpriced, partially priced, crowded, or stale?
- is this the direct winner or only a sympathy move?

## Invalidation Conditions

Do not stop at "the catalyst is good." Always state what breaks the thesis:
- the event points in the right direction, but details are weaker than the narrative
- price cannot hold breakout or follow-through after the catalyst
- heavy distribution or foreign selling appears right after the news
- the catalyst timeline slips, legal approval is delayed, or policy wording is weaker than hoped
- the market regime deteriorates and the catalyst no longer receives the expected multiple

## Suggested Output Format

1. Specific catalyst and transmission mechanism
2. Whether this is pre-position, binary execution, pullback-LO, or no-trade
3. Entry zone or execution style
4. Stop, target, and thesis horizon
5. T+2 unlock timing
6. Conditions that break the thesis
7. Whether missing the trade is acceptable if the order does not fill

## Common Pitfalls

1. Using the same execution style for every catalyst.  
   An unconfirmed catalyst and a fully exploding catalyst are different problems.

2. Using LO as a psychological compromise.  
   Half wanting the trade and half fearing it often creates the worst decision.

3. Ignoring T+2.  
   Many short trades look great until the position gets locked during a reversal.

4. Treating a strong catalyst as permission to chase at any price.  
   A good catalyst does not erase reward/risk discipline.

5. Looking only at the catalyst and not at the best beneficiary.  
   A major event still creates A-tier, B-tier, and C-tier winners.

## Verification Checklist

- [ ] Catalyst type and time window identified
- [ ] Correct mode selected: pre-position / binary execution / pullback-LO / no-trade
- [ ] T+2 unlock timing calculated before the recommendation
- [ ] It is clear when LO is appropriate and when it is not
- [ ] Opportunity cost of hesitation has been considered
- [ ] Stop, target, and thesis-failure conditions are stated
