# Local Source-of-Truth Layout for VN Portfolio + Trading Plans

## Purpose

Use this reference when syncing portfolio or trading-plan data from Analysis or from user-confirmed updates into Trading Team.

Goals:
- Analysis acts only as a sync source when the user requests it
- Trading Team must persist state into independent local files
- Recurring reports and cron jobs must read those local files rather than depend on temporary session memory

## Minimum local files

### 1) Portfolio state
Suggested path:
- `/memory/portfolio/AGENTS.md`

Suggested fields:
- `as_of`
- `cash_pct`
- `cash_notes` (optional)
- `holdings[]`
  - `symbol`
  - `weight_pct`
  - `shares` (optional if available)
  - `cost_basis`
  - `stop_loss` (optional)
  - `status` (e.g. core / trading / watch / trimming)
  - `notes` (optional, brief)

### 2) Trading plan state
Suggested path:
- `/memory/trading_plan/AGENTS.md`
or
- `/memory/tickers/<TICKER>.md`

Suggested fields if JSON:
- `as_of`
- `market_regime_preference` (optional)
- `plans[]`
  - `symbol`
  - `thesis`
  - `catalyst`
  - `entry_plan`
  - `invalidations`
  - `target_plan`
  - `next_review_trigger`

## Mandatory rule after Analysis sync

A Analysis sync is only complete when all 3 happen:
1. data is read from Analysis
2. data is normalized into Trading Team-owned structure
3. normalized state is written to independent local files

If step 3 did not happen, the sync is incomplete.

## Why this matters

Without local source-of-truth files:
- cron reports become market-only by default
- portfolio linkage disappears
- agent falls back to stale session memory
- user has to repeat holdings/plans too often

## Report integration rule

Recurring market reports should read:
- local portfolio state for current holdings / cash / stops
- local trading-plan state for thesis / trigger / invalidation context

**PROACTIVE UPDATE RULE (CRITICAL):**
When asked for VN stock analysis or trade recommendations, ALWAYS read `/memory/portfolio/AGENTS.md` and `vn_stock_trading_plan.json` first. Advice MUST factor in current holdings, cash percentage, and active plans. 
If the user agrees to a new plan or confirms a trade execution, **proactively update these local JSON files** to reflect the new state immediately. Do not wait to be asked. Update the state directly via `write_file` or `execute_code`.

Do not rely on:
- old session text
- durable memory for current holdings
- raw Analysis notes as the daily runtime source

## Good maintenance behavior

After any confirmed change:
- update the local portfolio file if positions/cash/stops changed
- update the local trading-plan file if thesis/catalyst/triggers changed
- keep the files concise and normalized
- treat these files as the working system of record for future routines

## Common failure modes

- Syncing from Analysis but not writing independent local files
- Writing portfolio state but forgetting trading-plan state
- Saving current holdings into durable memory instead of local files
- Letting cron prompts embed stale holdings instead of reading local state
- Treating Analysis as the daily operational source instead of explicit sync source

## Recommended next wiring step

When a market-monitor cron should become portfolio-aware:
- read `vn_stock_portfolio.json`
- read `vn_stock_trading_plan.json` or per-symbol plan files
- if files are missing, explicitly degrade to market-only mode
- if files exist, connect market regime directly to held symbols and planned trades
