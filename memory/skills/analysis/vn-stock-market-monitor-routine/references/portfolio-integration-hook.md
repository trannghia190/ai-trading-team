# Portfolio Integration Hook

When generating routine market monitor reports (open, mid, close, weekly):

**MANDATORY:**
You must read the user's live portfolio and trading plan state from the local source of truth before writing the report.
- Portfolio: `/memory/portfolio/AGENTS.md`
- Plans: `/memory/trading_plan/AGENTS.md`

**Integration:**
1. Parse the holdings and cash percentages.
2. Cross-reference the current market regime and breadth against the user's specific holdings.
3. If the user holds `SSI` and securities are the only green sector, note that explicitly. If the user is 50% cash and the regime is "risk-off", advise them to maintain the cash buffer.
4. If a holding threatens its stop loss, explicitly warn the user.
5. If the user has an active plan (e.g., "Buy STB on pullback to 70"), check if today's price action triggers that plan.

**If Files Are Missing:**
If the JSON files cannot be read or are empty, explicitly state at the beginning of the portfolio section: "No local portfolio state found. Defaulting to market-only report."