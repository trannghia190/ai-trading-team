---
name: vn-stock-portfolio-sync
description: Use when a VN stock portfolio changes and you need to update the current source of truth, separate durable lessons from ephemeral position state, and keep future routines aligned without hardcoding stale holdings.
version: 1.0.0
author: Trading Team
license: MIT
metadata:
  trading_team:
    tags: [stocks, vietnam, portfolio, state-management, workflow, memory]
    related_skills: [vn-stock-market-monitor-routine, trading-rules-vn-stocks, strawberry-stock-memory-harvest]
---

# VN Stock Portfolio Sync

## Overview

This skill rewrites the useful parts of Analysis's portfolio-update and dual-memory ideas into a Trading Team-native workflow.

This is the state-sync / source-of-truth maintenance layer, not a rebalance-decision skill replacing `vn-stock-portfolio-rebalance-mcp`.
- Use `vn-stock-portfolio-rebalance-mcp` when you need to decide add/trim/exit/replace actions.
- Use this skill when a portfolio change has already been confirmed and you need to update the correct current state for future routines/analysis.

Goal: whenever the user confirms a portfolio change, update the right artifacts in the right place:
- current portfolio state -> current source of truth file(s)
- current plan/watchlist -> plan file(s)
- durable lesson or preference -> Trading Team memory or a skill patch
- ephemeral trade event -> log/reference only, not durable memory

## When to Use

Use when:
- The user confirms a buy, sell, trim, add, stop-loss exit, or trailing SL change.
- The watchlist or entry zone changes materially.
- The portfolio risk posture changes enough to affect future reports.

Do not use for:
- Pure market commentary with no portfolio change.
- Saving every trade event into durable memory.
- Copying daily cash/P&L/open orders into long-term memory.

## Core Separation Rule

Always separate information into 3 buckets:
1. Current state
2. Durable lesson or preference
3. Ephemeral event log

## Source-of-Truth Mode Selection

When the user works with both Analysis and Trading Team, explicitly determine which system owns the live portfolio state.

Default preference in this environment:
- Trading Team should maintain the live VN-stock portfolio state locally.
- Analysis is a sync/import source, not the default live source-of-truth.
- Do not auto-overwrite Trading Team portfolio state from Analysis unless the user explicitly asks to sync from Analysis.

Operational rule:
- Keep live holdings / cash / avg cost / stop-loss / active plan in Trading Team-managed source-of-truth files.
- Keep trading plans in independent local files as well; do not leave them only inside Analysis-derived notes.
- Cron jobs and recurring market-monitor routines should read the Trading Team-managed files, not Analysis, unless the user intentionally switches the source.
- When the user says things like "sync from Analysis" or otherwise explicitly requests a refresh, then pull from Analysis, normalize the data, and overwrite/update the Trading Team source-of-truth files.
- If Analysis is used for a one-time bootstrap import, treat that as initialization only; after import, Trading Team remains the live state until the user requests another sync.

Mandatory persistence rule after Analysis sync:
- An Analysis sync is not complete until Trading Team writes the synced portfolio into an independent local state file.
- The same rule applies to active trading plans: persist them into Trading Team-managed local files, separate from raw Analysis artifacts.
- After sync, Trading Team should maintain these local files as the working system of record for future reports and routines.
- Do not treat Analysis as something that must be consulted every time just to remember current holdings or plans.

Common failure to avoid:
- Do not keep asking the user to re-enter portfolio state when a trusted source already exists.
- Do not let a background sync silently replace the live portfolio state with Analysis data unless the user opted into that behavior.
- Do not stop at "sync/read from Analysis" without persisting normalized local files for portfolio state and trading plans.

1. Current state
   - holdings
   - average cost
   - current SL
   - cash
   - current watchlist / entry zones
   -> update source-of-truth files

2. Durable lesson or preference
   - e.g. the user does not want fast-twitch trading
   - e.g. use technicals mainly for SL/trailing, not frequent churn
   - e.g. a new rule discovered from repeated experience
   -> save to Trading Team memory or patch a skill

3. Ephemeral event log
   - sold 3,000 shares today
   - ATC fill happened
   - P/L on a given date
   -> keep in notes/log/reference if needed, not durable memory

## Recommended Workflow

### Step 1: Confirm the actual change
Before updating anything, ensure you know:
- symbol
- action type: buy / sell / trim / add / cut-loss / trail-SL / watchlist change
- quantity
- execution or intended price
- whether the plan/catalyst changed or only the position size changed

### Step 2: Update current source of truth
Update the file(s) the user currently uses for live portfolio state.
Typical fields:
- holdings table
- cash
- average cost
- stop loss
- realized/unrealized notes if the user tracks them
- watchlist and entry zones

If there is both a portfolio state file and a plan file:
- portfolio file = positions and risk levels
- plan file = thesis, targets, catalysts, triggers

### Step 3: Decide whether future routines need adjustment
If the change affects:
- held symbols
- stop losses
- watchlist targets
- cash available for deployment
then future market-monitor routines must read the updated state.

Do not hardcode those values into the skill itself.

### Step 3B: Mandatory final step — propagate state changes to recurring routines
Treat routine sync as a required closing step, not an optional cleanup.

If any portfolio / plan / watchlist / cash change happened, you must ensure the recurring market-monitor workflow is immediately aligned before finishing the task.

Practical rule:
- if the routines read a live source-of-truth file at runtime, update that source of truth before finishing
- if any routine, prompt, automation, or cached artifact embeds portfolio/watchlist/cash details directly, refresh both the open-session routine and the mid/close-session routine immediately
- do not assume the next run will "figure it out" from stale embedded text

This rule is about workflow reliability, not about saving transient state into durable memory.

### Step 4: Distill durable knowledge
Ask whether the event created a reusable lesson:
- new stop-loss handling rule?
- new catalyst execution lesson?
- new preference about speed, sizing, or no-chase discipline?

If yes:
- patch an existing stock skill, or
- save a concise durable memory fact

### Step 5: Log the event at the right granularity
Keep a short structured note if needed:
- date
- action
- symbol
- quantity
- price
- 1-line reason

Avoid verbose daily journals in durable memory.

## What Belongs in Durable Memory

Good candidates:
- The user prefers conviction-driven swing trades over frequent short-term flips.
- The user uses technical analysis mainly for trailing SL and risk control.
- The user expects pre-trade checklist enforcement before recommendations.
- The user prefers MCP/tool data first, web search second when available.

Bad candidates:
- Current holdings list
- Cash today
- Unrealized P/L today
- Pending LO/ATC order
- A dated entry zone likely to change next week

## When to Patch a Skill Instead of Saving Memory

Patch a skill when the new knowledge is procedural or generalizable, e.g.:
- a better stop-loss exception rule
- a new breadth-divergence interpretation
- a refined catalyst-day execution heuristic
- a repeatable routine section that was missing before

Save memory when the new knowledge is a stable preference or standing convention.

## Common Pitfalls

1. Saving current holdings into durable memory.
2. Mixing thesis with current state in one place so both go stale together.
3. Treating every trade as a lesson.
4. Updating logs but forgetting the live source-of-truth file.
5. Hardcoding new state into routine prompts instead of updating the underlying state file.

## Verification Checklist

- [ ] Confirmed symbol, action, qty, and price before updating
- [ ] Updated the current source-of-truth file(s)
- [ ] Updated plan/watchlist only if thesis or triggers changed
- [ ] Did not save holdings/cash/P&L/open orders into durable memory
- [ ] Saved memory only if it was a durable preference or convention
- [ ] Patched a skill if the event produced a reusable rule
