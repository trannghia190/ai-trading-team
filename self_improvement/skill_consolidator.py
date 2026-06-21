"""
Skill Consolidator — merge duplicates, drop outdated skills.

Steps:
  1. Load all SKILL.md files with full content
  2. Send to LLM with a consolidation prompt
  3. LLM returns a JSON plan: KEEP / DELETE / MERGE actions
  4. Execute plan (write merged files, delete obsolete dirs)
  5. Return a human-readable summary

Called via Telegram /si_compress_skills command.
"""
from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from . import config as cfg

logger = logging.getLogger("trading_team.si.consolidator")

SKILLS_ROOT = cfg.MEMORY_DIR.parent / "skills"   # memory/skills/
CATEGORIES  = ("shared", "analysis", "strategy")


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class ConsolidationResult:
    kept:    list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    merged:  list[str] = field(default_factory=list)
    errors:  list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = []
        if self.merged:
            lines.append(f"🔀 *Merged* ({len(self.merged)}):\n" + "\n".join(f"  • {m}" for m in self.merged))
        if self.deleted:
            lines.append(f"🗑 *Deleted* ({len(self.deleted)}):\n" + "\n".join(f"  • {d}" for d in self.deleted))
        if self.kept:
            lines.append(f"✅ *Kept unchanged* ({len(self.kept)}):\n" + "\n".join(f"  • {k}" for k in self.kept))
        if self.errors:
            lines.append(f"⚠️ *Errors*:\n" + "\n".join(f"  • {e}" for e in self.errors))
        return "\n\n".join(lines) if lines else "Nothing to consolidate."


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

@dataclass
class _SkillEntry:
    category: str
    name:     str
    path:     Path
    content:  str


def _load_all_skills() -> list[_SkillEntry]:
    entries = []
    for cat in CATEGORIES:
        cat_dir = SKILLS_ROOT / cat
        if not cat_dir.exists():
            continue
        for skill_dir in sorted(cat_dir.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                entries.append(_SkillEntry(
                    category=cat,
                    name=skill_dir.name,
                    path=skill_file,
                    content=skill_file.read_text(encoding="utf-8"),
                ))
    return entries


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=cfg.CODING_MODEL,
        api_key=cfg.CODING_API_KEY,
        base_url=cfg.CODING_BASE_URL,
        temperature=0,
    )


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

async def consolidate() -> ConsolidationResult:
    result = ConsolidationResult()
    skills = _load_all_skills()

    if not skills:
        result.kept.append("(no skills found)")
        return result

    # Build skills block for the prompt
    skills_block = ""
    for i, s in enumerate(skills):
        skills_block += (
            f"\n### SKILL {i} — [{s.category}] {s.name}\n"
            f"{s.content}\n"
        )

    prompt = (
        "You are a knowledge curator for a Vietnamese stock trading AI team.\n\n"
        "Below are ALL skills currently in the skill library. Analyse them and produce a\n"
        "consolidation plan. Be CONSERVATIVE — only consolidate when there is clear overlap.\n\n"
        "Rules:\n"
        "  KEEP   — skill is unique and still relevant\n"
        "  DELETE — skill is: truly outdated, superseded by a better one, or meta/instructions\n"
        "           (e.g. 'how-to-create-skill' is a meta-skill, can be deleted)\n"
        "  MERGE  — two or more skills overlap significantly; combine into ONE better skill\n"
        "           The merged skill gets a NEW English name (lowercase-hyphens), keeps the best\n"
        "           category. new_content must be the FULL merged SKILL.md file content.\n\n"
        "Respond with a JSON array only (no markdown fences, no extra text):\n"
        "[\n"
        "  {\"action\": \"KEEP\",   \"category\": \"...\", \"name\": \"...\"},\n"
        "  {\"action\": \"DELETE\", \"category\": \"...\", \"name\": \"...\", \"reason\": \"...\"},\n"
        "  {\n"
        "    \"action\": \"MERGE\",\n"
        "    \"into_category\": \"...\",\n"
        "    \"into_name\": \"<new-english-name>\",\n"
        "    \"sources\": [{\"category\": \"...\", \"name\": \"...\"}, ...],\n"
        "    \"reason\": \"...\",\n"
        "    \"new_content\": \"<full SKILL.md text starting with ---\\nname: ...>\"\n"
        "  },\n"
        "  ...\n"
        "]\n\n"
        "Every existing skill name MUST appear exactly once across all actions "
        "(either in KEEP, DELETE, or as a source of MERGE).\n\n"
        f"{skills_block}"
    )

    try:
        response = await _llm().ainvoke([HumanMessage(content=prompt)])
        raw = (response.content or "").strip()
        # Strip accidental markdown fences
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        plan: list[dict] = json.loads(raw)
    except Exception as exc:
        result.errors.append(f"LLM/parse error: {exc}")
        logger.error("consolidate: failed to get plan: %s", exc)
        return result

    # Index existing skills for lookup
    existing_map: dict[tuple[str, str], _SkillEntry] = {
        (s.category, s.name): s for s in skills
    }

    # Track which skill dirs to delete after processing MERGE sources
    to_delete: set[tuple[str, str]] = set()

    for action in plan:
        act = action.get("action", "").upper()
        try:
            if act == "KEEP":
                result.kept.append(f"[{action['category']}] {action['name']}")

            elif act == "DELETE":
                key = (action["category"], action["name"])
                entry = existing_map.get(key)
                if entry:
                    shutil.rmtree(entry.path.parent, ignore_errors=True)
                    result.deleted.append(
                        f"[{action['category']}] {action['name']} — {action.get('reason', '')}"
                    )
                    logger.info("Deleted skill: %s/%s", action["category"], action["name"])
                else:
                    result.errors.append(f"DELETE: not found [{action['category']}] {action['name']}")

            elif act == "MERGE":
                into_cat  = action["into_category"]
                into_name = action["into_name"]
                sources   = action.get("sources", [])
                new_content = action.get("new_content", "")

                if not new_content:
                    result.errors.append(f"MERGE into {into_name}: missing new_content")
                    continue

                # Write merged skill
                dest_dir = SKILLS_ROOT / into_cat / into_name
                dest_dir.mkdir(parents=True, exist_ok=True)
                (dest_dir / "SKILL.md").write_text(new_content.strip(), encoding="utf-8")
                logger.info("Merged skill written: %s/%s", into_cat, into_name)

                # Delete source dirs (but not if into_name == source name, i.e. in-place update)
                source_descs = []
                for src in sources:
                    src_key = (src["category"], src["name"])
                    src_entry = existing_map.get(src_key)
                    if src_entry and not (src["category"] == into_cat and src["name"] == into_name):
                        shutil.rmtree(src_entry.path.parent, ignore_errors=True)
                        logger.info("Removed merge source: %s/%s", src["category"], src["name"])
                    source_descs.append(f"[{src['category']}] {src['name']}")

                result.merged.append(
                    f"[{into_cat}] {into_name} ← {', '.join(source_descs)}"
                    + (f" — {action.get('reason', '')}" if action.get("reason") else "")
                )

            else:
                result.errors.append(f"Unknown action: {act}")

        except Exception as exc:
            result.errors.append(f"{act} {action.get('name', '?')}: {exc}")
            logger.error("consolidate action %s failed: %s", act, exc)

    return result
