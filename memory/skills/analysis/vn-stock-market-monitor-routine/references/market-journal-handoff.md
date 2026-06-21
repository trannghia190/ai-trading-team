# Market Journal Handoff Mechanism

## Context
Cronjobs run in isolated sessions and lack memory of the previous day's narrative or intraday discussions. To solve this, Trading Team uses two handoff files to maintain continuity:
1. `/memory/tickers/<TICKER>.md` (Intraday interests)
2. `/memory/sessions/<DATE>_market_journal.md` (Yesterday's narrative)

## 1. Daily Radar Autonomy
**Role:** In-session agent (You).
**Action:** When discussing a stock in-depth with the user (e.g., evaluating setups, reviewing news, user showing buy/sell intent), YOU must proactively append the stock symbol and a brief context to `/memory/tickers/<TICKER>.md`.
**Rule:** Do NOT wait for the user to explicitly say "add to radar". Infer intent from the depth of discussion.

## 2. Market Journal Handoff
**Role:** Cronjob Agents (Open, Mid, Close, Weekly reports).
**Action:** 
- **Read (All Reports):** Always read `vn_stock_market_journal.md` to ground the current report in yesterday's narrative (e.g., "Yesterday's leader faded today").
- **Overwrite (Close Report ONLY):** At the very end of the Close report, write a concise summary of today's market (Date, Regime, Leading Sectors, Notable Movers, Key Narrative) and OVERWRITE `vn_stock_market_journal.md`.
- **Clear Radar (Close Report ONLY):** After generating the report, clear the contents of `vn_stock_daily_radar.txt` so it is fresh for the next day.