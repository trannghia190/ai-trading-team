---
name: how-to-create-skill
description: Guide for creating a new skill to capture a reusable workflow. Read this when you want to preserve a multi-step process discovered in the current session.
---

# Guide to Creating a New Skill

## When should you create a skill?
A skill is a multi-step process that CAN BE REUSED across future situations.

✅ Good candidates for a skill:
- "A 5-step workflow for analyzing steel stocks when global steel prices move"
- "A pre-trade checklist before recommending a bank stock buy"
- "How to calculate position size when stop loss is wider than 7% on HOSE"

❌ Do NOT create a skill for these cases. Use `memory/tickers/` or `sessions/` instead:
- Information about one specific ticker, for example `HPG is at 28,500`
- A lesson from one specific session
- A one-off fact, for example `April CPI = 3.2%`

## Naming convention
- Lowercase, hyphens only, 1-64 characters, matching the directory name
- ✅ `vn-steel-sector-scan`, `position-sizing-vn`
- ❌ `Steel Analysis`, `position_sizing`

## Choose a category
- `/memory/skills/shared/`   — usable by every agent
- `/memory/skills/analysis/` — only for MacroAnalyst and TechnicalAnalyst
- `/memory/skills/strategy/` — only for Bull/Bear/Leader

## Create the file
```
write_file /memory/skills/<category>/<skill-name>/SKILL.md
```

Required contents:
```
---
name: <skill-name>
description: <1-2 sentences - this is ALL the agent sees before deciding whether to open the skill>
---

# <Skill Name>

## When to use this skill
<Specific condition or trigger>

## Steps
1. ...
2. ...

## Notes / Pitfalls
...
```

## After creation
The skill appears automatically in the next session context.
No extra registration or announcement is needed.
