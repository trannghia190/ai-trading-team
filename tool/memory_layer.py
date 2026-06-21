"""
Trading Team — Local Filesystem Memory Layer
=============================================

3-tier memory architecture for ALL agents:

  Short-term   │ MemoryMiddleware (deepagents built-in)
               │   • Auto-loads bounded AGENTS.md files into system prompt before each invocation
               │   • SummarizationMiddleware compacts conversation history when context fills
               │   • Zero extra tool calls — just works
  ─────────────┼─────────────────────────────────────────────────────────────────────
  Long-term    │ LocalShellBackend-backed files under memory/ directory
               │
               │   Persistent state (auto-injected, always bounded):
               │     /memory/portfolio/AGENTS.md     — current positions & NAV
               │     /memory/trading_plan/AGENTS.md  — living strategy document
               │
               │   Domain knowledge (per agent type, auto-injected):
               │     /memory/macro/AGENTS.md         — MacroAnalyst: macro pattern library
               │     /memory/technical/AGENTS.md     — TechnicalAnalyst: VN chart patterns
               │     /memory/leader/AGENTS.md        — Leader: user prefs, session tips
               │
               │   Per-asset and session logs (on-demand read_file):
               │     /memory/tickers/<TICKER>.md     — accumulated per-ticker knowledge
               │     /memory/sessions/<DATE>_<slug>  — full session reviews
  ─────────────┼─────────────────────────────────────────────────────────────────────
  Skills       │ SkillsMiddleware (deepagents built-in) — progressive disclosure
               │   • Only name + description injected into system prompt (tiny overhead)
               │   • Agent loads full instructions on demand when the skill is needed
               │   • Agents and node_memory_save can CREATE new skills at runtime
               │
               │   /memory/skills/shared/    — available to ALL 5 agents
               │   /memory/skills/analysis/  — MacroAnalyst + TechnicalAnalyst only
               │   /memory/skills/strategy/  — Bull/Bear/Leader only
  ─────────────┼─────────────────────────────────────────────────────────────────────
  External     │ MCP memory server (read-only) — memory_search + memory_list only
  (MCP)        │   Agents read externally-ingested knowledge (research reports, news)
               │   All writes go to local files, not MCP

Memory auto-loaded per agent (ALWAYS bounded — never grows):
  MacroAnalyst    → portfolio + trading_plan + macro/AGENTS.md
                    skills: shared/ + analysis/
  TechnicalAnalyst→ portfolio + trading_plan + technical/AGENTS.md
                    skills: shared/ + analysis/
  BullAnalyst     → portfolio + trading_plan
                    skills: shared/ + strategy/
  BearAnalyst     → portfolio + trading_plan
                    skills: shared/ + strategy/
  Leader          → portfolio + trading_plan + leader/AGENTS.md
                    skills: shared/ + analysis/ + strategy/

Skills design:
  - Only name+description shown at startup (1 line each — negligible overhead)
  - Full SKILL.md loaded on demand by agent via built-in skill tool
  - Agents and node_memory_save can CREATE skills: write_file /memory/skills/<category>/<name>/SKILL.md
  - New skills auto-discovered next session by SkillsMiddleware

Design invariants:
  - Global AGENTS.md is NOT in memory sources — it is a rules doc agents can
    read on demand with read_file. It never grows (no lessons appended).
  - Session lessons go ONLY to sessions/<date>_<slug>.md — never to AGENTS.md.
  - domain AGENTS.md files (macro/, technical/, leader/) hold patterns, NOT logs.
    Agents append patterns selectively; these stay human-audited and bounded.
  - SummarizationMiddleware (auto-included by deepagents) compacts conversation
    history when context fills up — system prompt overhead must stay minimal.
"""
from __future__ import annotations

import logging
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, LocalShellBackend
from deepagents.middleware.filesystem import FilesystemPermission

logger = logging.getLogger("trading_team.memory")

# ---------------------------------------------------------------------------
# Memory directory layout
# ---------------------------------------------------------------------------

MEMORY_ROOT: Path = Path(__file__).parent.parent / "memory"
SKILLS_ROOT: Path = MEMORY_ROOT / "skills"

# ---------------------------------------------------------------------------
# Starter skill templates
# ---------------------------------------------------------------------------

_SKILL_HOW_TO_CREATE_MD = """\
---
name: how-to-create-skill
description: Guide for creating new skills to capture reusable workflows. Read this when you want to save a multi-step procedure discovered during this session.
---

# How to Create a New Skill

## When to create a skill?
A skill is a multi-step procedure that CAN BE REUSED across many future situations.

✅ Worth creating:
- "5-step steel stock analysis workflow when global steel prices fluctuate"
- "Pre-buy checklist for bank stocks"
- "How to calculate position size when SL > 7% on HOSE"

❌ DO NOT create (use memory/tickers/ or sessions/ instead):
- Single ticker info (HPG is at 28,500)
- Lesson from one specific session
- One-time fact (CPI April = 3.2%)

## Naming conventions
- Lowercase, hyphens only, 1–64 chars, must match folder name
- ✅ `vn-steel-sector-scan`, `position-sizing-vn`
- ❌ `Steel Analysis`, `position_sizing`

## Choose category
- `/memory/skills/shared/`   — all agents can use
- `/memory/skills/analysis/` — MacroAnalyst + TechnicalAnalyst only
- `/memory/skills/strategy/` — Bull/Bear/Leader only

## Create the file
```
write_file /memory/skills/<category>/<skill-name>/SKILL.md
```

Required content:
```
---
name: <skill-name>
description: <1–2 sentences — this is ALL the agent sees before deciding to load this skill>
---

# <Skill Title>

## When to use
<Specific condition / trigger>

## Steps
1. ...
2. ...

## Notes / Pitfalls
...
```

## After creating
The skill appears automatically in the next session's context.
No registration or notification needed.
"""

_SKILL_VN_FUNDAMENTAL_VALUATION_MD = """\
---
name: vn-fundamental-valuation
description: Value VN stocks using P/E, P/B, EV/EBITDA, simple DCF. Use when Bull/Bear debate needs upside/downside targets based on fundamental valuation.
---

# VN Fundamental Valuation

## When to use
- Determine if a stock is cheap/expensive vs history and sector
- Calculate price target for Bull/Bear debate
- Evaluate margin of safety before recommending a buy

## Data to collect
1. EPS trailing 12 months (TTM) + forward EPS FY+1
2. Book value per share (BVPS)
3. EBITDA + Net Debt
4. Current price + shares outstanding

## Formulas

### P/E Analysis
- Current P/E = Price / EPS TTM
- Benchmark VN: VNIndex P/E ~12–16x (depending on cycle)
- Price target = Target P/E × Forward EPS
- Upside/Downside = (Target - Current Price) / Current Price

### P/B Analysis
- P/B = Price / BVPS
- VN Banks: reasonable 1.2–2.5x
- Steel/Manufacturing: reasonable 0.8–1.5x
- Real Estate: reasonable 1.0–2.0x

### EV/EBITDA
- EV = Market cap + Net debt - Cash
- <6x: cheap | 6–10x: reasonable | >10x: expensive (VN context)

### Simple DCF (3-year)
- WACC = 13–15% (VN risk premium)
- Terminal growth g = 3–5%
- Terminal value = FCF₃ × (1+g) / (WACC − g)
- Intrinsic value = PV(FCF₁ + FCF₂ + FCF₃) + PV(TV)

## Sample Output
• P/E TTM: 12x | 5Y avg: 10x | Sector: 11x → Slight premium ~9%
• P/B: 1.8x | Peer avg: 1.5x → More expensive than peers
• Target based on P/E 11x × Forward EPS 3,500₫ = 38,500₫ (+12% upside)
• Valuation conclusion: [Cheap / Reasonable / Expensive]
"""

_SKILL_POSITION_SIZING_VN_MD = """\
---
name: position-sizing-vn
description: "Calculate optimal position size for VN market: risk per trade, simple Kelly, NAV limit checks. Use before any buy recommendation."
---

# Position Sizing for VN Market

## When to use
- Before a BUY recommendation: calculate exact shares and % NAV
- Check if a recommendation violates allocation rules in the trading plan

## Pre-check (from trading plan — already in context)
- Max single position: 25% NAV
- Max sector concentration: 40% NAV
- Minimum cash: 10% NAV
- Drawdown rule: NAV −15% → cut 50% of everything, halt new buys

## Calculation Process

### Step 1: Define risk per trade
- Default: 1–1.5% NAV
- Clear setup (confirmed breakout + favourable macro): 2% NAV
- Unclear/unconfirmed setup: 0.5–1% NAV

### Step 2: Calculate position size from SL
```
SL distance % = (Entry − SL) / Entry
Position size (₫) = Risk / SL distance %
Position size (% NAV) = Position size / NAV
```
Example:
- NAV = 1 billion, Risk = 1.5% = 15M
- Entry = 28,500 | SL = 26,600 → SL distance = 6.67%
- Position = 15M / 6.67% = 225M = 22.5% NAV ✅

### Step 3: Check sector concentration
- Current same-sector positions + new position ≤ 40% NAV

### Step 4: Check cash buffer
- Cash remaining after buy = NAV − total portfolio − new position ≥ 10% NAV

## VN-Specific Notes
- T+2.5: do not sell immediately after buying → account in liquidity buffer
- No auto SL: must monitor manually — never forget
- ±7% band on HOSE: do not set SL too close to entry (easily hit in one session)

## Sample Output
• NAV: 1,000,000,000₫
• Entry: 28,500 | SL: 26,600 | SL distance: 6.7%
• Risk 1.5% NAV = 15,000,000₫ → 7,500 shares ≈ 214M ≈ 21.4% NAV ✅
• Cash after buy: check portfolio → X% ≥ 10%? [confirm]
• Recommendation: Buy 7,500 shares (~21% NAV)
"""


_GLOBAL_AGENTS_MD = """\
# Trading Team — Global Reference

This file is NOT auto-injected. Agents read it on demand: `read_file /memory/AGENTS.md`

## Memory File Map
- `/memory/portfolio/AGENTS.md`   — current positions (auto-injected, always fresh)
- `/memory/trading_plan/AGENTS.md` — strategy doc (auto-injected, always fresh)
- `/memory/macro/AGENTS.md`       — macro pattern library (auto-injected for MacroAnalyst)
- `/memory/technical/AGENTS.md`   — VN chart pattern library (auto-injected for TechnicalAnalyst)
- `/memory/leader/AGENTS.md`      — user prefs + session tips (auto-injected for Leader)
- `/memory/tickers/<TICKER>.md`   — per-ticker accumulated knowledge
- `/memory/sessions/<DATE>_<slug>.md` — past session reviews

## Accumulated Session Lessons
*(Browse: `ls /memory/sessions/` then `read_file /memory/sessions/<file>`)*
"""

_PORTFOLIO_AGENTS_MD = """\
# Current Portfolio

No positions recorded yet.
Update this file when trades are executed.

## Format
- <TICKER>: <SHARES> shares @ avg <PRICE> | <PCT>% NAV | SL: <SL_PRICE>
"""

_MACRO_AGENTS_MD = """\
# MacroAnalyst — Domain Knowledge

## Reliable Tool Combinations
- SBV interest rate: web_search "lãi suất SBV tháng MM/YYYY"
- FII flows: web_search "khối ngoại mua bán ròng YYYY" + listing tools
- CPI/GDP: web_search "CPI Vietnam YYYY" (GSOVN or SBV releases)

## VN Macro Patterns (accumulated)
*(Append new patterns below as they are observed)*

## Tool Reliability Notes
*(Append tool success/failure notes here)*
"""

_TECHNICAL_AGENTS_MD = """\
# TechnicalAnalyst — Domain Knowledge

## VN Market Rules (always apply)
- Trailing SL: based on CLOSE price only — no intraday stops (±2-3% ATO/ATC noise)
- No auto stop-loss on HOSE/HNX — must use conditional/manual orders
- Price limits: HOSE ±7%, HNX ±10%, UPCOM ±15%
- Settlement: T+2.5 — factor into liquidity planning

## Reliable Patterns in VN Market
- Confirmed breakout: Volume > 1.5× 20d avg + NN net buying
- False breakout signal: Volume below avg + NN selling despite price rise
*(Append new observed patterns below)*

## Per-Ticker Technical Notes
*(Use /memory/tickers/<TICKER>.md for per-asset chart patterns)*
"""

_TRADING_PLAN_AGENTS_MD = """\
# Trading Plan — Living Strategy Document

## Market Outlook
*(Updated by Leader after each session where market view changes)*
- **Overall stance**: NEUTRAL — awaiting clearer direction
- **Key macro drivers**: Interest rates, FII flows, USD/VND exchange rate
- **Time horizon focus**: Medium-term (1–3 months)

## Investment Themes
*(Sectors / megatrends currently favored)*
*(Append or update as thesis evolves)*

## Watchlist
*(Tickers being tracked — NOT yet in portfolio)*
| Ticker | Thesis | Entry condition | Target | Max size |
|--------|--------|-----------------|--------|----------|
| (empty) | | | | |

## Entry Rules
- Only enter when BOTH technical + fundamental align
- Volume confirmation required (>1.5× 20d avg on breakout day)
- Never chase more than 2% above planned entry
- Maximum 3 new positions open simultaneously

## Exit Rules
- Profit target: +15–20% from entry (sector/momentum dependent)
- Hard stop-loss: -7% from entry (HOSE limit — discipline required)
- Thesis broken: Exit regardless of price (document reason)
- Time stop: Re-evaluate any position held > 60 days without target hit

## Capital Allocation
- Max single position: 25% NAV
- Max sector concentration: 40% NAV
- Minimum cash reserve: 10% NAV (liquidity buffer)
- Drawdown rule: If NAV drops >15% → reduce all positions 50%, pause new entries

## Rules NOT to Break
*(User-specific hard rules — append here)*
- Never average down into a losing position more than once
- Never hold through earnings if unrealised gain < 5%

## Recent Strategy Changes
*(Append dated notes when plan changes — trace the evolution)*
"""

_LEADER_AGENTS_MD = """\
# Leader — Session Management Knowledge

## User Preferences
*(Append user-specific preferences and communication style notes here)*

## Session Management Tips
- Ambiguous requests: ask max 2 clarifying questions, not more
- Long analysis sessions: summarise macro + technical in 3-5 bullets before handoff
- Debate deadlock: end after 3 rounds if no new arguments

## Past Decision Patterns
*(Append recurring decision frameworks and lessons here)*
"""


def ensure_memory_structure() -> None:
    """Create memory directory tree, default AGENTS.md files, and starter skills if absent."""
    dirs = [
        MEMORY_ROOT,
        MEMORY_ROOT / "portfolio",
        MEMORY_ROOT / "trading_plan",
        MEMORY_ROOT / "tickers",
        MEMORY_ROOT / "sessions",
        MEMORY_ROOT / "macro",
        MEMORY_ROOT / "technical",
        MEMORY_ROOT / "leader",
        # Skills directories (SkillsMiddleware scans these)
        SKILLS_ROOT / "shared" / "how-to-create-skill",
        SKILLS_ROOT / "analysis" / "vn-fundamental-valuation",
        SKILLS_ROOT / "strategy" / "position-sizing-vn",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    defaults = {
        MEMORY_ROOT / "AGENTS.md": _GLOBAL_AGENTS_MD,
        MEMORY_ROOT / "portfolio" / "AGENTS.md": _PORTFOLIO_AGENTS_MD,
        MEMORY_ROOT / "trading_plan" / "AGENTS.md": _TRADING_PLAN_AGENTS_MD,
        MEMORY_ROOT / "macro" / "AGENTS.md": _MACRO_AGENTS_MD,
        MEMORY_ROOT / "technical" / "AGENTS.md": _TECHNICAL_AGENTS_MD,
        MEMORY_ROOT / "leader" / "AGENTS.md": _LEADER_AGENTS_MD,
        # Starter skills (created once, agents and humans can add more at runtime)
        SKILLS_ROOT / "shared" / "how-to-create-skill" / "SKILL.md": _SKILL_HOW_TO_CREATE_MD,
        SKILLS_ROOT / "analysis" / "vn-fundamental-valuation" / "SKILL.md": _SKILL_VN_FUNDAMENTAL_VALUATION_MD,
        SKILLS_ROOT / "strategy" / "position-sizing-vn" / "SKILL.md": _SKILL_POSITION_SIZING_VN_MD,
    }
    for path, content in defaults.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            logger.info("Created %s", path.relative_to(MEMORY_ROOT.parent))


# ---------------------------------------------------------------------------
# Shared backend instance (all agents reuse one CompositeBackend instance)
# ---------------------------------------------------------------------------

def _make_backend(memory_root: str) -> CompositeBackend:
    """Return a CompositeBackend instance routing /memory/ to local files."""
    return CompositeBackend(
        default=StateBackend(),
        routes={
            "/memory/": LocalShellBackend(
                root_dir=memory_root,
                virtual_mode=True,
            ),
        },
    )


# ---------------------------------------------------------------------------
# Common internal factory
# ---------------------------------------------------------------------------

def _create_memory_agent(
    llm,
    tools: list,
    system_prompt: str,
    name: str,
    memory_sources: list[str],
    skill_sources: list[str] | None = None,
):
    """
    Wrap any trading team agent with the 4-tier memory harness.

    All agents get:
      - MemoryMiddleware: auto-inject bounded AGENTS.md files (portfolio, trading_plan, domain)
      - SkillsMiddleware: progressive-disclosure workflows (name+desc only in prompt; load on demand)
      - FilesystemMiddleware: read + write /memory/ (tickers, sessions, skills creation)
      - No execute() sandbox — shell is blocked by design for financial agents
    """
    return create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        memory=memory_sources,
        skills=skill_sources,
        permissions=[
            FilesystemPermission(
                operations=["read", "write"],
                paths=["/memory/"],
            ),
            FilesystemPermission(
                operations=["read"],
                paths=["/logs/"],
            )
        ],
        backend=_make_backend(str(MEMORY_ROOT)),
        name=name,
    )


# ---------------------------------------------------------------------------
# Public factories
# ---------------------------------------------------------------------------

def create_lead_analysis_agent(llm, tools: list, system_prompt: str):
    """
    Create a deep agent for the LeadAnalysis coordinator role.

    Orchestrates MacroAnalyst and TechnicalAnalyst (called concurrently in graph.py).
    Synthesizes their outputs into a unified analysis brief for the strategy room.

    Memory: portfolio + trading_plan (same as strategy agents — knows the current plan).
    Skills: shared/ + analysis/ (same pool as the analysts it coordinates).
    """
    return _create_memory_agent(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        name="LeadAnalysis",
        memory_sources=[
            "/memory/portfolio/AGENTS.md",
            "/memory/trading_plan/AGENTS.md",
        ],
        skill_sources=[
            "/memory/skills/shared/",
            "/memory/skills/analysis/",
        ],
    )


def create_analysis_agent(llm, tools: list, system_prompt: str, name: str, domain: str):
    """
    Create a deep agent for the analysis room (MacroAnalyst / TechnicalAnalyst).

    Memory: portfolio + trading_plan + domain AGENTS.md (always bounded).
    Skills: shared/ + analysis/ (progressive disclosure — name+desc only until needed).
    Can read/write ticker notes, domain patterns, and create new skills.
    """
    return _create_memory_agent(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        name=name,
        memory_sources=[
            "/memory/portfolio/AGENTS.md",
            "/memory/trading_plan/AGENTS.md",
            f"/memory/{domain}/AGENTS.md",
        ],
        skill_sources=[
            "/memory/skills/shared/",
            "/memory/skills/analysis/",
        ],
    )


def create_strategy_agent(llm, tools: list, system_prompt: str, name: str):
    """
    Create a deep agent for the strategy room (BullAnalyst / BearAnalyst).

    Memory: portfolio + trading_plan (always bounded).
    Skills: shared/ + strategy/ (progressive disclosure).
    Can read/write ticker notes and create new skills.
    MCP memory_search included in tools for read-only external knowledge.
    """
    return _create_memory_agent(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        name=name,
        memory_sources=[
            "/memory/portfolio/AGENTS.md",
            "/memory/trading_plan/AGENTS.md",
        ],
        skill_sources=[
            "/memory/skills/shared/",
            "/memory/skills/strategy/",
        ],
    )


def create_leader_agent(llm, tools: list, system_prompt: str):
    """
    Create a deep agent for the Leader role.

    Memory: portfolio + trading_plan + leader AGENTS.md (always bounded).
    Skills: shared/ + analysis/ + strategy/ — sees ALL skills, orchestrates the full team.
    Primary writer of session summaries, portfolio, trading plan, and skill extraction.
    """
    return _create_memory_agent(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        name="Leader",
        memory_sources=[
            "/memory/portfolio/AGENTS.md",
            "/memory/trading_plan/AGENTS.md",
            "/memory/leader/AGENTS.md",
        ],
        skill_sources=[
            "/memory/skills/shared/",
            "/memory/skills/analysis/",
            "/memory/skills/strategy/",
        ],
    )

