"""
Self-Improvement Module — LangChain Trading Team
-------------------------------------------------
Periodically:
  1. Collects recent logs + session history
  2. Analyses for bugs / improvement opportunities
  3. If actionable → creates a feature branch with a fix
  4. Sends a Telegram review request with diff summary

Only one pending fix is allowed at a time (guarded by pending.json state).
Long-term knowledge is stored in memory/self_improvement/ with a file index
so agents can fetch only what they need rather than loading everything.
"""
