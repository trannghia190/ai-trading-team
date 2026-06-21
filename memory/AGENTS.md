# Trading Team — Global Reference

This file is NOT auto-injected. Agents read it on demand: `read_file /memory/AGENTS.md`

## Memory File Map
- `/memory/portfolio/AGENTS.md`    — current positions (auto-injected, always fresh)
- `/memory/trading_plan/AGENTS.md` — strategy doc (auto-injected, always fresh)
- `/memory/macro/AGENTS.md`        — macro pattern library (auto-injected for MacroAnalyst)
- `/memory/technical/AGENTS.md`    — VN chart pattern library (auto-injected for TechnicalAnalyst)
- `/memory/leader/AGENTS.md`       — user prefs + session tips (auto-injected for Leader)
- `/memory/tickers/<TICKER>.md`    — per-ticker accumulated knowledge
- `/memory/sessions/<DATE>_<slug>.md` — past session reviews

## Report Files
When the user asks to "create a report" / "save a file", the workflow saves a markdown file to:
  `reports/<YYYY-MM-DD>_<slug>.md`
Leader can use `save_report` tool explicitly; LeadStrategy notes this at the end of synthesis.

## Accumulated Session Lessons
*(Browse: `ls /memory/sessions/` then `read_file /memory/sessions/<file>`)*
